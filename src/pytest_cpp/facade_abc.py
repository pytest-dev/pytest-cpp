from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Sequence

from pytest_cpp.error import CppTestFailure


class AbstractFacade(ABC):
    @classmethod
    @abstractmethod
    def is_test_suite(
        cls,
        executable: str,
        harness_collect: Sequence[str] = (),
    ) -> bool:
        """Return True if the given path to an executable contains tests for this framework."""

    @abstractmethod
    def list_tests(
        self,
        executable: str,
        harness_collect: Sequence[str] = (),
    ) -> list[str]:
        """Return a list of test ids found in the given executable."""

    @abstractmethod
    def run_test(
        self,
        executable: str,
        test_id: str,
        test_args: Sequence[str] = (),
        harness: Sequence[str] = (),
    ) -> tuple[Sequence[CppTestFailure] | None, str]:
        """
        Runs a test and returns the results.

        :param executable:
            The executable with the tests.

        :param test_id:
            A test id as returned by ``list_tests``.

        :param test_args:
            A list of extra arguments that will be passed along to the call to the executable.

        :param harness:
            If given, extra arguments which will be prepended to the command line, which
            usually wraps the executable for performance and/or memory profiling.

        :return:
            Return a tuple of:
            * list of failures, or None.
            * output from the executable call
        """
