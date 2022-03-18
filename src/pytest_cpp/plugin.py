import os
import stat
import sys
from fnmatch import fnmatch

import pytest

from pytest_cpp.boost import BoostTestFacade
from pytest_cpp.error import CppFailureRepr, CppFailureError
from pytest_cpp.google import GoogleTestFacade
from pytest_cpp.catch2 import Catch2Facade

FACADES = [GoogleTestFacade, BoostTestFacade, Catch2Facade]
DEFAULT_MASKS = ("test_*", "*_test")

_ARGUMENTS = "cpp_arguments"


# pytest 5.4 introduced the 'from_parent' constructor
needs_from_parent = hasattr(pytest.Item, "from_parent")


def matches_any_mask(path, masks):
    """Return True if the given path matches any of the masks given"""
    if sys.platform.startswith("win"):
        masks = [m + ".exe" for m in masks]
    return any(fnmatch(path.name, m) for m in masks)


def pytest_collect_file(parent, file_path):
    try:
        is_executable = os.stat(str(file_path)).st_mode & stat.S_IXUSR
    except OSError:
        # in some situations the file might not be available anymore at this point
        is_executable = False
    if not is_executable:
        return

    config = parent.config
    masks = config.getini("cpp_files")
    test_args = config.getini("cpp_arguments")
    cpp_ignore_py_files = config.getini("cpp_ignore_py_files")

    # don't attempt to check *.py files even if they were given as explicit arguments
    if cpp_ignore_py_files and fnmatch(file_path.name, "*.py"):
        return

    if not parent.session.isinitpath(file_path) and not matches_any_mask(
        file_path, masks
    ):
        return

    for facade_class in FACADES:
        if facade_class.is_test_suite(str(file_path)):
            if needs_from_parent:
                return CppFile.from_parent(
                    path=file_path,
                    parent=parent,
                    facade=facade_class(),
                    arguments=test_args,
                )
            else:
                return CppFile(
                    path=file_path,
                    parent=parent,
                    facade_class=facade_class(),
                    arguments=test_args,
                )


def pytest_addoption(parser):
    parser.addini(
        "cpp_files",
        type="args",
        default=DEFAULT_MASKS,
        help="glob-style file patterns for C++ test module discovery",
    )
    parser.addini(
        "cpp_arguments",
        type="args",
        default=(),
        help="additional arguments for test executables",
    )
    parser.addini(
        "cpp_ignore_py_files",
        type="bool",
        default=True,
        help='ignore *.py files that otherwise match "cpp_files" patterns',
    )
    parser.addini(
        "cpp_harness",
        type="args",
        default=(),
        help="command that wraps the cpp binary",
    )
    parser.addini(
        "cpp_verbose",
        type="bool",
        default=False,
        help="print the test output right after it ran, requires -s",
    )


class CppFile(pytest.File):
    def __init__(self, *, path, parent, facade, arguments, **kwargs):
        pytest.File.__init__(self, path=path, parent=parent, **kwargs)
        self.facade = facade
        self._arguments = arguments

    @classmethod
    def from_parent(cls, *, parent, path, facade, arguments, **kwargs):
        return super().from_parent(
            parent=parent, path=path, facade=facade, arguments=arguments
        )

    def collect(self):
        for test_id in self.facade.list_tests(str(self.fspath)):
            if needs_from_parent:
                yield CppItem.from_parent(
                    parent=self,
                    name=test_id,
                    facade=self.facade,
                    arguments=self._arguments,
                )
            else:
                yield CppItem(test_id, self, self.facade, self._arguments)


class CppItem(pytest.Item):
    def __init__(self, *, name, parent, facade, arguments, **kwargs):
        pytest.Item.__init__(self, name, parent, **kwargs)
        self.facade = facade
        self._arguments = arguments

    @classmethod
    def from_parent(cls, *, parent, name, facade, arguments, **kw):
        return super().from_parent(
            name=name, parent=parent, facade=facade, arguments=arguments, **kw
        )

    def runtest(self):
        failures, output = self.facade.run_test(
            str(self.fspath),
            self.name,
            self._arguments,
            harness=self.config.getini("cpp_harness"),
        )
        # Report the c++ output in its own sections
        self.add_report_section("call", "c++", output)

        if self.config.getini("cpp_verbose"):
            print(output)

        if failures:
            raise CppFailureError(failures)

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, CppFailureError):
            return CppFailureRepr(excinfo.value.failures)
        return pytest.Item.repr_failure(self, excinfo)

    def reportinfo(self):
        return self.fspath, 0, self.name
