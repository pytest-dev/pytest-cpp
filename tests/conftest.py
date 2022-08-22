import os
import shutil
import sys

import pytest

pytest_plugins = "pytester"


@pytest.fixture
def exes(testdir, request):
    """
    Returns a fixture that can be used to obtain the executables found
    in the same directory as the test requesting it. The executables
    are copied first to testdir's tmpdir location to ensure tests don't
    interfere with each other.
    """

    class Executables:
        def get(self, name, new_name=None):
            if not new_name:
                new_name = os.path.basename(name)
            source = os.path.join(request.node.fspath.dirname, self.exe_name(name))
            dest = testdir.tmpdir.join(self.exe_name(new_name))
            shutil.copy(str(source), str(dest))
            return str(dest)

        def exe_name(self, name):
            if sys.platform.startswith("win"):
                name += ".exe"
            return name

    return Executables()
