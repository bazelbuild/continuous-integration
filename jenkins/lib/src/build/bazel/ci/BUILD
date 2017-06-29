package(default_visibility = ["//jenkins/lib:__subpackages__"])

load("@io_bazel_rules_groovy//groovy:groovy.bzl", "groovy_library")

filegroup(
    name = "ci",
    srcs = glob(
        ["**"],
        exclude = ["BUILD"],
    ),
)

groovy_library(
    name = "BazelConfiguration",
    srcs = ["BazelConfiguration.groovy"],
    deps = ["//3rdparty/jvm/com/cloudbees:groovy_cps"],
)

groovy_library(
    name = "JsonUtils",
    srcs = ["JsonUtils.groovy"],
    deps = ["//3rdparty/jvm/com/cloudbees:groovy_cps"],
)

groovy_library(
    name = "lib",
    srcs = glob(["*.groovy"]),
    deps = [
        "//3rdparty/jvm/com/cloudbees:groovy_cps",
        "//3rdparty/jvm/org/jenkins_ci/main:jenkins_core",
        "//3rdparty/jvm/org/jenkins_ci/plugins/workflow:workflow_support",
    ],
)
