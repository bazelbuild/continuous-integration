import os
import yaml
import sys
import subprocess
import json
import time

from config import DOWNSTREAM_PROJECTS, PLATFORMS
from steps import create_step, bazel_build_step
from utils import eprint, fetch_bazelcipy_command, python_binary


def fetch_incompatible_flags():
    """
    Return a list of incompatible flags to be tested in downstream with the current release Bazel
    """
    incompatible_flags = {}

    # If INCOMPATIBLE_FLAGS environment variable is set, we get incompatible flags from it.
    if "INCOMPATIBLE_FLAGS" in os.environ:
        for flag in os.environ["INCOMPATIBLE_FLAGS"].split():
            # We are not able to get the github link for this flag from INCOMPATIBLE_FLAGS,
            # so just assign the url to empty string.
            incompatible_flags[flag] = ""
        return incompatible_flags

    # Get bazel major version on CI, eg. 0.21 from "Build label: 0.21.0\n..."
    output = subprocess.check_output(
        ["bazel", "--nomaster_bazelrc", "--bazelrc=/dev/null", "version"]
    ).decode("utf-8")
    bazel_major_version = output.split()[2].rsplit(".", 1)[0]

    output = subprocess.check_output(
        [
            "curl",
            "https://api.github.com/search/issues?q=repo:bazelbuild/bazel+label:migration-%s+state:open"
            % bazel_major_version,
        ]
    ).decode("utf-8")
    issue_info = json.loads(output)

    for issue in issue_info["items"]:
        # Every incompatible flags issue should start with "<incompatible flag name (without --)>:"
        name = "--" + issue["title"].split(":")[0]
        url = issue["html_url"]
        if name.startswith("--incompatible_"):
            incompatible_flags[name] = url
        else:
            eprint(
                f"{name} is not recognized as an incompatible flag, please modify the issue title "
                f'of {url} to "<incompatible flag name (without --)>:..."'
            )

    return incompatible_flags


def print_disabled_projects_info_box_step():
    info_text = ["Downstream testing is disabled for the following projects :sadpanda:"]
    for project, config in DOWNSTREAM_PROJECTS.items():
        disabled_reason = config.get("disabled_reason", None)
        if disabled_reason:
            info_text.append("* **%s**: %s" % (project, disabled_reason))

    if len(info_text) == 1:
        return None
    return create_step(
        label=":sadpanda:",
        commands=[
            'buildkite-agent annotate --append --style=info "\n' + "\n".join(info_text) + '\n"'
        ],
    )


def incompatible_flag_verbose_failures_url():
    """
    URL to the latest version of this script.
    """
    return "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/incompatible_flag_verbose_failures.py?{}".format(
        int(time.time())
    )


def fetch_incompatible_flag_verbose_failures_command():
    return "curl -sS {0} -o incompatible_flag_verbose_failures.py".format(
        incompatible_flag_verbose_failures_url()
    )


def print_incompatible_flags_info_box_step(incompatible_flags_map):
    info_text = ["Build and test with the following incompatible flags:"]

    for flag in incompatible_flags_map:
        info_text.append("* **%s**: %s" % (flag, incompatible_flags_map[flag]))

    if len(info_text) == 1:
        return None
    return create_step(
        label="Incompatible flags info",
        commands=[
            'buildkite-agent annotate --append --style=info "\n' + "\n".join(info_text) + '\n"'
        ],
    )


def upload_project_pipeline_step(
    project_name, git_repository, http_config, file_config, incompatible_flags
):
    pipeline_command = (
        '{0} bazelci.py project_pipeline --project_name="{1}" ' + "--git_repository={2}"
    ).format(python_binary(), project_name, git_repository)
    if incompatible_flags is None:
        pipeline_command += " --use_but"
    else:
        for flag in incompatible_flags:
            pipeline_command += " --incompatible_flag=" + flag
    if http_config:
        pipeline_command += " --http_config=" + http_config
    if file_config:
        pipeline_command += " --file_config=" + file_config
    pipeline_command += " | buildkite-agent pipeline upload"

    return create_step(
        label="Setup {0}".format(project_name),
        commands=[fetch_bazelcipy_command(), pipeline_command],
    )


def main(configs, http_config, file_config, test_incompatible_flags, test_disabled_projects):
    if not configs:
        raise Exception("Bazel downstream pipeline configuration is empty.")

    if set(configs) != set(PLATFORMS):
        raise Exception(
            "Bazel downstream pipeline needs to build Bazel on all supported platforms (has=%s vs. want=%s)."
            % (sorted(set(configs)), sorted(set(PLATFORMS)))
        )

    pipeline_steps = []

    info_box_step = print_disabled_projects_info_box_step()
    if info_box_step is not None:
        pipeline_steps.append(info_box_step)

    if not test_incompatible_flags:
        for platform in configs:
            pipeline_steps.append(
                bazel_build_step(platform, "Bazel", http_config, file_config, build_only=True)
            )

        pipeline_steps.append("wait")

    incompatible_flags = None
    if test_incompatible_flags:
        incompatible_flags_map = fetch_incompatible_flags()
        info_box_step = print_incompatible_flags_info_box_step(incompatible_flags_map)
        if info_box_step is not None:
            pipeline_steps.append(info_box_step)
        incompatible_flags = list(incompatible_flags_map.keys())

    for project, config in DOWNSTREAM_PROJECTS.items():
        disabled_reason = config.get("disabled_reason", None)
        # If test_disabled_projects is true, we add configs for disabled projects.
        # If test_disabled_projects is false, we add configs for not disbaled projects.
        if (test_disabled_projects and disabled_reason) or (
            not test_disabled_projects and not disabled_reason
        ):
            pipeline_steps.append(
                upload_project_pipeline_step(
                    project_name=project,
                    git_repository=config["git_repository"],
                    http_config=config.get("http_config", None),
                    file_config=config.get("file_config", None),
                    incompatible_flags=incompatible_flags,
                )
            )

    if test_incompatible_flags:
        pipeline_steps.append({"wait": "~", "continue_on_failure": "true"})
        current_build_number = os.environ.get("BUILDKITE_BUILD_NUMBER", None)
        if not current_build_number:
            raise Exception("Not running inside Buildkite")
        pipeline_steps.append(
            create_step(
                label="Test failing jobs with incompatible flag separately",
                commands=[
                    fetch_bazelcipy_command(),
                    fetch_incompatible_flag_verbose_failures_command(),
                    python_binary()
                    + " incompatible_flag_verbose_failures.py --build_number=%s | buildkite-agent pipeline upload"
                    % current_build_number,
                ],
            )
        )

    print(yaml.dump({"steps": pipeline_steps}))


if __name__ == "__main__":
    sys.exit(main())
