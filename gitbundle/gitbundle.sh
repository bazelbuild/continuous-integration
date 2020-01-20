#!/bin/bash

set -euxo pipefail

BUILDKITE_API_TOKEN=$(gsutil cat "gs://bazel-encrypted-secrets/buildkite-api-token.enc" | \
    gcloud kms decrypt --project "bazel-public" --location "global" --keyring "buildkite" --key "buildkite-api-token" --plaintext-file "-" --ciphertext-file "-")

rm -rf bazelbuild
gsutil cat "gs://bazel-git-mirror/bazelbuild-mirror.tar" | tar x
cd bazelbuild

function mirror() {
    repo="$1"
    remote_name="$(echo -n $repo | tr -C '[[:alnum:]]' '-')"
    if [[ -d $remote_name ]]; then
        git -C "${remote_name}" remote set-url origin "${repo}"
        git -C "${remote_name}" remote update --prune
    else
        git clone --mirror "${repo}" "${remote_name}"
    fi
}

for repo in $(curl -sS -H "Authorization: Bearer ${BUILDKITE_API_TOKEN}" "https://api.buildkite.com/v2/organizations/bazel/pipelines?per_page=100" \
    | jq '.[] | .repository' | sort -u | sed -e 's/^"//' -e 's/"$//'); do
    mirror "$repo" &
done

for repo in $(fgrep '"git_repository": "' ../buildkite/bazelci.py | cut -d'"' -f4 | sort -u); do
    mirror "$repo" &
done

wait

find . -name .DS_Store -delete

cd ..

# Verify that it works:
git clone --reference bazelbuild/https---github-com-bazelbuild-bazel-git https://github.com/bazelbuild/bazel.git bazel-test

tar c bazelbuild | gsutil cp - "gs://bazel-git-mirror/bazelbuild-mirror.tar"
zip -q0r - bazelbuild | gsutil cp - "gs://bazel-git-mirror/bazelbuild-mirror.zip"
