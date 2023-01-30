from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Sequence
from xml.etree import ElementTree

import pytest

from pytest_cpp.error import CppTestFailure
from pytest_cpp.error import Markup
from pytest_cpp.facade_abc import AbstractFacade
from pytest_cpp.helpers import make_cmdline


class Catch2Facade(AbstractFacade):
    """
    Facade for Catch2.
    """

    @classmethod
    def is_test_suite(
        cls,
        executable: str,
        harness_collect: Sequence[str] = (),
    ) -> bool:
        args = make_cmdline(harness_collect, executable, ["--help"])
        try:
            output = subprocess.check_output(
                args,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except (subprocess.CalledProcessError, OSError):
            return False
        else:
            return "--list-test-names-only" in output

    def list_tests(
        self,
        executable: str,
        harness_collect: Sequence[str] = (),
    ) -> list[str]:
        """
        Executes test with "--list-test-names-only" and gets list of tests
        parsing output like this:

        1: All test cases reside in other .cpp files (empty)
        2: Factorial of 0 is 1 (fail)
        2: Factorials of 1 and higher are computed (pass)
        """
        # This will return an exit code with the number of tests available
        args = make_cmdline(harness_collect, executable, ["--list-test-names-only"])
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
            try:
                xml_filename = os.path.join(os.path.relpath(temp_dir), "cpp-report.xml")
            except ValueError:
                xml_filename = os.path.join(temp_dir, "cpp-report.xml")
            args = list(
                make_cmdline(
                    harness,
                    executable,
                    [test_id, "--success", "--reporter=xml", f"--out {xml_filename}"],
                )
            )
            args.extend(test_args)

            try:
                output = subprocess.check_output(
                    args, stderr=subprocess.STDOUT, universal_newlines=True
                )
            except subprocess.CalledProcessError as e:
                output = e.output
                if e.returncode != 1:
                    msg = (
                        "Internal Error: calling {executable} "
                        "for test {test_id} failed (returncode={returncode}):\n"
                        "{output}"
                    )
                    failure = Catch2Failure(
                        executable,
                        0,
                        msg.format(
                            executable=executable,
                            test_id=test_id,
                            output=e.output,
                            returncode=e.returncode,
                        ),
                    )

                    return [failure], output

            results = self._parse_xml(xml_filename)

        for (executed_test_id, failures, skipped) in results:
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
        self, xml_filename: str
    ) -> Sequence[tuple[str, Sequence[tuple[str, int, str]], bool]]:
        root = ElementTree.parse(xml_filename)
        result = []
        for test_suite in root.findall("Group"):
            for test_case in test_suite.findall("TestCase"):
                test_name = test_case.attrib["name"]
                test_result = test_case.find("OverallResult")
                failures = []
                if test_result is not None and test_result.attrib["success"] == "false":
                    test_checks = test_case.findall("Expression")
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
