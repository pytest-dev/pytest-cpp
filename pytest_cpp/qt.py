import os
import subprocess
import tempfile
import io
import shutil
import copy
import fnmatch
from pytest_cpp.error import CppTestFailure
import xml.etree.ElementTree as ET


class QTestLibFacade(object):
    """
    Facade for QTestLib.
    """

    @classmethod
    def is_test_suite(cls, executable):
        try:
            output = subprocess.check_output([executable, '-help'],
                                             stderr=subprocess.STDOUT,
                                             universal_newlines=True)
        except (subprocess.CalledProcessError, OSError):
            return False
        else:
            return '-csv' in output

    def list_tests(self, executable):
        # unfortunately boost doesn't provide us with a way to list the tests
        # inside the executable, so the test_id is a dummy placeholder :(
        return [os.path.basename(os.path.splitext(executable)[0])]

    def run_test(self, executable, test_id):
        def read_file(name):
            try:
                with io.open(name) as f:
                    return f.read()
            except IOError:
                return None

        temp_dir = tempfile.mkdtemp()
        log_xml = os.path.join(temp_dir, 'log.xml')
        args = [
            executable,
            "-o",
            "{xml_file},xunitxml".format(xml_file=log_xml),
        ]
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, _ = p.communicate()

        matches = []
        for root, dirnames, filenames in os.walk(temp_dir):
            for filename in filenames:
                if filename.endswith('.xml'):
                    matches.append(os.path.join(root, filename))
        failures = 0
        tests = 0
        errors = 0
        cases = []
        suites = []

        for file_name in matches:
            tree = ET.parse(file_name)
            test_suite = tree.getroot()
            failures += int(test_suite.attrib['failures'])
            tests += int(test_suite.attrib['tests'])
            errors += int(test_suite.attrib['errors'])
            cases.append(test_suite.getchildren())
            suites.append(test_suite)

        new_root = ET.Element('testsuites')
        new_root.attrib['failures'] = '%s' % failures
        new_root.attrib['tests'] = '%s' % tests
        new_root.attrib['errors'] = '%s' % errors

        for suite in suites:
            new_root.append(suite)

        new_tree = ET.ElementTree(new_root)
        new_tree.write(os.path.join(temp_dir, "result-merged.xml"),
                       encoding="UTF-8",
                       xml_declaration=True)

        log_xml = os.path.join(temp_dir, "result-merged.xml")

        log = read_file(log_xml)

        if p.returncode not in (0, 1):
            msg = ('Internal Error: calling {executable} '
                   'for test {test_id} failed (returncode={returncode}):\n'
                   'output:{stdout}\n'
                   'log:{log}\n')
            failure = QTestFailure(
                '<no source file>',
                linenum=0,
                contents=msg.format(executable=executable,
                                    test_id=test_id,
                                    stdout=stdout,
                                    log=log,
                                    returncode=p.returncode))
            return [failure]

        results = self._parse_log(log=log_xml)
        shutil.rmtree(temp_dir)

        if results:
            return results

    def _parse_log(self, log):
        failed_suites = []
        tree = ET.parse(log)
        root = tree.getroot()
        if log:
            for suite in root:
                if int(root.attrib['errors']) > 0 or int(root.attrib['failures']) > 0:
                    failed_cases = [case for case in root.iter('testcase') if case.get('result') != "pass"]
                    updated_attrib = copy.deepcopy(suite.attrib)
                    updated_attrib.update(tests=len(failed_cases))
                    fail_suite = ET.Element(suite.tag, attrib=updated_attrib)
                    fail_suite.extend(failed_cases)
                    failed_suites.append(fail_suite)
        return failed_suites


class QTestFailure(CppTestFailure):
    def __init__(self, filename, linenum, contents):
        self.filename = filename
        self.linenum = linenum
        self.lines = contents.splitlines()

    def get_lines(self):
        m = ('red', 'bold')
        return [(x, m) for x in self.lines]

    def get_file_reference(self):
        return self.filename, self.linenum
