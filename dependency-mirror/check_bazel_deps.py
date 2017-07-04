#!/usr/bin/python
#
# Copyright 2015 The Bazel Authors. All rights reserved.
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

# Python tool to read all external bazel dependencies and mirror them on GCS.
import argparse
import hashlib
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib2

_BAZEL_MIRROR_BUCKET = 'bazel-mirror'
_CACHE_MAX_AGE = 60 * 60 * 24 * 365  # one year
_CALL_PATTERN = re.compile(r'\bif not omit_(\w+):\n +(\w+)\(\)')
_DEFAULT_CONTENT_TYPE = 'application/binary'
_DEF_PATTERN = re.compile(r'(?<=\ndef )(\w+)\(\):\n  \w+\(\n +name = "([^"]+)"')
_GSUTIL = 'gsutil/gsutil'
_MIRROR_URL = re.compile(r'^https?://mirror.bazel.build/(.*)$')
_PARAM_PATTERN = re.compile(r'(?<=omit_)\w+(?==)')
_REPOSITORIES_FUNCTION_PATTERN = re.compile(r'\ndef \w+?_repositories\(')
_RULE_PATTERN = re.compile(r'\w+\(\n +name = "[^"]+".*?\n +\)\n', re.S)
_SHA256_PATTERN = re.compile(r'[0-9a-f]{64}')
_THREAD_COUNT = 5
_URL_PATTERN = re.compile(r'(?<=")https?://[^"\s]+')

_COMPESSIBLE_MIMETYPES = set([
    'application/javascript',
    'application/json',
    'application/json+protobuf',
    'image/svg+xml',
])


class _State(object):
  """Container for state of workspace rule checker across threads."""

  def __init__(self):
    """Creates new instance."""
    self._lock = threading.Lock()
    self._queue = []
    self._errors = []

  @property
  def errors(self):
    """Returns all errors that have been added."""
    with self._lock:
      return self._errors[:]

  def log(self, message):
    """Emits a log message.

    Args:
      message: String saying something.
    """
    with self._lock:
      print >>sys.stderr, message

  def log_error(self, message):
    """Adds an error message.

    Args:
      message: String message explaining error.
    """
    with self._lock:
      self._errors.append(message)

  def add_work_item(self, item):
    """Adds item to work queue.

    Args:
      item: Arbitrary item of work.
    """
    with self._lock:
      self._queue.append(item)

  def get_work_item(self):
    """Returns item from work queue.

    Returns:
      Arbitrary item of work or None if queue is empty.
    """
    with self._lock:
      return self._queue.pop() if self._queue else None


class _Rule(object):
  """Value class for a workspace rule."""

  def __init__(self, urls, sha256):
    """Creates new instance.

    Args:
      urls: List of string URLs.
      sha256: Hex checksum to which each URL contents must conform.
    """
    self.urls = urls
    self.sha256 = sha256

  @property
  def content_type(self):
    """Guesses Content-Type for CDN when mirroring rules.

    The first URL that has a recognizable extension will be chosen. Otherwise,
    the default will be used.

    Returns:
      String value for Content-Type header.
    """
    for url in self.urls:
      if url.endswith('.ts'):
        return 'text/plain'  # Python thinks TypeScript is video/MP2T.
      mime = mimetypes.guess_type(url)[0]
      if mime:
        return mime
    return _DEFAULT_CONTENT_TYPE

  @property
  def is_compressible(self):
    """Determines if CDN should be configured to allow gzipped transmission.

    Returns:
      True if mime represents content that is suitable for compression.
    """
    mime = self.content_type
    return mime.startswith('text/') or mime in _COMPESSIBLE_MIMETYPES


class _RuleChecker(object):
  """Checker for attributes of individual workspace rules."""

  def __init__(self, state, force):
    """Creates new instance.

    Args:
      state: _State object for program.
      force: Indicates mirroring should be forced even if already done.
    """
    self._state = state
    self._force = force
    self._was_mirrored = set()  # prevents infinite loop when --force

  def __call__(self, rule):
    """Checks validity of rule.

    If an error is found it is stored to the program state. The work queue may
    also be mutated.

    Args:
      rule: _Rule object to check.
    """
    unmirrored = set()
    for url in rule.urls:
      is_mirror = self._is_mirror_url(url)
      if self._force and is_mirror and url not in self._was_mirrored:
        unmirrored.add(url)
        continue
      self._state.log('Checking ' + url)
      try:
        connection = urllib2.urlopen(url)
      except urllib2.URLError as error:
        if is_mirror:
          unmirrored.add(url)
        else:
          self._state.log_error('%s %s' % (error, url))
        continue
      sha256 = hashlib.sha256(connection.read()).hexdigest()
      if sha256 != rule.sha256:
        self._state.log_error('bad checksum for %s is %s but wanted %s' % (
            url, sha256, rule.sha256))
    if unmirrored:
      success = True
      for url in unmirrored:
        success &= self._mirror(rule, url)
      if success:
        self._state.add_work_item(rule)

  def _is_mirror_url(self, url):
    """Determines if URL is something we mirror.

    The URL must be: http://mirror.bazel.build/HOSTNAME/PATH. The
    way we tell mirrored GCS URLs apart from ordinary GCS URLs is based on
    whether or not the HOSTNAME portion contains a dot.

    Args:
      url: String URL.

    Returns:
      True if url is something we bear responsibility for mirroring.
    """
    match = _MIRROR_URL.search(url)
    if match is None:
      return False
    labels = match.group(1).split('/')
    return len(labels) > 1 and '.' in labels[0]

  def _mirror(self, rule, url):
    """Mirrors URL to Google Cloud Storage.

    Args:
      rule: _Rule object from which url originated.
      url: A URL within rule that is in mirror format.

    Returns:
      True if operation was successful, otherwise False.
    """
    self._was_mirrored.add(url)
    match = _MIRROR_URL.search(url)
    original_url = 'http://' + match.group(1)
    gs_url = 'gs://%s/%s' % (_BAZEL_MIRROR_BUCKET, match.group(1))

    self._state.log('Mirroring ' + original_url)

    try:
      input_ = urllib2.urlopen(original_url)
    except urllib2.URLError as error:
      self._state.log_error('%s %s' % (original_url, error))
      return False

    fd, path = tempfile.mkstemp()
    try:
      with open(path, 'w') as output:
        shutil.copyfileobj(input_, output)
      args = [_GSUTIL, 'cp']
      if rule.is_compressible:
        # When mirroring uncompressed files, e.g. JavaScript, it is
        # advantageous to allow the CDN apply gzip compression ahead of time,
        # so that it can be served to Bazel in a more efficient manner.
        args.append('-Z')
      args.extend(['-a', 'public-read', path, gs_url])
      status = subprocess.call(args)
      if status != 0:
        self._state.log_error('could not copy to ' + gs_url)
        return False
    finally:
      os.unlink(path)
      os.close(fd)

    status = subprocess.call(
        [_GSUTIL, 'setmeta',
         '-h', 'Content-Type:' + rule.content_type,
         '-h', 'Cache-Control:public, max-age=%d' % _CACHE_MAX_AGE,
         gs_url])
    if status != 0:
      self._state.log_error('could not setmeta on ' + gs_url)
      return False

    return True


class _Worker(object):
  """Thread that consumes input from a work queue."""

  def __init__(self, state, callback):
    """Creates new instance.

    Args:
      state: _State object containing stored program data.
      callback: Function that consumes a single item of work.
    """
    self._state = state
    self._callback = callback

  def __call__(self):
    """Runs thread until work items are exhausted."""
    while True:
      item = self._state.get_work_item()
      if item is None:
        break
      self._callback(item)


def _run_in_multiple_threads(worker, count=_THREAD_COUNT):
  """Runs a pool of threads and waits for it to complete.

  Args:
    worker: Function that runs in separate threads.
    count: Number of threads to spawn.
  """
  threads = [threading.Thread(target=worker) for _ in range(count)]
  for thread in threads:
    thread.start()
  for thread in threads:
    thread.join()


class _WorkspaceInspector(object):
  """Utility for extracting information from workspace source code."""

  def __init__(self, state):
    """Creates new instance.

    Args:
      state: _State object containing program state.
    """
    self._state = state

  def extract_rules(self, contents):
    """Extracts information about workspace rules from source file.

    Most rules, e.g. new_http_archive will have one sha256 and multiple URLs.
    However there exists other repository rules like filegroup_external where
    multiple external files can be defined within the same rule. Each will be
    extracted, however the rule MUST be designed in such a way that the checksum
    appears before the URLs with which it's associated.

    Args:
      contents: String containing contents of Bazel source file.

    Yields:
      _Rule objects parsed from file.
    """
    for chunk in _RULE_PATTERN.findall(contents):
      urls = [(m.start(), m.group(0)) for m in _URL_PATTERN.finditer(chunk)]
      shas = [(m.start(), m.group(0)) for m in _SHA256_PATTERN.finditer(chunk)]
      if not shas and not urls:
        continue
      if not shas:
        self._state.log_error('No sha256 checksum on\n' + chunk)
      if len(shas) == 1:
        yield self._make_rule([url for _, url in urls], shas[0][1])
        continue
      for start, sha in reversed(shas):
        links = []
        while urls and urls[-1][0] > start:
          links.append(urls.pop()[1])
        if not links:
          self._state.log_error(
              'No urls come after %s within:\n%s' % (sha, chunk))
          continue
        links.reverse()
        yield self._make_rule(links, sha)

  def _make_rule(self, urls, sha256):
    """Constructs _Rule object.

    Args:
      urls: List of string URLs.
      sha256: Hex checksum to which each URL contents must conform.

    Returns:
      Instance of _Rule.
    """
    if len(urls) == 1:
      self._state.log_error('URL should be mirrored for redundancy: ' + urls[0])
    return _Rule(urls, sha256)


class _StyleChecker(object):
  """Utility for checking foo_repositories() boilerplate.

  This class is meant to enforce the best practice described here:
  https://github.com/bazelbuild/bazel/issues/1952
  """

  def __init__(self, state):
    """Creates new instance.

    Args:
      state: _State object containing program state.
    """
    self._state = state

  def check_style(self, contents):
    """Enforces style on file contents.

    Error messages are stored to program state.

    Args:
      contents: String containing contents of Bazel source file.
    """
    if _REPOSITORIES_FUNCTION_PATTERN.search(contents) is None:
      return
    params = _PARAM_PATTERN.findall(contents)

    defs = []
    for match in _DEF_PATTERN.finditer(contents):
      if match.group(1) == match.group(2):
        defs.append(match.group(1))

    calls = []
    for match in _CALL_PATTERN.finditer(contents):
      if match.group(1) != match.group(2):
        self._state.log_error('bad repo function call:\n' + match.group(0))
      calls.append(match.group(1))

    for name, other in (('repository function parameters', params),
                        ('repository function calls', calls),
                        ('external repo functions', defs)):
      if list(sorted(other)) != other:
        self._state.log_error(name + ' not sorted')
      if set(other) != set(params):
        self._state.log_error(name + ' list not consistent with others')


def check_bazel_deps(contents, force=False):
  """Lints Bazel workspace file.

  Args:
    contents: String contents of WORKSPACE or repositories.bzl file.
    force: Indicates mirroring should be forced even if not already done.

  Returns:
    List of error message strings.
  """
  state = _State()
  rule_checker = _RuleChecker(state, force)
  worker = _Worker(state, rule_checker)
  inspector = _WorkspaceInspector(state)
  for rule in inspector.extract_rules(contents):
    state.add_work_item(rule)
  styler = _StyleChecker(state)
  styler.check_style(contents)
  _run_in_multiple_threads(worker)
  return state.errors


def main():
  """Runs program."""
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('workspaces', metavar='PATH', type=str, nargs='+',
                      help='a WORKSPACE or repositories.bzl file')
  parser.add_argument('--force', dest='force', action='store_true',
                      help='always mirror GCS mirror URLs, even if they exist')
  args = parser.parse_args()

  errors = []
  for workspace in args.workspaces:
    with open(workspace) as fi:
      data = fi.read()
    file_errors = check_bazel_deps(data, args.force)
    if len(args.workspaces) > 1:
      file_errors = ['%s: %s' % (workspace, error) for error in file_errors]
    errors.extend(file_errors)

  if errors:
    for error in errors:
      print >>sys.stderr, 'ERROR:', error
  else:
    print >>sys.stderr, 'LGTM'


if __name__ == '__main__':
  main()
