==========
pytest-cpp
==========

Use `pytest <https://pypi.python.org/pypi/pytest>`_ runner to discover and execute C++ tests.

|python| |version| |anaconda| |ci| |coverage|

Supports `Google Test <https://code.google.com/p/googletest>`_ ,
`Boost::Test <http://www.boost.org/doc/libs/release/libs/test>`_ and `QTest <http://doc.qt.io/qt-5/qtest.html>`_:

.. image:: https://raw.githubusercontent.com/pytest-dev/pytest-cpp/master/images/screenshot.png

.. |version| image:: http://img.shields.io/pypi/v/pytest-cpp.png
  :target: https://crate.io/packages/pytest-cpp

.. |anaconda| image:: https://anaconda.org/conda-forge/pytest-cpp/badges/version.svg
    :target: https://anaconda.org/conda-forge/pytest-cpp

.. |ci| image:: http://img.shields.io/travis/pytest-dev/pytest-cpp.png
  :target: https://travis-ci.org/pytest-dev/pytest-cpp

.. |coverage| image:: http://img.shields.io/coveralls/pytest-dev/pytest-cpp.png
  :target: https://coveralls.io/r/pytest-dev/pytest-cpp

.. |python| image:: https://img.shields.io/pypi/pyversions/pytest-cpp.svg
    :target: https://pypi.python.org/pypi/pytest-cpp/
    :alt: Supported Python versions

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
founds in executable files, detecting if the suites are
Google, Boost or Qt tests automatically.

You can configure which files are tested for suites by using the ``cpp_files``
ini configuration:

.. code-block:: ini

    [pytest]
    cpp_files=test_suite*

By default matches ``test_*`` and ``*_test`` executable files.

Requirements
============

* Python 2.7+, Python 3.4+
* pytest

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
