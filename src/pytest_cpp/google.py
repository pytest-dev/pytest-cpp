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


class GoogleTestFacade(AbstractFacade):
    """
    Facade for GoogleTests.
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
            return "--gtest_list_tests" in output

    def list_tests(
        self,
        executable: str,
        harness_collect: Sequence[str] = (),
    ) -> list[str]:
        """
        Executes google-test with "--gtest_list_tests" and gets list of tests
        parsing output like this:

        PrimeTableTest/0.  # TypeParam = class OnTheFlyPrimeTable
          ReturnsFalseForNonPrimes
          ReturnsTrueForPrimes
          CanGetNextPrime
        """
        args = make_cmdline(harness_collect, executable, ["--gtest_list_tests"])
        output = subprocess.check_output(
            args,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        def strip_comment(x: str) -> str:
            comment_start = x.find("#")
            if comment_start != -1:
                x = x[:comment_start]
            return x

        test_suite: str | None = None
        result = []
        for line in output.splitlines():
            has_indent = line.startswith(" ")
            if not has_indent and "." in line:
                test_suite = strip_comment(line).strip()
            elif has_indent:
                assert test_suite is not None
                result.append(test_suite + strip_comment(line).strip())
        return result

    def run_test(
        self,
        executable: str,
        test_id: str,
        test_args: Sequence[str] = (),
        harness: Sequence[str] = (),
    ) -> tuple[list[GoogleTestFailure] | None, str]:
        with tempfile.TemporaryDirectory(prefix="pytest-cpp") as temp_dir:
            # On Windows, ValueError is raised when path and start are on different drives.
            # In this case failing back to the absolute path.
            try:
                xml_filename = os.path.join(os.path.relpath(temp_dir), "cpp-report.xml")
            except ValueError:
                xml_filename = os.path.join(temp_dir, "cpp-report.xml")
            args = list(
                make_cmdline(
                    harness,
                    executable,
                    [f"--gtest_filter={test_id}", f"--gtest_output=xml:{xml_filename}"],
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
                    failure = GoogleTestFailure(
                        msg.format(
                            executable=executable,
                            test_id=test_id,
                            output=e.output,
                            returncode=e.returncode,
                        )
                    )

                    return [failure], output

            results = self._parse_xml(xml_filename)

        for executed_test_id, failures, skipped in results:
            if executed_test_id == test_id:
                if failures:
                    return [GoogleTestFailure(x) for x in failures], output
                elif skipped:
                    pytest.skip("\n".join(skipped))
                else:
                    return None, output

        msg = "Internal Error: could not find test " "{test_id} in results:\n{results}"
        results_list = "\n".join(x for (x, f, s) in results)
        failure = GoogleTestFailure(msg.format(test_id=test_id, results=results_list))
        return [failure], output

    def _parse_xml(
        self, xml_filename: str
    ) -> Sequence[tuple[str, Sequence[str], Sequence[str]]]:
        root = ElementTree.parse(xml_filename)
        result = []
        for test_suite in root.findall("testsuite"):
            test_suite_name = test_suite.attrib["name"]
            for test_case in test_suite.findall("testcase"):
                test_name = test_case.attrib["name"]
                failures = []
                failure_elements = test_case.findall("failure")
                for failure_elem in failure_elements:
                    failures.append(failure_elem.text or "")
                skippeds = []
                if test_case.attrib.get("result", None) == "skipped":
                    # In gtest 1.11 a skipped message was added to
                    # the output file
                    skipped_elements = test_case.findall("skipped")
                    for skipped_elem in skipped_elements:
                        skippeds.append(skipped_elem.text or "")
                    # In gtest 1.10 the skipped message is not dump,
                    # so if no skipped message was found just
                    # append a "skipped" keyword
                    if not skipped_elements:
                        skippeds.append("Skipped")
                elif test_case.attrib.get("status", None) == "notrun":
                    skippeds.append("Disabled")
                result.append((test_suite_name + "." + test_name, failures, skippeds))

        return result


class GoogleTestFailure(CppTestFailure):
    def __init__(self, contents: str) -> None:
        self.lines = contents.splitlines()
        self.filename = "unknown file"
        self.linenum = 0
        if self.lines:
            fields = self.lines[0].rsplit(":", 1)
            if len(fields) == 2:
                try:
                    linenum = int(fields[1])
                except ValueError:
                    return
                self.filename = fields[0]
                self.linenum = linenum
                self.lines.pop(0)

    def get_lines(self) -> list[tuple[str, Markup]]:
        m = ("red", "bold")
        return [(x, m) for x in self.lines]

    def get_file_reference(self) -> tuple[str, int]:
        return self.filename, self.linenum
