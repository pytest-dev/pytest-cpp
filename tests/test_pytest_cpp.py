import subprocess
import sys
import tempfile
from shutil import which

import pytest

from pytest_cpp import error
from pytest_cpp.boost import BoostTestFacade
from pytest_cpp.catch2 import Catch2Facade
from pytest_cpp.error import CppFailureRepr
from pytest_cpp.error import CppTestFailure
from pytest_cpp.google import GoogleTestFacade
from pytest_cpp.helpers import make_cmdline


def assert_outcomes(result, expected_outcomes):
    __tracebackhide__ = True
    obtained = []
    for test_id, _ in expected_outcomes:
        rep = result.matchreport(test_id, "pytest_runtest_logreport")
        obtained.append((test_id, rep.outcome))
    assert expected_outcomes == obtained


@pytest.fixture
def dummy_failure():
    class DummyTestFailure(CppTestFailure):
        def __init__(self):
            self.lines = []
            self.file_reference = "unknown", 0

        def get_lines(self):
            return self.lines

        def get_file_reference(self):
            return self.file_reference

    return DummyTestFailure()


@pytest.mark.parametrize(
    "facade, name, expected",
    [
        (
            GoogleTestFacade(),
            "gtest",
            [
                "FooTest.test_success",
                "FooTest.test_failure",
                "FooTest.test_error",
                "FooTest.DISABLED_test_disabled",
                "FooTest.test_skipped",
                "FooTest.test_skipped_no_msg",
            ],
        ),
        (BoostTestFacade(), "boost_success", ["boost_success"]),
        (BoostTestFacade(), "boost_error", ["boost_error"]),
        (BoostTestFacade(), "boost_fixture_setup_error", ["boost_fixture_setup_error"]),
        (
            Catch2Facade(),
            "catch2_success",
            ["Factorials are computed", "Passed Sections"],
        ),
        (
            Catch2Facade(),
            "catch2_success_v3",
            ["Factorials are computed", "Passed Sections"],
        ),
    ],
)
def test_list_tests(facade, name, expected, exes):
    obtained = facade.list_tests(exes.get(name))
    assert obtained == expected


@pytest.mark.parametrize(
    "facade, name, other_name",
    [
        (GoogleTestFacade(), "gtest", "boost_success"),
        (BoostTestFacade(), "boost_success", "gtest"),
        (Catch2Facade(), "catch2_success", "gtest"),
    ],
)
def test_is_test_suite(facade, name, other_name, exes, tmp_path):
    assert facade.is_test_suite(exes.get(name))
    assert not facade.is_test_suite(exes.get(other_name))
    tmp_path.joinpath("foo.txt").touch()
    assert not facade.is_test_suite(str(tmp_path.joinpath("foo.txt")))


@pytest.mark.parametrize(
    "facade, name, test_id",
    [
        (GoogleTestFacade(), "gtest", "FooTest.test_success"),
        (BoostTestFacade(), "boost_success", "<unused>"),
        (Catch2Facade(), "catch2_success", "Factorials are computed"),
    ],
)
def test_success(facade, name, test_id, exes):
    assert facade.run_test(exes.get(name), test_id)[0] is None


def test_cmdline_builder_happy_flow():
    arg_string = make_cmdline(["wine"], "gtest", ["--help"])
    assert arg_string == ["wine", "gtest", "--help"]


def test_cmdline_builder_with_empty_harness():
    arg_string = make_cmdline(
        list(), "boost_test", ["--output_format=XML", "--log_sink=dummy.log"]
    )
    assert arg_string == ["boost_test", "--output_format=XML", "--log_sink=dummy.log"]


def test_cmdline_builder_with_empty_args():
    arg_string = make_cmdline(["wine"], "gtest")
    assert arg_string == ["wine", "gtest"]


def test_google_failure(exes):
    facade = GoogleTestFacade()
    failures, _ = facade.run_test(exes.get("gtest"), "FooTest.test_failure")
    assert len(failures) == 2
    colors = ("red", "bold")
    assert failures[0].get_lines() == [
        ("Expected equality of these values:", colors),
        ("  2 * 3", colors),
        ("    Which is: 6", colors),
        ("  5", colors),
    ]
    assert failures[0].get_file_reference() == ("gtest.cpp", 19)

    assert failures[1].get_lines() == [
        ("Expected equality of these values:", colors),
        ("  2 * 6", colors),
        ("    Which is: 12", colors),
        ("  15", colors),
    ]
    assert failures[1].get_file_reference() == ("gtest.cpp", 20)


def test_google_error(exes):
    facade = GoogleTestFacade()
    failures, _ = facade.run_test(exes.get("gtest"), "FooTest.test_error")
    assert len(failures) == 1
    colors = ("red", "bold")
    assert failures[0].get_lines() == [
        ("unknown file", colors),
        (
            'C++ exception with description "unexpected exception"'
            " thrown in the test body.",
            colors,
        ),
    ]


def test_google_disabled(exes):
    facade = GoogleTestFacade()
    try:
        facade.run_test(exes.get("gtest"), "FooTest.DISABLED_test_disabled")
    except pytest.skip.Exception as disabled_message:
        assert "Disabled" in str(disabled_message)


def test_google_skipped(exes):
    facade = GoogleTestFacade()
    try:
        facade.run_test(exes.get("gtest"), "FooTest.test_skipped")
        assert False, "No skipped exception found"
    except pytest.skip.Exception as skipped_message:
        assert "This is a skipped message" in str(skipped_message)


def test_google_skipped_no_msg(exes):
    facade = GoogleTestFacade()
    with pytest.raises(pytest.skip.Exception):
        facade.run_test(exes.get("gtest"), "FooTest.test_skipped_no_msg")
        assert False, "No skipped exception found"


def test_boost_failure(exes):
    facade = BoostTestFacade()
    failures, _ = facade.run_test(exes.get("boost_failure"), "<unused>")
    assert len(failures) == 2

    fail1, fail2 = failures
    colors = ("red", "bold")
    assert fail1.get_lines() == [("check 2 * 3 == 5 has failed", colors)]
    assert fail1.get_file_reference() == ("boost_failure.cpp", 9)

    assert fail2.get_lines() == [("check 2 - 1 == 0 has failed", colors)]
    assert fail2.get_file_reference() == ("boost_failure.cpp", 15)


def test_boost_fatal_error(exes):
    facade = BoostTestFacade()
    failures, _ = facade.run_test(exes.get("boost_fatal_error"), "<unused>")
    assert len(failures) == 1

    (fail1,) = failures
    colors = ("red", "bold")
    assert fail1.get_lines() == [("critical check 2 * 3 == 5 has failed", colors)]
    assert fail1.get_file_reference() == ("boost_fatal_error.cpp", 8)


def test_boost_error(exes):
    facade = BoostTestFacade()
    failures, _ = facade.run_test(exes.get("boost_error"), "<unused>")
    assert len(failures) == 2

    fail1, fail2 = failures
    colors = ("red", "bold")
    assert fail1.get_lines() == [("std::runtime_error: unexpected exception", colors)]
    assert fail1.get_file_reference() == ("unknown location", 0)

    assert fail2.get_lines() == [
        ("std::runtime_error: another unexpected exception", colors)
    ]
    assert fail2.get_file_reference() == ("unknown location", 0)


def test_boost_fixture_setup_error(exes):
    facade = BoostTestFacade()
    failures, _ = facade.run_test(exes.get("boost_fixture_setup_error"), "<unused>")
    assert len(failures) == 1

    fail1 = failures[0]
    colors = ("red", "bold")
    ((line, obtained_colors),) = fail1.get_lines()
    assert line == "std::runtime_error: This is a global fixture init failure"
    assert obtained_colors == colors
    assert fail1.get_file_reference() == ("unknown location", 0)


def test_google_run(testdir, exes):
    result = testdir.inline_run("-v", exes.get("gtest", "test_gtest"))
    assert_outcomes(
        result,
        [
            ("FooTest.test_success", "passed"),
            ("FooTest.test_failure", "failed"),
            ("FooTest.test_error", "failed"),
            ("FooTest.DISABLED_test_disabled", "skipped"),
            ("FooTest.test_skipped", "skipped"),
            ("FooTest.test_skipped_no_msg", "skipped"),
        ],
    )


def test_unknown_error(testdir, exes, mocker):
    mocker.patch.object(
        GoogleTestFacade, "run_test", side_effect=RuntimeError("unknown error")
    )
    result = testdir.inline_run("-v", exes.get("gtest", "test_gtest"))
    rep = result.matchreport("FooTest.test_success", "pytest_runtest_logreport")
    assert "unknown error" in str(rep.longrepr)


def test_google_internal_errors(mocker, testdir, exes, tmp_path):
    mocker.patch.object(GoogleTestFacade, "is_test_suite", return_value=True)
    mocker.patch.object(
        GoogleTestFacade, "list_tests", return_value=["FooTest.test_success"]
    )
    mocked = mocker.patch.object(
        subprocess, "check_output", autospec=True, return_value=""
    )

    def raise_error(*args, **kwargs):
        raise subprocess.CalledProcessError(returncode=100, cmd="")

    mocked.side_effect = raise_error
    result = testdir.inline_run("-v", exes.get("gtest", "test_gtest"))
    rep = result.matchreport(exes.exe_name("test_gtest"), "pytest_runtest_logreport")
    assert "Internal Error: calling" in str(rep.longrepr)

    mocked.side_effect = None
    xml_file = tmp_path.joinpath("cpp-report.xml")
    xml_file.write_text("<empty/>")
    temp_mock = mocker.patch.object(tempfile, "TemporaryDirectory")
    temp_mock().__enter__.return_value = str(tmp_path)

    result = testdir.inline_run("-v", exes.get("gtest", "test_gtest"))
    rep = result.matchreport(exes.exe_name("test_gtest"), "pytest_runtest_logreport")

    assert "Internal Error: could not find test" in str(rep.longrepr)


def test_boost_run(testdir, exes):
    all_names = [
        "boost_success",
        "boost_error",
        "boost_fixture_setup_error",
        "boost_failure",
    ]
    all_files = [exes.get(n, "test_" + n) for n in all_names]
    result = testdir.inline_run("-v", *all_files)
    assert_outcomes(
        result,
        [
            ("test_boost_success", "passed"),
            ("test_boost_error", "failed"),
            ("test_boost_fixture_setup_error", "failed"),
            ("test_boost_failure", "failed"),
        ],
    )


def mock_popen(mocker, return_code, stdout, stderr):
    mocked_popen = mocker.MagicMock()
    mocked_popen.__enter__ = mocked_popen
    mocked_popen.communicate.return_value = stdout, stderr
    mocked_popen.return_code = return_code
    mocked_popen.poll.return_value = return_code
    mocker.patch.object(subprocess, "Popen", return_value=mocked_popen)
    return mocked_popen


def test_boost_internal_error(testdir, exes, mocker):
    exe = exes.get("boost_success", "test_boost_success")
    mock_popen(mocker, return_code=100, stderr=None, stdout=None)
    mocker.patch.object(BoostTestFacade, "is_test_suite", return_value=True)
    mocker.patch.object(GoogleTestFacade, "is_test_suite", return_value=False)
    result = testdir.inline_run(exe)
    rep = result.matchreport(
        exes.exe_name("test_boost_success"), "pytest_runtest_logreport"
    )
    assert "Internal Error:" in str(rep.longrepr)


def test_cpp_failure_repr(dummy_failure):
    dummy_failure.lines = [("error message", {"red"})]
    dummy_failure.file_reference = "test_suite", 20
    failure_repr = CppFailureRepr([dummy_failure])
    assert str(failure_repr) == "error message\ntest_suite:20: C++ failure"


def test_cpp_files_option(testdir, exes):
    exes.get("boost_success")
    exes.get("gtest")

    result = testdir.runpytest("--collect-only")
    result.stdout.fnmatch_lines("* no tests *")

    testdir.makeini(
        """
        [pytest]
        cpp_files = gtest* boost*
    """
    )
    result = testdir.runpytest("--collect-only")
    result.stdout.fnmatch_lines(
        [
            "*CppFile boost_success*",
            "*CppFile gtest*",
        ]
    )


# skip to avoid dealing with exes.get appending extension
@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="This is not a problem on Windows"
)
def test_cpp_ignore_py_files(testdir, exes):
    file_name = "cpptest_success.py"
    exes.get("gtest", "cpptest_success.py")
    testdir.makeini(
        """
        [pytest]
        cpp_files = cpptest_*
    """
    )

    result = testdir.runpytest("--collect-only")
    result.stdout.fnmatch_lines("* no tests *")

    result = testdir.runpytest("--collect-only", "-o", "cpp_ignore_py_files=False")
    result.stdout.fnmatch_lines("*CppFile cpptest_success.py*")

    # running directly skips out machinery as well.
    result = testdir.runpytest("--collect-only", file_name)
    result.stdout.fnmatch_lines("*1 error in*")

    result = testdir.runpytest(
        "--collect-only", "-o", "cpp_ignore_py_files=False", file_name
    )
    result.stdout.fnmatch_lines("*CppFile cpptest_success.py*")


def test_google_one_argument(testdir, exes):
    testdir.makeini(
        """
        [pytest]
        cpp_arguments = argument1
    """
    )

    result = testdir.inline_run(exes.get("gtest_args"), "-k", "ArgsTest.one_argument")
    assert_outcomes(result, [("ArgsTest.one_argument", "passed")])


def test_google_two_arguments(testdir, exes):
    testdir.makeini(
        """
        [pytest]
        cpp_arguments = argument1 argument2
    """
    )

    result = testdir.inline_run(exes.get("gtest_args"), "-k", "ArgsTest.two_arguments")
    assert_outcomes(result, [("ArgsTest.two_arguments", "passed")])


def test_google_one_argument_via_option(testdir, exes):
    result = testdir.inline_run(
        exes.get("gtest_args"),
        "-k",
        "ArgsTest.one_argument",
        "-o",
        "cpp_arguments=argument1",
    )
    assert_outcomes(result, [("ArgsTest.one_argument", "passed")])


def test_google_two_arguments_via_option(testdir, exes):
    result = testdir.inline_run(
        exes.get("gtest_args"),
        "-k",
        "ArgsTest.two_arguments",
        "-o",
        "cpp_arguments=argument1 argument2",
    )
    assert_outcomes(result, [("ArgsTest.two_arguments", "passed")])


def test_argument_option_priority(testdir, exes):
    testdir.makeini(
        """
        [pytest]
        cpp_arguments = argument2
    """
    )
    result = testdir.inline_run(
        exes.get("gtest_args"),
        "-k",
        "ArgsTest.one_argument",
        "-o",
        "cpp_arguments=argument1",
    )
    assert_outcomes(result, [("ArgsTest.one_argument", "passed")])


@pytest.mark.skipif(
    not which("valgrind") or not which("catchsegv"),
    reason="Environment does not have required tools",
)
def test_google_cpp_harness_via_option(testdir, exes):
    result = testdir.inline_run(
        exes.get("gtest"),
        "-k",
        "FooTest.test_success",
        "-o",
        "cpp_harness=catchsegv valgrind --tool=memcheck",
    )
    assert_outcomes(result, [("FooTest.test_success", "passed")])


def test_boost_one_argument(testdir, exes):
    testdir.makeini(
        """
        [pytest]
        cpp_arguments = argument1
    """
    )

    result = testdir.inline_run(exes.get("boost_one_argument"))
    assert_outcomes(result, [("boost_one_argument", "passed")])


def test_boost_two_arguments(testdir, exes):
    testdir.makeini(
        """
        [pytest]
        cpp_arguments = argument1 argument2
    """
    )

    result = testdir.inline_run(exes.get("boost_two_arguments"))
    assert_outcomes(result, [("boost_two_arguments", "passed")])


def test_boost_one_argument_via_option(testdir, exes):
    result = testdir.inline_run(
        exes.get("boost_one_argument"), "-o", "cpp_arguments=argument1"
    )
    assert_outcomes(result, [("boost_one_argument", "passed")])


def test_boost_two_arguments_via_option(testdir, exes):
    result = testdir.inline_run(
        exes.get("boost_two_arguments"), "-o", "cpp_arguments=argument1 argument2"
    )
    assert_outcomes(result, [("boost_two_arguments", "passed")])


@pytest.mark.skipif(
    not which("valgrind") or not which("catchsegv"),
    reason="Environment does not have required tools",
)
def test_boost_cpp_harness_via_option(testdir, exes):
    result = testdir.inline_run(
        exes.get("boost_success"),
        "-s",
        "-k",
        "boost_success",
        "-o",
        "cpp_harness=catchsegv valgrind --tool=memcheck",
    )
    assert_outcomes(result, [("boost_success", "passed")])


def test_passing_files_directly_in_command_line(testdir, exes):
    f = exes.get("boost_success")
    result = testdir.runpytest(f)
    result.stdout.fnmatch_lines(["*1 passed*"])


def test_race_condition_on_collect(tmp_path):
    """
    Check that collection correctly handles when a path no longer is valid.

    This might happen in some situations when xdist is collecting multiple files, and that
    causes temporary .pyc files to be generated; in those situations, pytest may obtain that
    filename and ask plugins if they can collect it, but by the time a plugin is called
    the file may be gone already:

    OSError: [Errno 2] No such file or directory:
        '/../test_duplicate_filenames.cpython-27-PYTEST.pyc.21746'
    """
    import pytest_cpp.plugin

    assert (
        pytest_cpp.plugin.pytest_collect_file(None, tmp_path / "invalid-file") is None
    )


def test_exe_mask_on_windows(tmp_path, monkeypatch):
    """
    Test for #45: C++ tests not collected due to '*_test' mask on Windows
    """
    import pytest_cpp.plugin

    monkeypatch.setattr(sys, "platform", "win32")

    fn = tmp_path.joinpath("generator_demo_test.exe")
    fn.touch()
    assert pytest_cpp.plugin.matches_any_mask(fn, ["test_*", "*_test"])

    fn = tmp_path.joinpath("test_generator_demo.exe")
    fn.touch()
    assert pytest_cpp.plugin.matches_any_mask(fn, ["test_*", "*_test"])

    fn = tmp_path.joinpath("my_generator_test_demo.exe")
    fn.touch()
    assert not pytest_cpp.plugin.matches_any_mask(fn, ["test_*", "*_test"])


def test_output_section(testdir, exes):
    exes.get("boost_failure")
    exes.get("gtest")

    testdir.makeini(
        """
        [pytest]
        cpp_files = gtest* boost*
    """
    )
    result = testdir.runpytest("-k", "failure")
    result.stdout.fnmatch_lines(
        [
            "*Captured c++ call*",
            "Just saying hi from boost",
            "Just saying hi from gtest",
        ]
    )


def test_cpp_verbose(testdir, exes):
    exes.get("boost_success")
    exes.get("gtest")

    testdir.makeini(
        """
        [pytest]
        cpp_files = gtest* boost*
    """
    )
    result = testdir.runpytest("-k", "success", "-s", "-o", "cpp_verbose=true")
    result.stdout.fnmatch_lines(
        ["*Just saying hi from boost", "*Just saying hi from gtest"]
    )


def assert_catch2_failure(line, expected_line, expected_colors):
    assert expected_line in line[0]
    assert line[1] == expected_colors


def test_catch2_failure(exes):
    for suffix in ["", "_v3"]:
        facade = Catch2Facade()
        failures, _ = facade.run_test(
            exes.get(f"catch2_failure{suffix}"), "Factorials are computed"
        )
        assert len(failures) == 1

        fail1 = failures[0]
        colors = ("red", "bold")
        assert_catch2_failure(fail1.get_lines()[0], "Expected: ", colors)
        assert_catch2_failure(fail1.get_lines()[1], "Factorial(1) == 0", colors)
        assert_catch2_failure(fail1.get_lines()[3], "Actual: ", colors)
        assert_catch2_failure(fail1.get_lines()[4], "1 == 0", colors)

        assert fail1.get_file_reference() == (f"catch2_failure.cpp", 9)

        failures, _ = facade.run_test(
            exes.get(f"catch2_failure{suffix}"), "Failed Sections"
        )
        assert len(failures) == 2

        # test exceptions
        failures, _ = facade.run_test(exes.get(f"catch2_error{suffix}"), "Error")
        [fail1] = failures
        assert_catch2_failure(fail1.get_lines()[0], "Error: ", colors)
        assert_catch2_failure(fail1.get_lines()[1], "a runtime error", colors)


@pytest.mark.parametrize("suffix", ["", "_v3"])
@pytest.mark.parametrize(
    "test_id",
    [
        "Brackets in [test] name",
        "**Star in test name**",
        "~Tilde in test name",
        "Comma, in, test, name",
        r"Backslash\ in\ test\ name",
        '"Quotes" in test name',
    ],
)
def test_catch2_special_chars(suffix, test_id, exes):
    facade = Catch2Facade()
    exe = exes.get("catch2_special_chars" + suffix)
    assert facade.run_test(exe, test_id)[0] is None


class TestError:
    def test_get_whitespace(self):
        assert error.get_left_whitespace("  foo") == "  "
        assert error.get_left_whitespace("\t\t foo") == "\t\t "

    def test_get_code_context_around_line(self, tmp_path):
        f = tmp_path.joinpath("foo.py")
        f.write_text("line1\nline2\nline3\nline4\nline5")

        assert error.get_code_context_around_line(str(f), 1) == ["line1"]
        assert error.get_code_context_around_line(str(f), 2) == ["line1", "line2"]
        assert error.get_code_context_around_line(str(f), 3) == [
            "line1",
            "line2",
            "line3",
        ]
        assert error.get_code_context_around_line(str(f), 4) == [
            "line2",
            "line3",
            "line4",
        ]
        assert error.get_code_context_around_line(str(f), 5) == [
            "line3",
            "line4",
            "line5",
        ]

        invalid = str(tmp_path.joinpath("invalid"))
        assert error.get_code_context_around_line(invalid, 10) == []
