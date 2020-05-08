import pytest


@pytest.mark.parametrize(
    "name, passed, failed",
    [
        ("sample1_unittest", 6, 0),
        ("sample2_unittest", 4, 0),
        ("sample3_unittest", 3, 0),
        ("sample4_unittest", 1, 0),
        ("sample5_unittest", 4, 0),
        ("sample6_unittest", 12, 0),
        ("sample7_unittest", 6, 0),
        ("sample8_unittest", 12, 0),
        ("sample9_unittest", 2, 1),
        ("sample10_unittest", 2, 0),
    ],
)
def test_samples(exes, testdir, name, passed, failed):
    result = testdir.runpytest(exes.get("googletest-samples/%s" % name))
    if not failed:
        line = "%d passed in " % passed
    else:
        line = "%d failed, %d passed in " % (failed, passed)
    result.stdout.fnmatch_lines(["*%s*" % line])
