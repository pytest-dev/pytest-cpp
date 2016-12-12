import fnmatch
import os
import stat
import pytest
from pytest_cpp.boost import BoostTestFacade

from pytest_cpp.error import CppFailureRepr, CppFailureError

from pytest_cpp.google import GoogleTestFacade

from pytest_cpp.qt import QTestLibFacade

FACADES = [GoogleTestFacade, BoostTestFacade, QTestLibFacade]
DEFAULT_MASKS = ('test_*', '*_test')


def pytest_collect_file(parent, path):
    try:
        is_executable = os.stat(str(path)).st_mode & stat.S_IXUSR
    except OSError:
        # in some situations the file might not be available anymore at this point
        is_executable = False
    if not is_executable:
        return
    masks = parent.config.getini('cpp_files') or DEFAULT_MASKS
    if not parent.session.isinitpath(path):
        for pat in masks:
            if path.fnmatch(pat):
                break
        else:
            return
    for facade_class in FACADES:
        if facade_class.is_test_suite(str(path)):
            return CppFile(path, parent, facade_class())


def pytest_addoption(parser):
    parser.addini("cpp_files", type="args",
        default=DEFAULT_MASKS,
        help="glob-style file patterns for C++ test module discovery")


class CppFile(pytest.File):
    def __init__(self, path, parent, facade):
        pytest.File.__init__(self, path, parent)
        self.facade = facade

    def collect(self):
        for test_id in self.facade.list_tests(str(self.fspath)):
            yield CppItem(test_id, self, self.facade)


class CppItem(pytest.Item):
    def __init__(self, name, collector, facade):
        pytest.Item.__init__(self, name, collector)
        self.facade = facade

    def runtest(self):
        failures = self.facade.run_test(str(self.fspath), self.name)
        if failures:
            raise CppFailureError(failures)

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, CppFailureError):
            return CppFailureRepr(excinfo.value.failures)
        return pytest.Item.repr_failure(self, excinfo)

    def reportinfo(self):
        return self.fspath, 0, self.name



