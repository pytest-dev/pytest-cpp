from __future__ import annotations

import io
import os
import subprocess
import tempfile
from typing import Sequence
from xml.etree import ElementTree

from pytest_cpp.error import CppTestFailure
from pytest_cpp.error import Markup
from pytest_cpp.facade_abc import AbstractFacade
from pytest_cpp.helpers import make_cmdline


class BoostTestFacade(AbstractFacade):
    """
    Facade for BoostTests.
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
            return "--output_format" in output and "log_format" in output

    def list_tests(
        self,
        executable: str,
        harness_collect: Sequence[str] = (),
    ) -> list[str]:
        del harness_collect
        # unfortunately boost doesn't provide us with a way to list the tests
        # inside the executable, so the test_id is a dummy placeholder :(
        return [os.path.basename(os.path.splitext(executable)[0])]

    def run_test(
        self,
        executable: str,
        test_id: str,
        test_args: Sequence[str] = (),
        harness: Sequence[str] = (),
    ) -> tuple[Sequence[BoostTestFailure] | None, str]:
        def read_file(name: str) -> str:
            try:
                with io.open(name) as f:
                    return f.read()
            except IOError:
                return ""

        with tempfile.TemporaryDirectory(prefix="pytest-cpp") as temp_dir:
            # On Windows, ValueError is raised when path and start are on different drives.
            # In this case failing back to the absolute path.
            try:
                log_xml = os.path.join(os.path.relpath(temp_dir), "log.xml")
                report_xml = os.path.join(os.path.relpath(temp_dir), "report.xml")
            except ValueError:
                log_xml = os.path.join(temp_dir, "log.xml")
                report_xml = os.path.join(temp_dir, "report.xml")
            args = list(
                make_cmdline(
                    harness,
                    executable,
                    [
                        "--output_format=XML",
                        f"--log_sink={log_xml}",
                        f"--report_sink={report_xml}",
                    ],
                )
            )
            args.extend(test_args)

            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            raw_stdout, _ = p.communicate()
            stdout = raw_stdout.decode("utf-8") if raw_stdout else ""

            log = read_file(log_xml)
            report = read_file(report_xml)

        if p.returncode not in (0, 200, 201):
            msg = (
                "Internal Error: calling {executable} "
                "for test {test_id} failed (returncode={returncode}):\n"
                "output:{stdout}\n"
                "log:{log}\n"
                "report:{report}"
            )
            failure = BoostTestFailure(
                "<no source file>",
                linenum=0,
                contents=msg.format(
                    executable=executable,
                    test_id=test_id,
                    stdout=stdout,
                    log=log,
                    report=report,
                    returncode=p.returncode,
                ),
            )
            return [failure], stdout

        results = self._parse_log(log=log)

        if results:
            return results, stdout

        return None, stdout

    def _parse_log(self, log: str) -> list[BoostTestFailure]:
        """
        Parse the "log" section produced by BoostTest.

        This is always a XML file, and from this we produce most of the
        failures possible when running BoostTest.
        """
        # Boosttest will sometimes generate unparseable XML
        # so we surround it with xml tags.
        parsed_elements = []
        log = "<xml>{}</xml>".format(log)

        log_root = ElementTree.fromstring(log)
        testlog = log_root.find("TestLog")

        parsed_elements.extend(log_root.findall("Exception"))
        parsed_elements.extend(log_root.findall("Error"))
        parsed_elements.extend(log_root.findall("FatalError"))

        if testlog is not None:
            parsed_elements.extend(testlog.findall("Exception"))
            parsed_elements.extend(testlog.findall("Error"))
            parsed_elements.extend(testlog.findall("FatalError"))

        result = []
        for elem in parsed_elements:
            filename = elem.attrib["file"]
            linenum = int(elem.attrib["line"])
            result.append(BoostTestFailure(filename, linenum, elem.text or ""))
        return result


class BoostTestFailure(CppTestFailure):
    def __init__(self, filename: str, linenum: int, contents: str) -> None:
        self.filename = filename
        self.linenum = linenum
        self.lines = contents.splitlines()

    def get_lines(self) -> list[tuple[str, Markup]]:
        m = ("red", "bold")
        return [(x, m) for x in self.lines]

    def get_file_reference(self) -> tuple[str, int]:
        return self.filename, self.linenum
