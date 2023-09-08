import pytest


@pytest.mark.parametrize(
    "name, passed, failed",
    [
        ("010-TestCase", 1, 1),
        ("020-TestCase", 2, 1),
        ("030-Asn-Require-Check", 1, 5),
        ("100-Fix-Section", 1, 0),
        ("110-Fix-ClassFixture", 2, 0),
        ("120-Bdd-ScenarioGivenWhenThen", 1, 0),
    ],
)
def test_samples(exes, testdir, name, passed, failed):
    result = testdir.runpytest(exes.get("catch2-samples/%s" % name))
    if not failed:
        line = "%d passed in " % passed
    else:
        line = "%d failed, %d passed in " % (failed, passed)
    result.stdout.fnmatch_lines(["*%s*" % line])
