from __future__ import annotations

import os
import stat
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Any
from typing import Iterator
from typing import Sequence
from typing import Type
from typing import TYPE_CHECKING

import pytest

from pytest_cpp.boost import BoostTestFacade
from pytest_cpp.catch2 import Catch2Facade
from pytest_cpp.error import CppFailureError
from pytest_cpp.error import CppFailureRepr
from pytest_cpp.facade_abc import AbstractFacade
from pytest_cpp.google import GoogleTestFacade

if TYPE_CHECKING:
    from _pytest._code.code import TerminalRepr


FACADES: Sequence[Type[AbstractFacade]] = (
    GoogleTestFacade,
    BoostTestFacade,
    Catch2Facade,
)
DEFAULT_MASKS = ("test_*", "*_test")

_ARGUMENTS = "cpp_arguments"


def matches_any_mask(path: Path, masks: Sequence[str]) -> bool:
    """Return True if the given path matches any of the masks given"""
    if sys.platform.startswith("win"):
        masks = [m + ".exe" for m in masks]
    return any(fnmatch(path.name, m) for m in masks)


def pytest_collect_file(
    parent: pytest.Collector, file_path: Path
) -> pytest.Collector | None:
    try:
        is_executable = os.stat(str(file_path)).st_mode & stat.S_IXUSR
    except OSError:
        # in some situations the file might not be available anymore at this point
        is_executable = False
    if not is_executable:
        return None

    config = parent.config
    masks = config.getini("cpp_files")
    test_args = config.getini("cpp_arguments")
    cpp_ignore_py_files = config.getini("cpp_ignore_py_files")

    # don't attempt to check *.py files even if they were given as explicit arguments
    if cpp_ignore_py_files and fnmatch(file_path.name, "*.py"):
        return None

    if not parent.session.isinitpath(file_path) and not matches_any_mask(
        file_path, masks
    ):
        return None

    harness_collect = parent.config.getini("cpp_harness_collect")
    for facade_class in FACADES:
        if facade_class.is_test_suite(str(file_path), harness_collect=harness_collect):
            return CppFile.from_parent(
                path=file_path,
                parent=parent,
                facade=facade_class(),
                arguments=test_args,
            )

    return None


def pytest_addoption(parser: pytest.Parser) -> None:
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
        help="command that wraps the cpp binary when running tests",
    )
    parser.addini(
        "cpp_harness_collect",
        type="args",
        default=(),
        help="command that wraps the cpp binary when collecting tests",
    )
    parser.addini(
        "cpp_verbose",
        type="bool",
        default=False,
        help="print the test output right after it ran, requires -s",
    )


class CppFile(pytest.File):
    def __init__(
        self,
        *,
        path: Path,
        parent: pytest.Item,
        facade: AbstractFacade,
        arguments: Sequence[str],
        **kwargs: Any,
    ) -> None:
        super().__init__(path=path, parent=parent, **kwargs)
        self.facade = facade
        self._arguments = arguments

    @classmethod
    def from_parent(  # type:ignore[override]
        cls,
        *,
        parent: pytest.Collector,
        path: Path,
        facade: AbstractFacade,
        arguments: Sequence[str],
        **kwargs: Any,
    ) -> CppFile:
        return super().from_parent(
            parent=parent, path=path, facade=facade, arguments=arguments
        )

    def collect(self) -> Iterator[CppItem]:
        harness_collect = self.config.getini("cpp_harness_collect")
        for test_id in self.facade.list_tests(
            str(self.fspath),
            harness_collect=harness_collect,
        ):
            yield CppItem.from_parent(
                parent=self,
                name=test_id,
                facade=self.facade,
                arguments=self._arguments,
            )


class CppItem(pytest.Item):
    def __init__(
        self,
        *,
        name: str,
        parent: pytest.Collector,
        facade: AbstractFacade,
        arguments: Sequence[str],
        **kwargs: Any,
    ) -> None:
        pytest.Item.__init__(self, name, parent, **kwargs)
        self.facade = facade
        self._arguments = arguments

    @classmethod
    def from_parent(  # type:ignore[override]
        cls,
        *,
        parent: pytest.Collector,
        name: str,
        facade: AbstractFacade,
        arguments: Sequence[str],
        **kwargs: Any,
    ) -> CppItem:
        return super().from_parent(
            name=name, parent=parent, facade=facade, arguments=arguments, **kwargs
        )

    def runtest(self) -> None:
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

    def repr_failure(  # type:ignore[override]
        self, excinfo: pytest.ExceptionInfo[BaseException]
    ) -> str | TerminalRepr | CppFailureRepr:
        if isinstance(excinfo.value, CppFailureError):
            return CppFailureRepr(excinfo.value.failures)
        return pytest.Item.repr_failure(self, excinfo)

    def reportinfo(self) -> tuple[Any, int, str]:
        return self.fspath, 0, self.name
