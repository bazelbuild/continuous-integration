load("@bazel_tools//tools/build_defs/docker:docker.bzl", "docker_build")

docker_build(
    name = "base",
    base = "@jenkins//:image",
    data_path = ".",
    directory = "/usr/local/bin",
    entrypoint = [
        "/bin/bash",
        "/usr/local/bin/jenkins.sh",
    ],
    files = ["jenkins.sh"],
    visibility = ["//jenkins:__pkg__"],
)
