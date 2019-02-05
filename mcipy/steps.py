#!/usr/bin/env python3
#
# Copyright 2019 The Bazel Authors. All rights reserved.
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

from config import PLATFORMS
from utils import python_binary, create_label, fetch_bazelcipy_command

DEFAULT_PLATFORM = "ubuntu1804"


def rchop(string_, *endings):
    for ending in endings:
        if string_.endswith(ending):
            return string_[: -len(ending)]
    return string_


def create_step(label, commands, platform=DEFAULT_PLATFORM):
    host_platform = PLATFORMS[platform].get("host-platform", platform)

    if "docker-image" in PLATFORMS[platform]:
        return create_docker_step(
            label, image=PLATFORMS[platform]["docker-image"], commands=commands
        )

    return {
        "label": label,
        "command": commands,
        "agents": {
            "kind": "worker",
            "java": PLATFORMS[platform]["java"],
            "os": rchop(host_platform, "_nojava", "_java8", "_java9", "_java10", "_java11"),
        },
    }


def create_docker_step(label, image, commands=None):
    step = {
        "label": label,
        "command": commands,
        "agents": {"kind": "docker", "os": "linux"},
        "plugins": {
            "philwo/docker": {
                "always-pull": True,
                "debug": True,
                "environment": ["BUILDKITE_ARTIFACT_UPLOAD_DESTINATION", "BUILDKITE_GS_ACL"],
                "image": image,
                "network": "host",
                "privileged": True,
                "propagate-environment": True,
                "volumes": [
                    ".:/workdir",
                    "{0}:{0}".format("/var/lib/buildkite-agent/builds"),
                    "{0}:{0}:ro".format("/var/lib/bazelbuild"),
                ],
                "workdir": "/workdir",
            }
        },
    }
    if not step["command"]:
        del step["command"]
    return step


def bazel_build_step(
    platform, project_name, http_config=None, file_config=None, build_only=False, test_only=False
):
    host_platform = PLATFORMS[platform].get("host-platform", platform)
    pipeline_command = python_binary(host_platform) + " bazelci.py runner"
    if build_only:
        pipeline_command += " --build_only"
        if "host-platform" not in PLATFORMS[platform]:
            pipeline_command += " --save_but"
    if test_only:
        pipeline_command += " --test_only"
    if http_config:
        pipeline_command += " --http_config=" + http_config
    if file_config:
        pipeline_command += " --file_config=" + file_config
    pipeline_command += " --platform=" + platform

    return create_step(
        label=create_label(platform, project_name, build_only, test_only),
        commands=[fetch_bazelcipy_command(), pipeline_command],
        platform=platform,
    )


def runner_step(
    platform,
    project_name=None,
    http_config=None,
    file_config=None,
    git_repository=None,
    git_commit=None,
    monitor_flaky_tests=False,
    use_but=False,
    incompatible_flags=None,
):
    host_platform = PLATFORMS[platform].get("host-platform", platform)
    command = python_binary(host_platform) + " bazelci.py runner --platform=" + platform
    if http_config:
        command += " --http_config=" + http_config
    if file_config:
        command += " --file_config=" + file_config
    if git_repository:
        command += " --git_repository=" + git_repository
    if git_commit:
        command += " --git_commit=" + git_commit
    if monitor_flaky_tests:
        command += " --monitor_flaky_tests"
    if use_but:
        command += " --use_but"
    for flag in incompatible_flags or []:
        command += " --incompatible_flag=" + flag
    label = create_label(platform, project_name)
    return create_step(
        label=label, commands=[fetch_bazelcipy_command(), command], platform=platform
    )
