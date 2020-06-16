#!/bin/bash

set -euo pipefail

BUILDKITE_API_TOKEN=$(gsutil cat "gs://bazel-encrypted-secrets/buildkite-api-token.enc" | \
    gcloud kms decrypt --project "bazel-public" --location "global" --keyring "buildkite" --key "buildkite-api-token" --plaintext-file "-" --ciphertext-file "-")

rm -rf bazelbuild
gsutil cat "gs://bazel-git-mirror/bazelbuild-mirror.tar" | tar x
# mkdir bazelbuild
cd bazelbuild

git config pack.compression 9

function mirror() {
    repo="$1"
    remote_name="$(echo -n $repo | tr -C '[[:alnum:]]' '-')"
    if [[ -d $remote_name ]]; then
        git -C "${remote_name}" fetch
    else
        git clone --bare "${repo}" "${remote_name}"
    fi
    git -C "${remote_name}" repack -a -d -F --threads=0
}

for repo in $(curl -sS -H "Authorization: Bearer ${BUILDKITE_API_TOKEN}" "https://api.buildkite.com/v2/organizations/bazel/pipelines?per_page=100" \
    | jq '.[] | .repository' | sort -u | sed -e 's/^"//' -e 's/"$//'); do
    mirror "$repo" &
done

wait

for repo in $(fgrep '"git_repository": "' ../../buildkite/bazelci.py | cut -d'"' -f4 | sort -u); do
    mirror "$repo" &
done

wait

find . -name .DS_Store -delete

cd ..

# Verify that it works:
rm -rf bazel-test
git clone --reference bazelbuild/https---github-com-bazelbuild-bazel-git https://github.com/bazelbuild/bazel.git bazel-test

tar c bazelbuild | gsutil cp - "gs://bazel-git-mirror/bazelbuild-mirror.tar"
zip -q0r - bazelbuild | gsutil cp - "gs://bazel-git-mirror/bazelbuild-mirror.zip"
