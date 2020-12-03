#!/bin/bash
#
# usage: mirror.sh <URL>
#
# Downloads <URL> and automatically uploads it in the right place on mirror.bazel.build.
#
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: mirror.sh <URL>"
  exit 1
fi

source="$1"
target="${source#"https://"}"
target="${target#"http://"}"
tmpfile="$(mktemp)"

echo "Source: $source"
echo "Target: https://mirror.bazel.build/$target"
echo "Bucket: gs://bazel-mirror/$target"

curl --progress-bar --remote-time --fail --location -o "$tmpfile" "$source"
digest="$(shasum -a256 "$tmpfile" | cut -d' ' -f1)"
echo "Digest: $digest"

if gsutil ls "gs://bazel-mirror/${target}" &>/dev/null; then
  echo "File already exists on mirror, skipping upload."
else
  gsutil cp "$tmpfile" "gs://bazel-mirror/$target"
fi

gsutil setmeta -h "Cache-Control: public, max-age=31536000" "gs://bazel-mirror/$target"

cat <<EOF
Here's your snippet for the WORKSPACE file:

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "<NAME>",
    sha256 = "${digest}",
    urls = [
        "https://mirror.bazel.build/${target}",
        "${source}",
    ],
)
EOF

rm -f "$tmpfile"

exit 0
