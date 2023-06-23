#!/bin/bash

set -euo pipefail

release_candidates="$(buildkite-agent meta-data get "release_candidates")"

PIPELINE="steps:
  - trigger: \"rules-java-updates\"
    label: \"Update rules_java\"
    build:
      message: ${BUILDKITE_MESSAGE}
      env:
        release_candidates: ${release_candidates}
"

echo "$PIPELINE" | buildkite-agent pipeline upload
