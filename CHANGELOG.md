# 2.6.0

*2024-09-17*

- Catch2: recognize `FAIL()` calls ([#147](https://github.com/pytest-dev/pytest-cpp/pull/147)).
- Dropped support for EOL Python 3.7.

# 2.5.0 (2023-11-01)

- Catch2: add support for catch version 3 ([#115](https://github.com/pytest-dev/pytest-cpp/pull/115)).
- Catch2: support exception handling ([#117](https://github.com/pytest-dev/pytest-cpp/pull/117)).
- Catch2: Correctly handle test names that contain special characters ([#123](https://github.com/pytest-dev/pytest-cpp/issues/123)).
- Added support for Python 3.12.

# 2.4.0 (2023-09-08)

- Catch2: fix issue with multiple test failures, and support multiple "SECTION" tests. ([#112](https://github.com/pytest-dev/pytest-cpp/pull/112))

# 2.3.0 (2023-01-30)

- New `cpp_harness_collect` configuration option allows users to add prefix arguments to run C++ test executables, allowing to use additional tools like `wine` of `qemu` for a test runners in cross-platform development.

# 2.2.1 (2022-09-23)

- Fixed a problem while handling errors using``--gtest_filter``. The recommendation is to use pytest's own
  filtering facilities (like `-k`) instead of passing filtering arguments to the underlying framework
  ([#84](https://github.com/pytest-dev/pytest-cpp/issues/84)).

# 2.2.0 (2022-08-22)

- Dropped support for Python 3.6.
- This plugin now requires pytest >=7.0.

# 2.1.2 (2022-03-18)

- Fix warnings in pytest 7.0 ([#78](https://github.com/pytest-dev/pytest-cpp/issues/78)).

# 2.1.1 (2021-12-06)

- Fix corner-case issue when no result attribute is found in google test XML output file.

# 2.1.0 (2021-12-03)

- Added support for `GTEST_SKIP()` skipped message from Google Test `1.11`.

# 2.0.0 (2021-06-04)

- `pytest-cpp` now supports [Catch2](https://github.com/catchorg/Catch2). Many thanks to [@salim-runsafe](https://github.com/salim-runsafe) for the contribution.

- Dropped support for Python 2.7 and 3.5.

# 1.5.0

- Added support for `GTEST_SKIP()` from Google Test 1.10.

# 1.4.0

- New `cpp_verbose` configuration option prints the full output of the C++ test runner as the test finishes. Thanks to @dajose for contributing.

- Now the output of the C++ test run is shown in its own section during test failure, similar to the `captured out` and `captured err` sections shown by pytest. Thanks to @dajose for contributing.


# 1.3.0

- New `cpp_harness` configuration option allows users to add prefix arguments when running the C++ test runner, allowing to use tools like `valgrind`. Thanks to @dajose for contributing!

# 1.2.1

- Remove `from_parent()`-related warnings in pytest 5.4.2+.

- Masks like `*_test` now work correctly on Windows by automatically appending the
  expected `".exe"` suffix (#45).
  Thanks @1fabrism for the report.

# 1.2.0

- `pytest-cpp` no longer supports Python 3.4.
- New `cpp_ignore_py_files` option that makes the plugin ignore `*.py` files even if they
  would otherwise match the `cpp_files` option (defaults to `True`).

# 1.1.0

- New `cpp_arguments` ini option allows customization of the command-line
  used to run tests, for example to enable logging and verbosity.
  Thanks @elkin for the PR.

# 1.0.1

- Use universal newlines for running Google tests (#33).
  Thanks @elkin for the PR.

# 0.4.5

- Properly handle fatal errors in Boost.Test.
  Thanks @dplucenio for the report.


# 0.4.4

- Properly handle fixture failures in Boost.Test.
  Thanks @fj128 for the PR.

# 0.4.3

- Use XML in CAPS since beginning at Boost 1.61 the parameter value is case sensitive (#29).
  Thanks @edisongustavo for the PR.

# 0.4.2 #

- Proper fix for #25, the fix made in `0.4.1` was incorrect.

# 0.4.1 #

- Fix error that may happen during collection when using xdist (#25).

# 0.4.0 #

- Integrated most of the examples found in boost-1.55 for Boost Test into the
  `pytest-cpp` test suite. This uncovered a problem when Fatal Errors were
  produced and which would break py.test.

- Integrated all the official Google Test examples into the `pytest-cpp` test
  suite, ensuring that Google Test is fully covered.

- Fixed #17: supporting Type-Parametrized tests in Google Test. Thanks
  @joarbe for the report.

- Now any executable passed explicitly to py.test in the
  command-line will run as a test, regardless of the `cpp_files` option.

# 0.3.1 #

- Now capturing standard error while collecting tests, otherwise
executable files that are not test suites could write into `stderr`,
which would mess with `py.test`'s output to console.

# 0.3.0 #

- Display more than one failure in a `Google` test for `EXPECT` calls, instead of only the first one.
- Improved code coverage and fixed a number of small issues when internal errors occurred.

# 0.2.0 #

- `cpp_files` option to `pytest.ini` files.
- `Boost::Test` suites now writes reports to a file, which makes
it behave correctly if a test writes in `std::cout` or `std::cerr`.

# 0.1.0 #

Support for Google Test and Boost Test.
