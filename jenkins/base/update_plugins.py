#!/usr/bin/env python3

import hashlib
import importlib.machinery
import json
import os
import os.path
import pprint
import sys
import types
import urllib.request

CACHE_DIR = os.path.expanduser("~/.update_jenkins_plugins")

def get_json_url(name):
  return "https://plugins.jenkins.io/api/plugin/%s" % name

def get_download_url(name, version):
  return "http://updates.jenkins-ci.org/download/plugins/%s/%s/%s.hpi" % (name, version, name)

def download_url(url):
  h = hashlib.sha256(url.encode("utf-8")).hexdigest()
  fname = os.path.join(CACHE_DIR, h)
  try:
    with open(fname, "rb") as f:
      return f.read()
  except OSError:
    with open(fname, "wb") as f:
      data = urllib.request.urlopen(url).read()
      f.write(data)
      return data

def get_plugin_sha256(name, version):
  url = get_download_url(name, version)
  data = download_url(url)
  return hashlib.sha256(data).hexdigest()

def load_plugins_bzl():
  # Load the current plugins.bzl.
  loader = importlib.machinery.SourceFileLoader("plugins", "plugins.bzl")
  plugins = types.ModuleType(loader.name)
  loader.exec_module(plugins)
  return plugins.JENKINS_PLUGINS

def get_plugin_json(name):
  url = get_json_url(name)
  data = download_url(url)
  return json.loads(data.decode("utf-8"))

os.makedirs(CACHE_DIR, exist_ok=True)

plugins = load_plugins_bzl()

# Update all plugins to the latest version.
current_versions = {name: metadata[0] for name, metadata in plugins.items()}
queue = [(name, metadata) for name, metadata in plugins.items()]
new_plugins = {}
rdeps = {}

while queue:
  name, metadata = queue.pop(0)

  if name in new_plugins:
    continue

  # Get information from the Jenkins API.
  plugin_json = get_plugin_json(name)
  latest_version = plugin_json["version"]

  if name not in current_versions:
    print("New plug-in: %s (%s)" % (name, latest_version), file=sys.stderr)
    new_plugins[name] = [latest_version, get_plugin_sha256(name, latest_version)]
  elif current_versions[name] != latest_version:
    print("Updated plug-in: %s (%s -> %s)" % (name, metadata[0], latest_version), file=sys.stderr)
    new_plugins[name] = [latest_version, get_plugin_sha256(name, latest_version)]
  else:
    print("Unchanged plug-in: %s (%s)" % (name, metadata[0]), file=sys.stderr)
    new_plugins[name] = metadata[0:2]

  for dep in plugin_json['dependencies']:
    if dep["optional"]:
      continue

    queue.append((dep["name"], None))
    if dep["name"] not in rdeps:
      rdeps[dep["name"]] = []
    rdeps[dep["name"]].append(name)

for name, metadata in new_plugins.items():
  if name in rdeps:
    print("%s is depended on by %s" % (name, sorted(rdeps[name])), file=sys.stderr)
  else:
    print("%s is depended on by nothing" % name, file=sys.stderr)

# Generate a new plugins.bzl.
print("""# Copyright 2015 The Bazel Authors. All rights reserved.
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

# Plugins for Jenkins
JENKINS_PLUGINS = {
 %s""" % pprint.pformat(new_plugins)[1:])
