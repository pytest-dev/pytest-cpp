This contains examples from the `libs\test\example` directory in the boost
distribution.

Changes:

* Made tests compile in "single header" mode by including the
  `<boost/test/included/unit_test.hpp>` header.
* Excluded `unit_test_example_10.cpp` and `unit_test_example_12.cpp`,
  as these tests require user input from the terminal.
* `test_case_template_example.cpp` was renamed to
  `utest_case_template_example.cpp` so it isn't picked up by `py.test`
  during `pytest-cpp`'s own test suite execution.
