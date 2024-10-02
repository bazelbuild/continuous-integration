import os

os.environ["BUILDKITE_ORGANIZATION_SLUG"] = "bazel"
os.environ["BUILDKITE_PIPELINE_SLUG"] = "bazel-bazel"
os.environ["BUILDKITE_BUILD_NUMBER"] = "29509"

import bazelci
bazelci.print_shard_summary()