#!/bin/bash

set -euxo pipefail

BUILDKITE_API_TOKEN=$(gsutil cat "gs://bazel-encrypted-secrets/buildkite-api-token.enc" | \
    gcloud kms decrypt --location "global" --keyring "buildkite" --key "buildkite-api-token" --plaintext-file "-" --ciphertext-file "-")

rm -rf bazelbuild
gsutil cat "gs://bazel-git-mirror/bazelbuild.tar" | tar x
cd bazelbuild

git config --local gc.auto 0

for remote in $(git remote); do
    git remote remove "${remote}"
done

for repo in $(curl -sS -H "Authorization: Bearer ${BUILDKITE_API_TOKEN}" "https://api.buildkite.com/v2/organizations/bazel/pipelines?per_page=100" \
    | jq '.[] | .repository' | sort -u | sed -e 's/^"//' -e 's/"$//'); do
remote_name="$(echo $repo | md5sum | cut -d' ' -f1)"
git remote add --no-tags "${remote_name}" "${repo}"
done

git fetch --all
git gc --aggresive

cd ..
tar c bazelbuild | gsutil -m cp -a public-read - "gs://bazel-git-mirror/bazelbuild.tar"
