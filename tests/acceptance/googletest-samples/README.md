This contains the full, unmodified samples from the
[googletest](https://github.com/google/googletest) repository, used to ensure
that `pytest-cpp` can run it completely.

An exception is the `main.cc` file, which contains a simple `main()` function
that is linked to tests which don't declare their own `main()`.
