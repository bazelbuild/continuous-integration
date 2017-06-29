package(default_visibility = ["//jenkins/lib/test:__subpackages__"])

load("@io_bazel_rules_groovy//groovy:groovy.bzl", "groovy_library")
load(":def.bzl", "bazel_groovy_test", "jenkins_library_test")

groovy_library(
    name = "BazelConfigurationParsingTest",
    srcs = ["BazelConfigurationParsingTest.groovy"],
    visibility = ["//jenkins:__subpackages__"],
    deps = ["//jenkins/lib/src/build/bazel/ci:BazelConfiguration"],
)

bazel_groovy_test(
    name = "BazelConfigurationTests",
    srcs = ["BazelConfigurationTests.groovy"],
    deps = ["//jenkins/lib/src/build/bazel/ci:BazelConfiguration"],
)

jenkins_library_test(
    name = "BazelJobTest",
    size = "small",
    srcs = ["BazelJobTest.groovy"],
)

bazel_groovy_test(
    name = "JsonUtilsTests",
    srcs = ["JsonUtilsTests.groovy"],
    deps = ["//jenkins/lib/src/build/bazel/ci:JsonUtils"],
)
