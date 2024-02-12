#!/bin/bash

# Download the latest postsubmit.yml from the Bazel repository and apply the patch to add `bazel mod deps --lockfile_mode=update` in setup phase.
curl -o bazel-postsubmit.yml https://raw.githubusercontent.com/bazelbuild/bazel/master/.bazelci/postsubmit.yml
patch < bazel-postsubmit.patch
