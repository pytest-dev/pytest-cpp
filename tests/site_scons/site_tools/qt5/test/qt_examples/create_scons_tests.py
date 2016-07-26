#!/usr/bin/env python
#
# Copyright (c) 2001-2010,2011,2012 The SCons Foundation
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
#
# create_scons_test.py
#
# Populates a Qt "examples" directory with files for the
# SCons test framework.
#
#
#
# Usage:
#
# Step 1: Copy the "examples" folder of your Qt source tree into
#         this directory.
# Step 2: Run "python create_scons_tests.py" to create all files
#         for the SCons test framework.
# Step 3: Execute "python runtest.py -a" to run all tests
#
# Additional options for this script are:
#
#   -local               Creates the test files in the local directory,
#                        also copies qtenv.py and qt5.py to their correct
#                        places.
#   -clean               Removes all intermediate test files.
#
#

import os, sys, re, glob, shutil

# cxx file extensions
cxx_ext = ['.c', '.cpp', '.cxx', '.cc']
# header file extensions
h_ext = ['.h', '.hpp', '.hxx']
# regex for includes
inc_re = re.compile(r'#include\s+<([^>]+)>')
# regex for qtLibraryTarget function
qtlib_re = re.compile(r'\$\$qtLibraryTarget\(([^\)]+)\)')
qrcinit_re = re.compile('Q_INIT_RESOURCE\(([^\)]+)\)')
localvar_re = re.compile("\\$\\$([^/\s]+)")
qthave_re = re.compile("qtHaveModule\([^\)]+\)\s*:\s")

updir = '..'+os.sep

# we currently skip all .pro files that use these config values
complicated_configs = ['qdbus','phonon','plugin']
# for the following CONFIG values we have to provide default qt modules
config_modules = {'designer' : ['QtCore','QtGui','QtXml','QtWidgets','QtDesigner','QtDesignerComponents'],
                  'uitools' : ['QtCore','QtGui','QtUiTools'],
                  'assistant' : ['QtCore','QtGui','QtXml','QtScript','QtAssistant'],
                  'core' : ['QtCore'],
                  'gui' : ['QtCore', 'QtGui'],
                  'concurrent' : ['QtCore', 'QtConcurrent'],
                  'dbus' : ['QtCore', 'QtDBus'],
                  'declarative' : ['QtCore', 'QtGui', 'QtScript', 'QtSql', 'QtNetwork', 'QtWidgets', 'QtXmlPatterns', 'QtDeclarative'],
                  'printsupport' : ['QtCore', 'QtGui', 'QtWidgets', 'QtPrintSupport'],
                  'mediawidgets' : ['QtCore', 'QtGui', 'QtOpenGL', 'QtNetwork', 'QtWidgets', 'QtMultimedia', 'QtMultimediaWidgets'],
                  'webkitwidgets' : ['QtCore', 'QtGui', 'QtOpenGL', 'QtNetwork', 'QtWidgets', 'QtPrintSupport', 'QtWebKit', 'QtQuick', 'QtQml', 'QtSql', 'QtV8', 'QtWebKitWidgets'],
                  'qml' : ['QtCore', 'QtGui', 'QtNetwork', 'QtV8', 'QtQml'],
                  'quick' : ['QtCore', 'QtGui', 'QtNetwork', 'QtV8', 'QtQml', 'QtQuick'],
                  'axcontainer' : [],
                  'axserver' : [],
                  'testlib' : ['QtCore', 'QtTest'],
                  'xmlpatterns' : ['QtCore', 'QtNetwork', 'QtXmlPatterns'],
                  'qt' : ['QtCore','QtGui'],
                  'xml' : ['QtCore','QtGui','QtXml'],
                  'webkit' : ['QtCore','QtGui','QtQuick','QtQml','QtNetwork','QtSql','QtV8','QtWebKit'],
                  'network' : ['QtCore','QtNetwork'],
                  'svg' : ['QtCore','QtGui','QtWidgets','QtSvg'],
                  'script' : ['QtCore','QtScript'],
                  'scripttools' : ['QtCore','QtGui','QtWidgets','QtScript','QtScriptTools'],
                  'multimedia' : ['QtCore','QtGui','QtNetwork','QtMultimedia'],
                  'script' : ['QtCore','QtScript'],
                  'help' : ['QtCore','QtGui','QtWidgets','QtCLucene','QtSql','QtNetwork','QtHelp'],
                  'qtestlib' : ['QtCore','QtTest'],
                  'opengl' : ['QtCore','QtGui','QtOpenGL'],
                  'widgets' : ['QtCore','QtGui','QtWidgets']
                  }
# for the following CONFIG values we have to provide additional CPP defines
config_defines = {'plugin' : ['QT_PLUGIN'],
                  'designer' : ['QDESIGNER_EXPORT_WIDGETS']
                 }

# dictionary of special Qt Environment settings for all single tests/pro files
qtenv_flags = {'QT5_GOBBLECOMMENTS' : '1'
              }

# available qt modules
validModules = [
    # Qt Essentials
    'QtCore',
    'QtGui',
    'QtMultimedia',
    'QtMultimediaQuick_p',
    'QtMultimediaWidgets',
    'QtNetwork',
    'QtPlatformSupport',
    'QtQml',
    'QtQmlDevTools',
    'QtQuick',
    'QtQuickParticles',
    'QtSql',
    'QtQuickTest',
    'QtTest',
    'QtWebKit',
    'QtWebKitWidgets',
    'QtWidgets',
    # Qt Add-Ons
    'QtConcurrent',
    'QtDBus',
    'QtOpenGL',
    'QtPrintSupport',
    'QtDeclarative',
    'QtScript',
    'QtScriptTools',
    'QtSvg',
    'QtUiTools',
    'QtXml',
    'QtXmlPatterns',
    # Qt Tools
    'QtHelp',
    'QtDesigner',
    'QtDesignerComponents',
    # Other
    'QtCLucene',
    'QtConcurrent',
    'QtV8'
    ]

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
        p = findMostRecentQtPath(os.path.join('/usr','local','Qt-*'))
        if not p:
            # ... then inspect '/usr/local/Trolltech'...
            p = findMostRecentQtPath(os.path.join('/usr','local','Trolltech','*'))
        if not p:
            # ...then try to find a binary install...
            p = findMostRecentQtPath(os.path.join('/opt','Qt*'))
        if not p:
            # ...then try to find a binary SDK.
            p = findMostRecentQtPath(os.path.join('/opt','qtsdk*'))
            
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

def expandProFile(fpath):
    """ Read the given file into a list of single lines,
        while expanding included files (mainly *.pri)
        recursively.
    """
    lines = []
    f = open(fpath,'r')
    content = f.readlines()
    f.close()
    pwdhead, tail = os.path.split(fpath)
    head = pwdhead
    if pwdhead:
        pwdhead = os.path.abspath(pwdhead)
    else:
        pwdhead = os.path.abspath(os.getcwd())
    for idx, l in enumerate(content):
        l = l.rstrip('\n')
        l = l.rstrip()
        if '$$PWD' in l:
            l = l.replace("$$PWD", pwdhead)
        if l.startswith('include('):
            # Expand include file
            l = l.rstrip(')')
            l = l.replace('include(','')
            while '$$' in l:
                # Try to replace the used local variable by
                # searching back in the content
                m = localvar_re.search(l)
                if m:
                    key = m.group(1)
                    tidx = idx-1
                    skey = "%s = " % key
                    while tidx >= 0:
                        if content[tidx].startswith(skey):
                            # Key found
                            l = l.replace('$$%s' % key, content[tidx][len(skey):].rstrip('\n'))
                            if os.path.join('..','..','qtbase','examples') in l:
                                # Quick hack to cope with erroneous *.pro files
                                l = l.replace(os.path.join('..','..','qtbase','examples'), os.path.join('..','examples'))
                            break
                        tidx -= 1
                    if tidx < 0:
                        print "Error: variable %s could not be found during parsing!" % key
                        break
            ipath = l
            if head:
                ipath = os.path.join(head, l)
            # Does the file exist?
            if not os.path.isfile(ipath):
                # Then search for it the hard way
                ihead, tail = os.path.split(ipath)
                for spath, dirs, files in os.walk('.'):
                    for f in files:
                        if f == tail:
                            ipath = os.path.join(spath, f)
            lines.extend(expandProFile(ipath))
        else:
            lines.append(l)
            
    return lines

def parseProFile(fpath):
    """ Parse the .pro file fpath and return the defined
    variables in a dictionary.
    """
    keys = {}
    curkey = None
    curlist = []
    for l in expandProFile(fpath):
        # Strip off qtHaveModule part
        m = qthave_re.search(l)
        if m:
            l = qthave_re.sub("", l)
        kl = l.split('=')
        if len(kl) > 1:
            # Close old key
            if curkey:
                if keys.has_key(curkey):
                    keys[curkey].extend(curlist)
                else:
                    keys[curkey] = curlist
                
            # Split off trailing +
            nkey = kl[0].rstrip('+')
            nkey = nkey.rstrip()
            # Split off optional leading part with "contains():"
            cl = nkey.split(':')
            if ('lesock' not in l) and ((len(cl) < 2) or ('msvc' in cl[0])):
                nkey = cl[-1]
                # Open new key
                curkey = nkey.split()[0]
                value = kl[1].lstrip()
                if value.endswith('\\'):
                    # Key is continued on next line
                    value = value[:-1]
                    curlist = value.split()
                else:
                    # Single line key
                    if keys.has_key(curkey):
                        keys[curkey].extend(value.split())
                    else:
                        keys[curkey] = value.split()
                    curkey = None
                    curlist = []
        else:
            if l.endswith('\\'):
                # Continue current key
                curlist.extend(l[:-1].split())
            else:
                # Unknown, so go back to VOID state
                if curkey:
                    # Append last item for current key...
                    curlist.extend(l.split())
                    if keys.has_key(curkey):
                        keys[curkey].extend(curlist)
                    else:
                        keys[curkey] = curlist
                        
                    # ... and reset parse state.
                    curkey = None
                    curlist = []
    
    return keys

def writeSConstruct(dirpath):
    """ Create a SConstruct file in dirpath.
    """
    sc = open(os.path.join(dirpath,'SConstruct'),'w')
    sc.write("""import qtenv

qtEnv = qtenv.createQtEnvironment()
Export('qtEnv')
SConscript('SConscript')
    """)
    sc.close()

def collectModulesFromFiles(fpath):
    """ Scan source files in dirpath for included
    Qt5 modules, and return the used modules in a list.
    """
    mods = []
    try:
        f = open(fpath,'r')
        content = f.read()
        f.close()
    except:
        return mods
    
    for m in inc_re.finditer(content):
        mod = m.group(1)
        if (mod in validModules) and (mod not in mods):
            mods.append(mod)
    return mods

def findQResourceName(fpath):
    """ Scan the source file fpath and return the name
        of the QRC instance that gets initialized via
        QRC_INIT_RESOURCE.
    """
    name = ""
    
    try:
        f = open(fpath,'r')
        content = f.read()
        f.close()
    except:
        return name
    
    m = qrcinit_re.search(content)
    if m:
        name = m.group(1)
    
    return name

def validKey(key, pkeys):
    """ Helper function
    """
    if pkeys.has_key(key) and len(pkeys[key]) > 0:
        return True
    
    return False

def collectModules(dirpath, pkeys):
    """ Scan source files in dirpath for included
    Qt5 modules, and return the used modules in a list.
    """
    mods = []
    defines = []
    # Scan subdirs
    if validKey('SUBDIRS', pkeys):
        for s in pkeys['SUBDIRS']:
            flist = glob.glob(os.path.join(dirpath, s, '*.*'))
            for f in flist:
                root, ext = os.path.splitext(f)
                if (ext and ((ext in cxx_ext) or
                             (ext in h_ext))):
                    mods.extend(collectModulesFromFiles(f))
                    
    # Scan sources
    if validKey('SOURCES', pkeys):
        for s in pkeys['SOURCES']:
            f = os.path.join(dirpath,s)
            mods.extend(collectModulesFromFiles(f))
    
    # Scan headers
    if validKey('HEADERS', pkeys):
        for s in pkeys['HEADERS']:
            f = os.path.join(dirpath,s)
            mods.extend(collectModulesFromFiles(f))
            
    # Check CONFIG keyword
    if validKey('CONFIG', pkeys):
        for k in pkeys['CONFIG']:
            if config_modules.has_key(k):
                mods.extend(config_modules[k])
            if config_defines.has_key(k):
                defines.extend(config_defines[k])

    # Check QT keyword
    if validKey('QT', pkeys):
        for k in pkeys['QT']:
            if config_modules.has_key(k):
                mods.extend(config_modules[k])

    # Make lists unique
    unique_mods = []
    for m in mods:
        if m not in unique_mods:
            unique_mods.append(m)
    unique_defines = []
    for d in defines:
        if d not in unique_defines:
            unique_defines.append(d)

    # Safety hack, if no modules are found so far
    # assume that this is a normal Qt GUI application...
    if len(unique_mods) == 0:
        unique_mods = ['QtCore','QtGui']

    return (unique_mods, unique_defines)

def relOrAbsPath(dirpath, rpath):
    if rpath.startswith('..'):
        return os.path.abspath(os.path.normpath(os.path.join(dirpath, rpath)))

    return rpath

def writeSConscript(dirpath, profile, pkeys):
    """ Create a SConscript file in dirpath.
    """

    # Activate modules
    mods, defines = collectModules(dirpath, pkeys)
    if validKey('CONFIG', pkeys) and isComplicated(pkeys['CONFIG'][0]):
        return False
    
    qrcname = ""
    if not validKey('SOURCES', pkeys):
        # No SOURCES specified, try to find CPP files
        slist = glob.glob(os.path.join(dirpath,'*.cpp'))
        if len(slist) == 0:
            # Nothing to build here
            return False
        else:
            # Scan for Q_INIT_RESOURCE
            for s in slist:
                qrcname = findQResourceName(s)
                if qrcname:
                    break   
    
    allmods = True
    for m in mods:
        if m not in pkeys['qtmodules']:
            print "   no module %s" % m
            allmods = False
    if not allmods:
        return False

    sc = open(os.path.join(dirpath,'SConscript'),'w')
    sc.write("""Import('qtEnv')

env = qtEnv.Clone()
""")

    if len(mods):
        sc.write('env.EnableQt5Modules([\n')
        for m in mods[:-1]:
            sc.write("'%s',\n" % m)
        sc.write("'%s'\n" % mods[-1])
        sc.write('])\n\n')

    # Add CPPDEFINEs
    if len(defines):
        sc.write('env.AppendUnique(CPPDEFINES=[\n')
        for d in defines[:-1]:
            sc.write("'%s',\n" % d)
        sc.write("'%s'\n" % defines[-1])
        sc.write('])\n\n')
    
    # Add LIBS
    if validKey('LIBS', pkeys):
        sc.write('env.AppendUnique(LIBS=[\n')
        for d in pkeys['LIBS'][:-1]:
            sc.write("'%s',\n" % d)
        sc.write("'%s'\n" % pkeys['LIBS'][-1])
        sc.write('])\n\n')

    # Collect INCLUDEPATHs
    incpaths = []
    if validKey('INCLUDEPATH', pkeys):
        incpaths = pkeys['INCLUDEPATH']
    if validKey('FORMS', pkeys):
        for s in pkeys['FORMS']:
            head, tail = os.path.split(s)
            if head and head not in incpaths:
                incpaths.append(head)
    if incpaths:
        sc.write('env.Append(CPPPATH=[\n')
        for d in incpaths[:-1]:
            sc.write("'%s',\n" % relOrAbsPath(dirpath, d))
        sc.write("'%s'\n" % relOrAbsPath(dirpath, incpaths[-1]))
        sc.write('])\n\n')
  
    # Add special environment flags
    if len(qtenv_flags):
        for key, value in qtenv_flags.iteritems():    
            sc.write("env['%s']=%s\n" % (key, value))
    
    
    # Write source files
    if validKey('SOURCES', pkeys):
        sc.write('source_files = [\n')
        for s in pkeys['SOURCES'][:-1]:
            sc.write("'%s',\n" % relOrAbsPath(dirpath, s))
            if not qrcname:
                qrcname = findQResourceName(os.path.join(dirpath,s))

        sc.write("'%s'\n" % relOrAbsPath(dirpath, pkeys['SOURCES'][-1]))
        if not qrcname:
            qrcname = findQResourceName(os.path.join(dirpath,pkeys['SOURCES'][-1]))
        sc.write(']\n\n')
    
    # Write .ui files
    if validKey('FORMS', pkeys):
        sc.write('ui_files = [\n')
        for s in pkeys['FORMS'][:-1]:
            sc.write("'%s',\n" % relOrAbsPath(dirpath, s))
        sc.write("'%s'\n" % relOrAbsPath(dirpath, pkeys['FORMS'][-1]))
        sc.write(']\n')
        sc.write('env.Uic5(ui_files)\n\n')
    
    # Write .qrc files
    if validKey('RESOURCES', pkeys):
        qrc_name = pkeys['RESOURCES'][0]
        if qrcname:
            if qrc_name.endswith('.qrc'):
                qrc_name = qrc_name[:-4]
            sc.write("qrc_out = env.Qrc5('%s')\nsource_files.append(qrc_out)\nenv['QT5_QRCFLAGS'] = ['-name', '%s']\n" % (qrc_name, qrcname))
        else:
            if not qrc_name.endswith('.qrc'):
                qrc_name += '.qrc'
            sc.write("source_files.append('%s')\n" % qrc_name)
    
    # Select module
    type = 'Program'
    if validKey('TEMPLATE', pkeys):
        if pkeys['TEMPLATE'][0] == 'lib':
            type = 'StaticLibrary'
        if pkeys['TEMPLATE'][0] == 'dll':
            type = 'SharedLibrary'

    # TARGET may be wrapped by qtLibraryTarget function...    
    target = profile
    if validKey('TARGET', pkeys):
        t = pkeys['TARGET'][0]
        m = qtlib_re.search(t)
        if m:
            t = "Qt" + m.group(1)
        target = t.replace("$$TARGET", profile)
        
    # Create program/lib/dll
    else:
        if validKey('SOURCES', pkeys):    
            sc.write("env.%s('%s', source_files)\n\n" % (type, target))
        else:
            sc.write("env.%s('%s', Glob('*.cpp'))\n\n" % (type, target))
        
    sc.close()

    return True

def writeSConsTestFile(dirpath, folder):
    dirnums = dirpath.count(os.sep)+1
    f = open(os.path.join(dirpath, "sconstest-%s.py" % folder),'w')
    f.write("""
import os
import TestSCons

test = TestSCons.TestSCons()
test.dir_fixture("%s")
test.file_fixture('%sqtenv.py')
test.file_fixture('%s__init__.py', os.path.join('site_scons','site_tools','qt5','__init__.py'))
test.run()

test.pass_test()
    """ % (folder, updir*dirnums, updir*(dirnums+1)))
    f.close()

def installLocalFiles(dirpath):
    dirnums = dirpath.count(os.sep)+1
    shutil.copy(os.path.join(dirpath,updir*dirnums+'qtenv.py'),
                os.path.join(dirpath,'qtenv.py'))
    toolpath = os.path.join(dirpath,'site_scons','site_tools','qt5')
    if not os.path.exists(toolpath):
        os.makedirs(toolpath)
    shutil.copy(os.path.join(dirpath,updir*(dirnums+1)+'__init__.py'),
                os.path.join(dirpath,'site_scons','site_tools','qt5','__init__.py'))
    
def isComplicated(keyvalues):
    for s in keyvalues:
        if s in complicated_configs:
            return True
    
    return False

# Folders that should get skipped while creating the SConscripts
skip_folders = ['activeqt', 'declarative', 'dbus']

def createSConsTest(dirpath, profile, options):
    """ Create files for the SCons test framework in dirpath.
    """
    pkeys = parseProFile(os.path.join(dirpath, profile))
    if validKey('TEMPLATE', pkeys) and pkeys['TEMPLATE'][0] == 'subdirs':
        return
    if validKey('CONFIG', pkeys) and isComplicated(pkeys['CONFIG']):
        return
    if validKey('QT', pkeys) and isComplicated(pkeys['QT']):
        return

    head, tail = os.path.split(dirpath)
    if head and tail:
        print os.path.join(dirpath, profile)
        for s in skip_folders:
            if s in dirpath:
                return
        pkeys['qtmodules'] = options['qtmodules']
        if not writeSConscript(dirpath, profile[:-4], pkeys):
            return
        writeSConstruct(dirpath)
        writeSConsTestFile(head, tail)
        if options['local']:
            installLocalFiles(dirpath)

def cleanSConsTest(dirpath, profile, options):
    """ Remove files for the SCons test framework in dirpath.
    """
    try:
        os.remove(os.path.join(dirpath,'SConstruct'))
    except:
        pass
    try:
        os.remove(os.path.join(dirpath,'SConscript'))
    except:
        pass
    try:
        os.remove(os.path.join(dirpath,'qtenv.py'))
    except:
        pass
    try:
        shutil.rmtree(os.path.join(dirpath,'site_scons'),
                      ignore_errors=True)
    except:
        pass
    head, tail = os.path.split(dirpath)
    if head and tail:
        try:
            os.remove(os.path.join(head, "sconstest-%s.py" % tail))
        except:
            pass
        
def main():
    """ The main program.
    """

    # Parse command line options
    options = {'local' : False, # Install qtenv.py and qt5.py in local folder
               'qtpath' : None,
               'pkgconfig' : None
               }
    clean = False
    qtpath = None
    for o in sys.argv[1:]:
        if o == "-local":
            options['local'] = True
        elif o == "-clean":
            clean = True
        else:
            options['qtpath'] = o
    
    if not options['qtpath']:
        qtpath = detectLatestQtVersion()
        if qtpath == "":
            print "No Qt installation found!"
            sys.exit(1)

        is_win = sys.platform.startswith('win')
        if not is_win:
            # Use pkgconfig to detect the available modules
            options['pkgconfig'] = detectPkgconfigPath(qtpath)
            if options['pkgconfig'] == "":
                print "No pkgconfig files found!"
                sys.exit(1)

        options['qtpath'] = qtpath
        options['qtmodules'] = []
        for v in validModules:
            if is_win or os.path.exists(os.path.join(options['pkgconfig'],v.replace('Qt','Qt5')+'.pc')):
                options['qtmodules'].append(v)

    if not clean:
        doWork = createSConsTest
    else:
        doWork = cleanSConsTest
        
    # Detect .pro files
    for path, dirs, files in os.walk('.'):
        for f in files:
            if f.endswith('.pro'):
                doWork(path, f, options)

if __name__ == "__main__":
    main()
