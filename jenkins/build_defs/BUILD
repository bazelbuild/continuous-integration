load("//jenkins/lib:def.bzl", "bazel_job_configuration_test")

exports_files(glob([
    "bazel-job*.tpl",
    "folder.xml",
    "default.json",
]))

bazel_job_configuration_test(
    name = "default-config-test",
    configs = ["default.json"],
)
