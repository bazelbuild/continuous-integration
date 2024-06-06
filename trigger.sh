#!/bin/bash

# Define the commit range
START_COMMIT=$1
END_COMMIT=$2

# Define Buildkite API token
PIPELINE_SLUG="publish-bazel-binaries-platform"

# Get all commits since the specified commit
commits=$(git log --format="%H" $START_COMMIT..$END_COMMIT)

# Iterate over each commit and trigger the Buildkite pipeline
for commit in $commits; do
  echo "Triggering build for commit: $commit"
  curl -X POST "https://api.buildkite.com/v2/organizations/bazel-trusted/pipelines/$PIPELINE_SLUG/builds" \
    -H "Authorization: Bearer $BUILDKITE_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "commit": "'"$commit"'",
      "branch": "master",  # Adjust branch as necessary
    }'
done

