#!/usr/bin/env python3
#
# Copyright 2024 The Bazel Authors. All rights reserved.
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
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
# pylint: disable=unspecified-encoding
# pylint: disable=invalid-name
"""The CI script for BCR Bazel Compatibility Test pipeline."""


import argparse
import os
import json
import re
import sys

import bazelci
import bcr_presubmit

BUILDKITE_ORG = os.environ["BUILDKITE_ORGANIZATION_SLUG"]

PIPELINE = os.environ["BUILDKITE_PIPELINE_SLUG"]

MODULE_VERSION_PATTERN = re.compile(r'(?P<module_version>[a-z](?:[a-z0-9._-]*[a-z0-9])?@[^\s]+)')

def extract_module_version(line):
    match = MODULE_VERSION_PATTERN.search(line)
    if match:
        return match.group("module_version")


def get_github_maintainer(module_name):
    metadata = json.load(open(bcr_presubmit.get_metadata_json(module_name), "r"))
    github_maintainers = []
    for maintainer in metadata["maintainers"]:
        if "github" in maintainer:
            github_maintainers.append(maintainer["github"])

    if not github_maintainers:
        github_maintainers.append("bazelbuild/bcr-maintainers")
    return github_maintainers


def print_report_in_markdown(failed_jobs_per_module, pipeline_url):
    bazel_version = os.environ.get("USE_BAZEL_VERSION")
    print("## The following modules are broken%s:" % (f" with Bazel@{bazel_version}" if bazel_version else ""))

    print("BCR Bazel Compatibility Test: ", pipeline_url)

    for module, jobs in failed_jobs_per_module.items():
        module_name = module.strip().split("@")[0]
        github_maintainers = get_github_maintainer(module_name)
        print(f"### {module}")
        print("Maintainers: ", ", ".join(f"@{maintainer}" for maintainer in github_maintainers))
        for job in jobs:
            print(f"- [{job['name']}]({job['web_url']})")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Script to report BCR Bazel Compatibility Test result.")
    parser.add_argument("--build_number", type=str)

    args = parser.parse_args(argv)
    if args.build_number:
        client = bazelci.BuildkiteClient(org=BUILDKITE_ORG, pipeline=PIPELINE)
        build_info = client.get_build_info(args.build_number)
        failed_jobs_per_module = {}
        for job in build_info["jobs"]:
            if "state" in job and "name" in job:
                module = extract_module_version(job["name"])
                if module:
                    if job["state"] == "failed":
                        if module not in failed_jobs_per_module:
                            failed_jobs_per_module[module] = []
                        failed_jobs_per_module[module].append(job)

        print_report_in_markdown(failed_jobs_per_module, build_info["web_url"])
    else:
        parser.print_help()
        return 2

if __name__ == "__main__":
    sys.exit(main())
