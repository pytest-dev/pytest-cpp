==========
pytest-cpp
==========

Use `pytest <https://pypi.python.org/pypi/pytest>`_ runner to discover and execute C++ tests.

|python| |version| |anaconda| |ci| |coverage| |black|

Supports both `Google Test <https://code.google.com/p/googletest>`_ and
`Boost::Test <http://www.boost.org/doc/libs/release/libs/test>`_:

.. image:: https://raw.githubusercontent.com/pytest-dev/pytest-cpp/master/images/screenshot.png

.. |version| image:: http://img.shields.io/pypi/v/pytest-cpp.png
  :target: https://crate.io/packages/pytest-cpp

.. |anaconda| image:: https://img.shields.io/conda/vn/conda-forge/pytest-cpp.svg
    :target: https://anaconda.org/conda-forge/pytest-cpp

.. |ci| image:: http://img.shields.io/travis/pytest-dev/pytest-cpp.png
  :target: https://travis-ci.org/pytest-dev/pytest-cpp

.. |coverage| image:: http://img.shields.io/coveralls/pytest-dev/pytest-cpp.png
  :target: https://coveralls.io/r/pytest-dev/pytest-cpp

.. |python| image:: https://img.shields.io/pypi/pyversions/pytest-cpp.svg
    :target: https://pypi.python.org/pypi/pytest-cpp/
    :alt: Supported Python versions

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

This brings several benefits:

* Allows you to run all your tests in multi-language projects with a single
  command;
* Execute C++ tests in **parallel** using
  `pytest-xdist <https://pypi.python.org/pypi/pytest-xdist>`_ plugin;
* Use ``--junitxml`` option to produce a single and uniform xml file with all
  your test suite results;
* Filter which tests to run using standard test filtering capabilities, such as
  by file names, directories, keywords by using the ``-k`` option, etc.;

Usage
=====

Once installed, when py.test runs it will search and run tests
found in executable files, detecting if the suites are
Google or Boost tests automatically.

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

**cpp_files**

You can configure which files are tested for suites by using the ``cpp_files``
ini configuration option:

.. code-block:: ini

    [pytest]
    cpp_files = test_suite*

By default matches ``test_*`` and ``*_test`` executable files.

**cpp_arguments**

*New in version 1.1*.

Arguments to the C++ tests can be provided with the
``cpp_arguments`` ini configuration option.

For example:

.. code-block:: ini

    [pytest]
    cpp_arguments =-v --log-dir=logs

You can change this option directly in the command-line using
pytest's ``-o`` option:

.. code-block:: console

    $ pytest -o cpp_arguments='-v --log-dir=logs'

**cpp_ignore_py_files**

*New in version 1.2*.

This option defaults to ``True`` and configures the plugin to ignore ``*.py`` files that
would otherwise match the ``cpp_files`` option.

Set it to ``False`` if you have C++ executable files that end with the ``*.py`` extension.

.. code-block:: ini

    [pytest]
    cpp_ignore_py_files = False

**cpp_harness**

This option allows the usage of tools that are used by invoking them on the console
wrapping the test binary, like valgrind and memcheck

.. code-block:: ini

    [pytest]
    cpp_harness = valgrind --tool=memcheck

Install
=======

Install using `pip <http://pip-installer.org/>`_:

.. code-block:: console

    $ pip install pytest-cpp

Changelog
=========

Please consult `CHANGELOG <https://github.com/pytest-dev/pytest-cpp/blob/master/CHANGELOG.md>`_.

Support
=======

All feature requests and bugs are welcome, so please make sure to add
feature requests and bugs to the
`issues <https://github.com/pytest-dev/pytest-cpp/issues>`_ page!
