#
# Copyright (c) 2001-2010 The SCons Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#


import os, sys, glob
from SCons import Environment

def findQtBinParentPath(qtpath):
    """ Within the given 'qtpath', search for a bin directory
        containing the 'lupdate' executable and return
        its parent path.
    """
    for path, dirs, files in os.walk(qtpath):
        for d in dirs:
            if d == 'bin':
                if sys.platform.startswith("linux"):
                    lpath = os.path.join(path, d, 'lupdate')
                else:
                    lpath = os.path.join(path, d, 'lupdate.exe')
                if os.path.isfile(lpath):
                    return path
                
    return ""

def findMostRecentQtPath(dpath):
    paths = glob.glob(dpath)
    if len(paths):
        paths.sort()
        return findQtBinParentPath(paths[-1])
        
    return ""

def detectLatestQtVersion():
    if sys.platform.startswith("linux"):
        # Inspect '/usr/local/Qt' first...
        p = findMostRecentQtPath('/usr/local/Qt-*')
        if not p:
            # ... then inspect '/usr/local/Trolltech'...
            p = findMostRecentQtPath('/usr/local/Trolltech/*')
        if not p:
            # ...then try to find a binary install...
            p = findMostRecentQtPath('/opt/Qt*')
        if not p:
            # ...then try to find a binary SDK.
            p = findMostRecentQtPath('/opt/qtsdk*')
            
    else:
        # Simple check for Windows: inspect only 'C:\Qt'
        paths = glob.glob(os.path.join('C:\\', 'Qt', 'Qt*'))
        p = ""
        if len(paths):
            paths.sort()
            # Select version with highest release number
            paths = glob.glob(os.path.join(paths[-1], '5*'))
            if len(paths):
                paths.sort()
                # Is it a MinGW or VS installation?
                p = findMostRecentQtPath(os.path.join(paths[-1], 'mingw*'))
                if not p:
                    # No MinGW, so try VS...
                    p = findMostRecentQtPath(os.path.join(paths[-1], 'msvc*'))
        
    return os.environ.get("QT5DIR", p)

def detectPkgconfigPath(qtdir):
    pkgpath = os.path.join(qtdir, 'lib', 'pkgconfig')
    if os.path.exists(os.path.join(pkgpath,'Qt5Core.pc')):
        return pkgpath
    pkgpath = os.path.join(qtdir, 'lib')
    if os.path.exists(os.path.join(pkgpath,'Qt5Core.pc')):
        return pkgpath

    return ""
    
def createQtEnvironment(qtdir=None, env=None):
    if not env:
        env = Environment.Environment(tools=['default'])
    if not qtdir:
        qtdir = detectLatestQtVersion()
    env['QT5DIR'] = qtdir
    if sys.platform.startswith("linux"):
        env['ENV']['PKG_CONFIG_PATH'] = detectPkgconfigPath(qtdir)
    env.Tool('qt5')
    env.Append(CXXFLAGS=['-fPIC'])

    return env

