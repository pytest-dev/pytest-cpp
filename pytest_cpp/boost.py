import os
import subprocess
import tempfile
from xml.etree import ElementTree
import io
import shutil
from pytest_cpp.error import CppTestFailure


class BoostTestFacade(object):
    """
    Facade for BoostTests.
    """

    @classmethod
    def is_test_suite(cls, executable):
        try:
            output = subprocess.check_output([executable, '--help'],
                                             stderr=subprocess.STDOUT,
                                             universal_newlines=True)
        except (subprocess.CalledProcessError, OSError):
            return False
        else:
            return '--output_format' in output and 'log_format' in output

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
        report_xml = os.path.join(temp_dir, 'report.xml')
        args = [
            executable,
            '--output_format=xml',
            '--log_sink=%s' % log_xml,
            '--report_sink=%s' % report_xml,
        ]
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, _ = p.communicate()

        log = read_file(log_xml)
        report = read_file(report_xml)

        if p.returncode not in (0, 200, 201):
            msg = ('Internal Error: calling {executable} '
                   'for test {test_id} failed (returncode={returncode}):\n'
                   'output:{stdout}\n'
                   'log:{log}\n'
                   'report:{report}')
            failure = BoostTestFailure(
                '<no source file>',
                linenum=0,
                contents=msg.format(executable=executable,
                                    test_id=test_id,
                                    stdout=stdout,
                                    log=log,
                                    report=report,
                                    returncode=p.returncode))
            return [failure]

        results = self._parse_log(log=log)
        shutil.rmtree(temp_dir)
        if results:
            return results

    def _parse_log(self, log):
        """
        Parse the "log" section produced by BoostTest.

        This is always a XML file, and from this we produce most of the
        failures possible when running BoostTest.
        """
        # Fatal errors apparently generate invalid xml in the form:
        # <FatalError>...</FatalError><TestLog>...</TestLog>
        # so we have to manually split it into two xmls if that's the case.
        parsed_elements = []
        if log.startswith('<FatalError'):
            fatal, log = log.split('</FatalError>')
            fatal += '</FatalError>'  # put it back, removed by split()
            fatal_root = ElementTree.fromstring(fatal)
            fatal_root.text = 'Fatal Error: %s' % fatal_root.text
            parsed_elements.append(fatal_root)

        log_root = ElementTree.fromstring(log)
        parsed_elements.extend(log_root.findall('Exception'))
        parsed_elements.extend(log_root.findall('Error'))

        result = []
        for elem in parsed_elements:
            filename = elem.attrib['file']
            linenum = int(elem.attrib['line'])
            result.append(BoostTestFailure(filename, linenum, elem.text))
        return result


class BoostTestFailure(CppTestFailure):
    def __init__(self, filename, linenum, contents):
        self.filename = filename
        self.linenum = linenum
        self.lines = contents.splitlines()

    def get_lines(self):
        m = ('red', 'bold')
        return [(x, m) for x in self.lines]

    def get_file_reference(self):
        return self.filename, self.linenum
