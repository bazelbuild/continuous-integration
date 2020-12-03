# mirror.bazel.build

The Bazel team provides an HTTPS mirror for artifacts that projects in the `bazelbuild` organization reference from their WORKSPACE files.

Only Bazel team members can upload files to the mirror. Uploads are done using a [simple script](https://github.com/bazelbuild/continuous-integration/blob/master/mirror/mirror.sh) that prevents mistakes like accidentally overwriting existing files.

The base URL is https://mirror.bazel.build and we mirror files using their original URL starting with the hostname.

## Example

```
Original:                    https://github.com/google/googletest/archive/release-1.10.0.tar.gz
Mirror:   https://mirror.bazel.build/github.com/google/googletest/archive/release-1.10.0.tar.gz
```
