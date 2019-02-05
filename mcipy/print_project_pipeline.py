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

import os
import yaml

from config import CLOUD_PROJECT, DOWNSTREAM_PROJECTS
from steps import runner_step, create_docker_step, create_step
from update_last_green_commit import get_last_green_commit
from utils import fetch_bazelcipy_command
from utils import python_binary


def is_pull_request():
    third_party_repo = os.getenv("BUILDKITE_PULL_REQUEST_REPO", "")
    return len(third_party_repo) > 0


def main(
    configs,
    project_name,
    http_config,
    file_config,
    git_repository,
    monitor_flaky_tests,
    use_but,
    incompatible_flags,
):
    platform_configs = configs.get("platforms", None)
    if not platform_configs:
        raise Exception("{0} pipeline configuration is empty.".format(project_name))

    pipeline_steps = []

    if configs.get("buildifier"):
        pipeline_steps.append(
            create_docker_step("Buildifier", image=f"gcr.io/{CLOUD_PROJECT}/buildifier")
        )

    # In Bazel Downstream Project pipelines, git_repository and project_name must be specified,
    # and we should test the project at the last green commit.
    git_commit = None
    if (use_but or incompatible_flags) and git_repository and project_name:
        git_commit = get_last_green_commit(
            git_repository, DOWNSTREAM_PROJECTS[project_name]["pipeline_slug"]
        )
    for platform in platform_configs:
        step = runner_step(
            platform,
            project_name,
            http_config,
            file_config,
            git_repository,
            git_commit,
            monitor_flaky_tests,
            use_but,
            incompatible_flags,
        )
        pipeline_steps.append(step)

    pipeline_slug = os.getenv("BUILDKITE_PIPELINE_SLUG")
    all_downstream_pipeline_slugs = []
    for _, config in DOWNSTREAM_PROJECTS.items():
        all_downstream_pipeline_slugs.append(config["pipeline_slug"])
    # We don't need to update last green commit in the following cases:
    #   1. This job is a github pull request
    #   2. This job uses a custom built Bazel binary (In Bazel Downstream Projects pipeline)
    #   3. This job doesn't run on master branch (Could be a custom build launched manually)
    #   4. We don't intend to run the same job in downstream with Bazel@HEAD (eg. google-bazel-presubmit)
    #   5. We are testing incompatible flags
    if not (
        is_pull_request()
        or use_but
        or os.getenv("BUILDKITE_BRANCH") != "master"
        or pipeline_slug not in all_downstream_pipeline_slugs
        or incompatible_flags
    ):
        pipeline_steps.append("wait")

        # If all builds succeed, update the last green commit of this project
        pipeline_steps.append(
            create_step(
                label="Try Update Last Green Commit",
                commands=[
                    fetch_bazelcipy_command(),
                    python_binary() + " bazelci.py try_update_last_green_commit",
                ],
            )
        )

    print(yaml.dump({"steps": pipeline_steps}))
