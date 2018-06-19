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
