import pytest


@pytest.mark.parametrize(
    "name, passed, failed",
    [
        ("unit_test_example_01", 0, 1),
        ("unit_test_example_02", 0, 1),
        ("unit_test_example_03", 0, 1),
        ("unit_test_example_04", 0, 1),
        ("unit_test_example_05", 0, 1),
        ("unit_test_example_06", 0, 1),
        ("unit_test_example_07", 1, 0),
        ("unit_test_example_08", 0, 1),
        ("unit_test_example_09_1", 1, 0),
        ("unit_test_example_09_2", 1, 0),
        ("unit_test_example_13", 1, 0),
        ("utest_case_template_example", 0, 1),
    ],
)
def test_samples(exes, testdir, name, passed, failed):
    result = testdir.runpytest(exes.get("boosttest-samples/%s" % name))
    phrases = []
    if failed:
        phrases.append("%d failed" % failed)
    if passed:
        phrases.append("%d passed" % passed)
    line = ", ".join(phrases) + " in "
    result.stdout.fnmatch_lines(["*%s*" % line])
    assert "Internal Error" not in result.stdout.str()


def test_example_11(exes, testdir):
    """
    "unit_test_example_11" generates an invalid XML by having two XML roots:
    <FatalError> and <TestLog>. --'
    """
    example = "boosttest-samples/unit_test_example_11"
    result = testdir.runpytest(exes.get(example))
    result.stdout.fnmatch_lines(
        [
            "*something happened*",
            "*check s.substr*",
            "*1 failed in*",
        ]
    )
