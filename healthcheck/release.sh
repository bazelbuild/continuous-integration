#!/bin/sh

set -eux

gsutil -m cp bin/* gs://bazel-ci/healthcheck/
