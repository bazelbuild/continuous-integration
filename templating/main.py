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
"""A template engine based on jinja2 to use as a tool for Skylark rules."""

import gflags
import jinja2
import os
import os.path
import sys
import xml.sax.saxutils as saxutils

gflags.DEFINE_string('output', None, 'The output file, mandatory.')
gflags.MarkFlagAsRequired('output')

gflags.DEFINE_string('template', None, 'The input file, mandatory.')
gflags.MarkFlagAsRequired('template')

gflags.DEFINE_multistring(
    'variable', [],
    'A variable to expand in the template, in the format NAME=VALUE. Each '
    'variable provided here will be available via the variables.NAME '
    'variable.')

gflags.DEFINE_multistring(
    'imports', [],
    'A file to import as another template, in the format NAME=filename. '
    'Each file imported here will be considered as template and expanded '
    'as such. The order of expansion happens in the order it is given on '
    'the command line, making each file available for consumption for the '
    'next one. All file content will be available via the imports.NAME '
    'variable.')

gflags.DEFINE_boolean(
    'escape_xml', True,
    'Whether to escape XML special characters in the import templates. '
    'If set to True, all files specified through --imports and all values '
    'specified through --variable will be escaped for XML characters '
    'before inclusion in the main template.')

gflags.DEFINE_boolean(
    'executable', False, 'Whether to adds the executable bit to the output.')

FLAGS = gflags.FLAGS

class OneFileLoader(jinja2.BaseLoader):
  """A file system loader that allows loading only one file."""
  def __init__(self, path):
    self.path = path

  def get_source(self, environment, template):
    if template != self.path or not os.path.exists(self.path):
      raise TemplateNotFound(template)
    mtime = os.path.getmtime(self.path)
    source = ''
    with file(self.path) as f:
      source = f.read().decode('utf-8')
    return source, self.path, lambda: mtime == os.path.getmtime(self.path)


def expand_template(template, variables, imports):
  """Expand a template."""
  env = jinja2.Environment(loader=OneFileLoader(template))
  template = env.get_template(template)
  return template.render(imports=imports, variables=variables)

def quote_xml(d):
  """Returns a copy of d where all values where escaped for XML."""
  return {k: saxutils.escape(v) for k,v in d.iteritems()}

def construct_imports(variables, imports):
  """Construct the list of imports by expanding all command line arguments."""
  result = {}
  for i in imports:
    kv = i.split('=', 1)
    if len(kv) != 2:
      print 'Invalid value for --imports: %s. See --help.' % i
      sys.exit(1)
    result[kv[0]] = expand_template(kv[1], variables, result)
  return result

def main(flags, unused_argv):
  """Main method."""
  variables = {}
  for v in flags.variable:
    kv = v.split('=', 1)
    if len(kv) != 2:
      print 'Invalid value for --variable: %s. See --help.' % v
      sys.exit(-1)
    variables[kv[0]] = kv[1]
  imports = construct_imports(variables, flags.imports)
  if flags.escape_xml:
    imports = quote_xml(imports)
    variables = quote_xml(variables)
  result = expand_template(flags.template, variables, imports)
  with open(flags.output, "w") as f:
    f.write(result)
  if flags.executable:
    os.chmod(flags.output, 0o755)

if __name__ == '__main__':
  unused_argv = FLAGS(sys.argv)
  main(FLAGS, unused_argv)
