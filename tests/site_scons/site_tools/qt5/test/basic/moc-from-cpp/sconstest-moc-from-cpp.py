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

"""
Create a moc file from a cpp file.
"""

import TestSCons

test = TestSCons.TestSCons()
test.dir_fixture('image')
test.file_fixture('../../qtenv.py')
test.file_fixture('../../../__init__.py','site_scons/site_tools/qt5/__init__.py')

lib_aaa = 'aaa_lib' # Alias for the Library
moc = 'aaa.moc'

test.run(arguments=lib_aaa,
         stderr=TestSCons.noisy_ar,
         match=TestSCons.match_re_dotall)

test.up_to_date(options = '-n', arguments = lib_aaa)

test.write('aaa.cpp', r"""
#include "aaa.h"

#include <QObject>

class aaa : public QObject
{
  Q_OBJECT

public:
  aaa() {};
};

#include "%s"

// Using the class
void dummy_a()
{
  aaa a;
}
""" % moc)

test.not_up_to_date(options = '-n', arguments = moc)

test.run(options = '-c', arguments = lib_aaa)

test.run(arguments = "variant_dir=1 " + lib_aaa,
         stderr=TestSCons.noisy_ar,
         match=TestSCons.match_re_dotall)

test.run(arguments = "variant_dir=1 chdir=1 " + lib_aaa)

test.must_exist(test.workpath('build', moc))

test.run(arguments = "variant_dir=1 dup=0 " + lib_aaa,
         stderr=TestSCons.noisy_ar,
         match=TestSCons.match_re_dotall)

test.must_exist(test.workpath('build_dup0', moc))

test.pass_test()

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
