package(default_visibility = ["//jenkins:__subpackages__"])

load("@bazel_tools//tools/build_defs/pkg:pkg.bzl", "pkg_tar")
load("@io_bazel_rules_groovy//groovy:groovy.bzl", "groovy_library")

pkg_tar(
    name = "lib",
    files = glob([
        "src/build/**",
        "vars/**",
    ]),
    package_dir = "/opt/lib",
    strip_prefix = ".",
)

groovy_library(
    name = "BazelConfigurationTests",
    srcs = [
        "src/build/bazel/ci/BazelConfiguration.groovy",
        "tests/build/bazel/ci/BazelConfigurationTests.groovy",
    ],
)

groovy_library(
    name = "JsonUtilsTests",
    srcs = [
        "src/build/bazel/ci/JsonUtils.groovy",
        "tests/build/bazel/ci/NonCPS.groovy",
        "tests/build/bazel/ci/JsonUtilsTests.groovy",
    ],
)

groovy_library(
    name = "BazelConfigurationParsingTest",
    srcs = [
        "src/build/bazel/ci/BazelConfiguration.groovy",
        "tests/build/bazel/ci/BazelConfigurationParsingTest.groovy",
    ],
)

java_test(
    name = "BazelConfigurationTests-test",
    size = "small",
    runtime_deps = [
        "@org_codehaus_groovy_all//jar",
        "@org_hamcrest//jar",
        ":BazelConfigurationTests",
    ],
    test_class = "build.bazel.ci.BazelConfigurationTests",
)

java_test(
    name = "JsonUtilsTests-test",
    size = "small",
    runtime_deps = [
        "@org_codehaus_groovy_all//jar",
        "@org_hamcrest//jar",
        ":JsonUtilsTests",
    ],
    test_class = "build.bazel.ci.JsonUtilsTests",
)
