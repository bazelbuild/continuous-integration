import sys
import yaml

from config import PLATFORMS
from steps import create_step, bazel_build_step
from utils import fetch_bazelcipy_command, python_binary


def main(configs, http_config, file_config):
    if not configs:
        raise Exception("Bazel publish binaries pipeline configuration is empty.")

    for platform in configs.copy():
        if platform not in PLATFORMS:
            raise Exception("Unknown platform '{}'".format(platform))
        if not PLATFORMS[platform]["publish_binary"]:
            del configs[platform]

    if set(configs) != set(
        name for name, platform in PLATFORMS.items() if platform["publish_binary"]
    ):
        raise Exception(
            "Bazel publish binaries pipeline needs to build Bazel for every commit on all publish_binary-enabled platforms."
        )

    # Build Bazel
    pipeline_steps = []

    for platform in configs:
        pipeline_steps.append(
            bazel_build_step(platform, "Bazel", http_config, file_config, build_only=True)
        )

    pipeline_steps.append("wait")

    # If all builds succeed, publish the Bazel binaries to GCS.
    pipeline_steps.append(
        create_step(
            label="Publish Bazel Binaries",
            commands=[fetch_bazelcipy_command(), python_binary() + " bazelci.py publish_binaries"],
        )
    )

    print(yaml.dump({"steps": pipeline_steps}))


if __name__ == "__main__":
    sys.exit(main())
