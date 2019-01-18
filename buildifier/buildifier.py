#!/usr/bin/env python3

import os.path
import re
import subprocess
import sys

regex = re.compile(
    r"(?P<filename>[^:]*):(?P<line>\d*):(?:(?P<column>\d*):)? (?P<message>.*)"
)

files = []
for root, dirnames, filenames in os.walk("."):
    for filename in filenames:
        if filename in ["BUILD", "BUILD.bazel"] or filename.endswith(".bzl"):
            files.append(os.path.relpath(os.path.join(root, filename)))

result = subprocess.run(
    ["buildifier", "--lint=warn"] + sorted(files),
    capture_output=True,
    universal_newlines=True,
)

findings = []
messages = []

for line in result.stderr.splitlines():
    match = regex.match(line)
    if match:
        findings.append(match)
    else:
        messages.append(line)

if not findings and not messages:
    sys.exit(0)

for finding in findings:
