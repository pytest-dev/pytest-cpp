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