from __future__ import annotations

import enum
import os
import subprocess
import tempfile
from typing import Optional
from typing import Sequence
from xml.etree import ElementTree

import pytest

from pytest_cpp.error import CppTestFailure
from pytest_cpp.error import Markup
from pytest_cpp.facade_abc import AbstractFacade
from pytest_cpp.helpers import make_cmdline


# Map each special character's Unicode ordinal to the escaped character.
_special_chars_map: dict[int, str] = {i: "\\" + chr(i) for i in b'[]*,~\\"'}


def escape(test_id: str) -> str:
    """Escape special characters in test names (see #123)."""
    return test_id.translate(_special_chars_map)


class Catch2Version(enum.Enum):
    V2 = "v2"
    V3 = "v3"


class Catch2Facade(AbstractFacade):
    """
    Facade for Catch2.
    """

    @classmethod
    def get_catch_version(
        cls,
        executable: str,
        harness_collect: Sequence[str] = (),
    ) -> Optional[Catch2Version]:
        args = make_cmdline(harness_collect, executable, ["--help"])
        try:
            output = subprocess.check_output(
                args,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except (subprocess.CalledProcessError, OSError):
            return None
        else:
            return (
                Catch2Version.V2
                if "--list-test-names-only" in output
                else Catch2Version.V3 if "--list-tests" in output else None
            )

    @classmethod
    def is_test_suite(
        cls,
        executable: str,
        harness_collect: Sequence[str] = (),
    ) -> bool:
        return cls.get_catch_version(executable, harness_collect) in [
            Catch2Version.V2,
            Catch2Version.V3,
        ]

    def list_tests(
        self,
        executable: str,
        harness_collect: Sequence[str] = (),
    ) -> list[str]:
        """
        Executes test with "--list-test-names-only" (v2) or "--list-tests --verbosity quiet" (v3) and gets list of tests
        parsing output like this:

        1: All test cases reside in other .cpp files (empty)
        2: Factorial of 0 is 1 (fail)
        2: Factorials of 1 and higher are computed (pass)
        """
        # This will return an exit code with the number of tests available
        exec_args = (
            ["--list-test-names-only"]
            if self.get_catch_version(executable, harness_collect) == Catch2Version.V2
            else ["--list-tests", "--verbosity quiet"]
        )
        args = make_cmdline(harness_collect, executable, exec_args)
        try:
            output = subprocess.check_output(
                args,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as e:
            output = e.output

        result = output.strip().split("\n")

        return result

    def run_test(
        self,
        executable: str,
        test_id: str = "",
        test_args: Sequence[str] = (),
        harness: Sequence[str] = (),
    ) -> tuple[Sequence[Catch2Failure] | None, str]:
        with tempfile.TemporaryDirectory(prefix="pytest-cpp") as temp_dir:
            """
            On Windows, ValueError is raised when path and start are on different drives.
            In this case failing back to the absolute path.
            """
            catch_version = self.get_catch_version(executable, harness)

            if catch_version is None:
                raise Exception("Invalid Catch Version")

            try:
                xml_filename = os.path.join(os.path.relpath(temp_dir), "cpp-report.xml")
            except ValueError:
                xml_filename = os.path.join(temp_dir, "cpp-report.xml")
            exec_args = [
                escape(test_id),
                "--success",
                "--reporter=xml",
                f"--out={xml_filename}",
            ]
            exec_args.extend(test_args)
            args = make_cmdline(harness, executable, exec_args)

            try:
                output = subprocess.check_output(
                    args, stderr=subprocess.STDOUT, universal_newlines=True
                )
            except subprocess.CalledProcessError as e:
                output = e.output

            results = self._parse_xml(xml_filename, catch_version)

        for executed_test_id, failures, skipped in results:
            if executed_test_id == test_id:
                if failures:
                    return (
                        [
                            Catch2Failure(filename, linenum, lines)
                            for (filename, linenum, lines) in failures
                        ],
                        output,
                    )
                elif skipped:
                    pytest.skip()
                else:
                    return None, output

        msg = "Internal Error: could not find test {test_id} in results:\n{results}"

        results_list = "\n".join(n for (n, x, f) in results)
        failure = Catch2Failure(
            msg.format(test_id=test_id, results=results_list), 0, ""
        )
        return [failure], output

    def _parse_xml(
        self, xml_filename: str, catch_version: Catch2Version
    ) -> Sequence[tuple[str, Sequence[tuple[str, int, str]], bool]]:
        root = ElementTree.parse(xml_filename)
        result = []
        test_suites = (
            root.findall("Group")
            if catch_version == Catch2Version.V2
            else root.iter("Catch2TestRun")
        )
        for test_suite in test_suites:
            for test_case in test_suite.findall("TestCase"):
                test_name = test_case.attrib["name"]
                test_result = test_case.find("OverallResult")
                failures = []
                if test_result is not None and test_result.attrib["success"] == "false":
                    test_checks = test_case.findall(".//Expression")
                    for check in test_checks:
                        file_name = check.attrib["filename"]
                        line_num = int(check.attrib["line"])
                        if check is not None and check.attrib["success"] == "false":
                            item = check.find("Original")
                            expected = item.text if item is not None else ""
                            item = check.find("Expanded")
                            actual = item.text if item is not None else ""
                            fail_msg = "Expected: {expected}\nActual: {actual}".format(
                                expected=expected, actual=actual
                            )
                            failures.append(
                                (
                                    file_name,
                                    line_num,
                                    fail_msg,
                                )
                            )
                    # These two tags contain the same attributes and can be treated the same
                    test_exception = test_case.findall(".//Exception")
                    test_failure = test_case.findall(".//Failure")
                    for exception in test_exception + test_failure:
                        file_name = exception.attrib["filename"]
                        line_num = int(exception.attrib["line"])

                        fail_msg = f"Error: {exception.text}"
                        failures.append(
                            (
                                file_name,
                                line_num,
                                fail_msg,
                            )
                        )
                skipped = False  # TODO: skipped tests don't appear in the results
                result.append((test_name, failures, skipped))

        return result


class Catch2Failure(CppTestFailure):
    def __init__(self, filename: str, linenum: int, lines: str):
        self.lines = lines.splitlines()
        self.filename = filename
        self.linenum = linenum

    def get_lines(self) -> list[tuple[str, Markup]]:
        m = ("red", "bold")
        return [(x, m) for x in self.lines]

    def get_file_reference(self) -> tuple[str, int]:
        return self.filename, self.linenum
