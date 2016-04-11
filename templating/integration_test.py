# Copyright 2016 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""End-to-end test of the template engine."""

from collections import namedtuple, OrderedDict
import templating.main as main
import os
import tempfile
import unittest

class IntegrationTest(unittest.TestCase):

  def setUp(self):
    self._tmpDir = os.getenv('TEST_TMPDIR')
    os.chdir(self._tmpDir)
    self._tmpFiles = []

  def tearDown(self):
    for f in self._tmpFiles:
      os.remove(f)
    self._tmpFiles = []

  def _get_tmp(self):
    tmp = tempfile.mkstemp(dir=self._tmpDir)
    os.close(tmp[0])
    self._tmpFiles.append(tmp[1])
    return tmp[1]

  def assert_template(self, expected, template, variables={},
                      imports={}, escape_xml=True, executable=False):
    tempfile = self._get_tmp()
    outfile = self._get_tmp()
    with open(tempfile, 'w') as f:
      f.write(template)
    imp = []
    for v in imports:
      fn = self._get_tmp()
      imp.append((v[0], fn))
      with open(fn, 'w') as f:
        f.write(v[1])
    MyStruct = namedtuple(
        'MyStruct',
        'template output variable imports escape_xml executable')
    main.main(MyStruct(
        template=tempfile,
        output=outfile,
        escape_xml=escape_xml,
        executable=executable,
        variable=['%s=%s' % (k, v) for k, v in variables.iteritems()],
        imports=['%s=%s' % v for v in imp],
    ), None)
    with open(outfile, 'r') as f:
      self.assertEquals(expected, f.read())

  def test_no_substitution(self):
    self.assert_template('toto', 'toto')

  def test_one_substitution(self):
    self.assert_template('toto', '{{ variables.toto }}',
                        variables={'toto': 'toto'})

  def test_one_import(self):
    self.assert_template('toto', '{{ imports.toto }}', 
                         imports=[('toto', 'toto')])

  def test_cascaded_imports(self):
    self.assert_template(
        'd',
        '{{ imports.a }}',
        imports=[
            ('c', 'd'),
            ('b', '{{ imports.c }}'),
            ('a', '{{ imports.b }}'),
        ])

  def test_escape_xml(self):
    self.assert_template('&amp;', '{{ variables.a }}',
                         variables={'a': '&'})
    self.assert_template('&amp;', '{{ imports.a }}',
                         imports=[('a', '&')])
    self.assert_template('&amp;', '{{ imports.b }}',
                         imports=[('a', '&'), ('b', '{{ imports.a }}')])
    self.assert_template('&', '{{ variables.a }}', escape_xml=False,
                         variables={'a': '&'})
    self.assert_template('&', '{{ imports.a }}', escape_xml=False,
                         imports=[('a', '&')])
    self.assert_template('&', '{{ imports.b }}', escape_xml=False,
                         imports=[('a', '&'), ('b', '{{ imports.a }}')])

if __name__ == '__main__':
  unittest.main()
