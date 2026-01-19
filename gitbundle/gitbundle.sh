#!/bin/bash

set -euo pipefail

BUILDKITE_API_TOKEN=$(gsutil cat "gs://bazel-encrypted-secrets/buildkite-api-token.enc" | \
    gcloud kms decrypt --project "bazel-public" --location "global" --keyring "buildkite" --key "buildkite-api-token" --plaintext-file "-" --ciphertext-file "-")

git config --global safe.bareRepository all

echo "+++ Starting Git Mirror Update $(date)"

echo "--- Downloading existing mirrors from GCS"
rm -rf bazelbuild
gsutil cat "gs://bazel-git-mirror/bazelbuild-mirror.tar" | tar x
cd bazelbuild

function mirror() {
    repo="$1"
    remote_name="$(echo -n $repo | tr -C '[[:alnum:]]' '-')"
    if [[ -d $remote_name ]]; then
        echo "--- Updating $repo in $remote_name"
        git -C "${remote_name}" fetch --prune
    else
        echo "+++ Cloning $repo into $remote_name"
        git clone --bare "${repo}" "${remote_name}"
        git -C "${remote_name}" config pack.compression 9
    fi
    echo "--- Repacking $remote_name"
    git -C "${remote_name}" repack -a -d -F --threads=0
}

echo "--- Fetching repositories from Buildkite API"
REPOS=$(curl -sS -H "Authorization: Bearer ${BUILDKITE_API_TOKEN}" "https://api.buildkite.com/v2/organizations/bazel/pipelines?per_page=100" \
    | jq '.[] | .repository' | sort -u | sed -e 's/^"//' -e 's/"$//')

echo "--- Mirroring Buildkite repositories"
for repo in $REPOS; do
    mirror "$repo" &
done

wait

echo "--- Fetching repositories from bazelci.py"
REPOS_CI=$(fgrep '"git_repository": "' ../../buildkite/bazelci.py | cut -d'"' -f4 | sort -u)

echo "--- Mirroring bazelci.py repositories"
for repo in $REPOS_CI; do
    mirror "$repo" &
done

wait

echo "--- Cleaning up .DS_Store files"
find . -name .DS_Store -delete

cd ..

echo "--- Verifying the Bazel mirror is up-to-date"
TEST_REPO="https://github.com/bazelbuild/bazel.git"
TEST_MIRROR="https---github-com-bazelbuild-bazel-git"

if [[ -d "bazelbuild/$TEST_MIRROR" ]]; then
    REMOTE_SHA=$(git ls-remote "$TEST_REPO" HEAD | cut -f1)
    LOCAL_SHA=$(git -c safe.bareRepository=all -C "bazelbuild/$TEST_MIRROR" rev-parse HEAD)
    echo "Remote SHA: $REMOTE_SHA"
    echo "Local SHA:  $LOCAL_SHA"

    if [[ "$REMOTE_SHA" == "$LOCAL_SHA" ]]; then
        echo "✅ Mirror is up-to-date."
    else
        echo "❌ Mirror is NOT up-to-date!"
        exit 1
    fi
else
    echo "❌ Test mirror bazelbuild/$TEST_MIRROR does not exist!"
    exit 1
fi

echo "+++ Uploading Git Mirror... $(date)"

tar c bazelbuild | gsutil cp - "gs://bazel-git-mirror/bazelbuild-mirror.tar"
zip -q0r - bazelbuild | gsutil cp - "gs://bazel-git-mirror/bazelbuild-mirror.zip"
