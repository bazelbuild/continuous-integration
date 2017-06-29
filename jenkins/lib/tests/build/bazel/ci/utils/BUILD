package(default_visibility = ["//jenkins/lib/tests:__subpackages__"])

load("@io_bazel_rules_groovy//groovy:groovy.bzl", "groovy_library")

groovy_library(
    name = "utils",
    srcs = glob(
        ["**"],
        exclude = ["BUILD"],
    ),
    deps = [
        "//3rdparty/jvm/com/lesfurets:jenkins_pipeline_unit",
        "//3rdparty/jvm/junit",
        "//3rdparty/jvm/org/jenkins_ci/plugins/workflow:workflow_step_api",
    ],
)
