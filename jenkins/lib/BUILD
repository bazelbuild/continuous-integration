package(default_visibility = ["//jenkins:__subpackages__"])

load("@bazel_tools//tools/build_defs/pkg:pkg.bzl", "pkg_tar")
load("@io_bazel_rules_groovy//groovy:groovy.bzl", "groovy_library")

filegroup(
    name = "vars-files",
    srcs = glob(["vars/**"]),
)

filegroup(
    name = "lib-files",
    srcs = [
        ":vars-files",
        "//jenkins/lib/src/build/bazel/ci",
    ],
)

pkg_tar(
    name = "lib",
    srcs = [":lib-files"],
    package_dir = "/opt/lib",
    strip_prefix = ".",
)
