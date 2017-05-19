load("//jenkins/lib:def.bzl", "bazel_job_configuration_test")

exports_files(glob([
    "github-jobs*.tpl",
    "folder.xml",
]))

bazel_job_configuration_test(
    name = "default-config-test",
    configs = ["default.json"],
)
