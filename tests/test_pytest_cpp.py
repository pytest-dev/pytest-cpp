import subprocess
import sys
from distutils.spawn import find_executable

import pytest

from pytest_cpp import error
from pytest_cpp.boost import BoostTestFacade
from pytest_cpp.catch2 import Catch2Facade
from pytest_cpp.error import CppFailureRepr, CppTestFailure
from pytest_cpp.google import GoogleTestFacade


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
            ],
        ),
        (BoostTestFacade(), "boost_success", ["boost_success"]),
        (BoostTestFacade(), "boost_error", ["boost_error"]),
        (BoostTestFacade(), "boost_fixture_setup_error", ["boost_fixture_setup_error"]),
        (Catch2Facade(), "catch2_success", ["Factorials are computed"]),
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
def test_is_test_suite(facade, name, other_name, exes, tmpdir):
    assert facade.is_test_suite(exes.get(name))
    assert not facade.is_test_suite(exes.get(other_name))
    tmpdir.ensure("foo.txt")
    assert not facade.is_test_suite(str(tmpdir.join("foo.txt")))


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


def test_google_failure(exes):
    facade = GoogleTestFacade()
    failures, _ = facade.run_test(exes.get("gtest"), "FooTest.test_failure")
    assert len(failures) == 2
    colors = ("red", "bold")
    assert failures[0].get_lines() == [
        ("      Expected: 2 * 3", colors),
        ("      Which is: 6", colors),
        ("To be equal to: 5", colors),
    ]
    assert failures[0].get_file_reference() == ("gtest.cpp", 19)

    assert failures[1].get_lines() == [
        ("      Expected: 2 * 6", colors),
        ("      Which is: 12", colors),
        ("To be equal to: 15", colors),
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
    with pytest.raises(pytest.skip.Exception):
        facade.run_test(exes.get("gtest"), "FooTest.DISABLED_test_disabled")


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
        ],
    )


def test_unknown_error(testdir, exes, mocker):
    mocker.patch.object(
        GoogleTestFacade, "run_test", side_effect=RuntimeError("unknown error")
    )
    result = testdir.inline_run("-v", exes.get("gtest", "test_gtest"))
    rep = result.matchreport("FooTest.test_success", "pytest_runtest_logreport")
    assert "unknown error" in str(rep.longrepr)


def test_google_internal_errors(mocker, testdir, exes, tmpdir):
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
    xml_file = tmpdir.join("results.xml")
    xml_file.write("<empty/>")
    mocker.patch.object(
        GoogleTestFacade, "_get_temp_xml_filename", return_value=str(xml_file)
    )
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
        ["*CppFile boost_success*", "*CppFile gtest*",]
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
    not find_executable("valgrind") or not find_executable("catchsegv"),
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
    not find_executable("valgrind") or not find_executable("catchsegv"),
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


def test_race_condition_on_collect(tmpdir):
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

    assert pytest_cpp.plugin.pytest_collect_file(None, tmpdir / "invalid-file") is None


def test_exe_mask_on_windows(tmpdir, monkeypatch):
    """
    Test for #45: C++ tests not collected due to '*_test' mask on Windows
    """
    import pytest_cpp.plugin

    monkeypatch.setattr(sys, "platform", "win32")

    fn = tmpdir.join("generator_demo_test.exe").ensure(file=1)
    assert pytest_cpp.plugin.matches_any_mask(fn, ["test_*", "*_test"])

    fn = tmpdir.join("test_generator_demo.exe").ensure(file=1)
    assert pytest_cpp.plugin.matches_any_mask(fn, ["test_*", "*_test"])

    fn = tmpdir.join("my_generator_test_demo.exe").ensure(file=1)
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


def test_catch2_failure(exes):
    facade = Catch2Facade()
    failures, _ = facade.run_test(exes.get("catch2_failure"), "Factorials are computed")
    assert len(failures) == 1

    fail1 = failures[0]
    colors = ("red", "bold")
    assert fail1.get_lines() == [
        ("Expected: ", colors),
        ("          Factorial(1) == 0", colors),
        ("        ", colors),
        ("Actual: ", colors),
        ("          1 == 0", colors),
        ("        ", colors),
    ]

    assert fail1.get_file_reference() == ("catch2_failure.cpp", 9)


class TestError:
    def test_get_whitespace(self):
        assert error.get_left_whitespace("  foo") == "  "
        assert error.get_left_whitespace("\t\t foo") == "\t\t "

    def test_get_code_context_around_line(self, tmpdir):
        f = tmpdir.join("foo.py")
        f.write("line1\nline2\nline3\nline4\nline5")

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

        invalid = str(tmpdir.join("invalid"))
        assert error.get_code_context_around_line(invalid, 10) == []
