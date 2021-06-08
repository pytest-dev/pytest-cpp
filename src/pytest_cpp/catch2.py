import os
import subprocess
import tempfile
from xml.etree import ElementTree

import pytest

from pytest_cpp.error import CppTestFailure


class Catch2Facade(object):
    """
    Facade for Catch2.
    """

    @classmethod
    def is_test_suite(cls, executable):
        try:
            output = subprocess.check_output(
                [executable, "--help"],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except (subprocess.CalledProcessError, OSError):
            return False
        else:
            return "--list-test-names-only" in output

    def list_tests(self, executable):
        """
        Executes test with "--list-test-names-only" and gets list of tests
        parsing output like this:

        1: All test cases reside in other .cpp files (empty)
        2: Factorial of 0 is 1 (fail)
        2: Factorials of 1 and higher are computed (pass)
        """
        # This will return an exit code with the number of tests available
        try:
            output = subprocess.check_output(
                [executable, "--list-test-names-only"],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as e:
            output = e.output

        result = output.strip().split("\n")

        return result

    def run_test(self, executable, test_id="", test_args=(), harness=None):
        harness = harness or []
        xml_filename = self._get_temp_xml_filename()
        args = harness + [
            executable,
            test_id,
            "--success",
            "--reporter=xml",
            "--out %s" % xml_filename,
        ]
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
        os.remove(xml_filename)
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

        msg = "Internal Error: could not find test " "{test_id} in results:\n{results}"

        results_list = "\n".join("\n".join(x) for (n, x, f) in results)
        failure = Catch2Failure(msg.format(test_id=test_id, results=results_list))
        return [failure], output

    def _get_temp_xml_filename(self):
        return tempfile.mktemp()

    def _parse_xml(self, xml_filename):
        root = ElementTree.parse(xml_filename)
        result = []
        for test_suite in root.findall("Group"):
            test_suite_name = test_suite.attrib["name"]
            for test_case in test_suite.findall("TestCase"):
                test_name = test_case.attrib["name"]
                test_result = test_case.find("OverallResult")
                failures = []
                if test_result.attrib["success"] == "false":
                    test_checks = test_case.findall("Expression")
                    for check in test_checks:
                        file_name = check.attrib["filename"]
                        line_num = check.attrib["line"]
                        if check.attrib["success"] == "false":
                            expected = check.find("Original").text
                            actual = check.find("Expanded").text
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
    def __init__(self, filename, linenum, lines):
        self.lines = lines.splitlines()
        self.filename = filename
        self.linenum = int(linenum)

    def get_lines(self):
        m = ("red", "bold")
        return [(x, m) for x in self.lines]

    def get_file_reference(self):
        return self.filename, self.linenum
