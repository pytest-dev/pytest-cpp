import os
import subprocess
import tempfile
import io
import shutil
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
            return '-datatags' in output

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
            "{xml_file},xml".format(xml_file=log_xml),
        ]
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, _ = p.communicate()

        num_reports = len(os.listdir(temp_dir))
        if num_reports > 1:
            self.merge_xml_report(temp_dir)
            log_xml = os.path.join(temp_dir, "result-merged.xml")
            log = read_file(log_xml)
        elif num_reports == 1:
            log_xml = os.path.join(temp_dir, os.listdir(temp_dir)[0])
            log = read_file(log_xml)
        else:
            log_xml = log = None

        if p.returncode < 0 and p.returncode not in(-6, ):
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

    def merge_xml_report(self, temp_dir):
        matches = []
        for root, dirnames, filenames in os.walk(temp_dir):
            for filename in filenames:
                if filename.endswith('.xml'):
                    matches.append(os.path.join(root, filename))

        cases = []
        suites = []

        for file_name in matches:
            tree = ET.parse(file_name)
            test_suite = tree.getroot()
            cases.append(test_suite.getchildren())
            suites.append(test_suite)

        new_root = ET.Element('testsuites')

        for suite in suites:
            new_root.append(suite)

        new_tree = ET.ElementTree(new_root)
        new_tree.write(os.path.join(temp_dir, "result-merged.xml"),
                       encoding="UTF-8",
                       xml_declaration=True)

    def _parse_log(self, log):
        failed_suites = []
        tree = ET.parse(log)
        root = tree.getroot()
        if log:
            for suite in root:
                failed_cases = [case for case in root.iter('Incident') if case.get('type') != "pass"]
                if failed_cases:
                    failed_suites = []
                    for case in failed_cases:
                        failed_suites.append(QTestFailure(case.attrib['file'], int(case.attrib['line']), case.find('Description').text))
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
