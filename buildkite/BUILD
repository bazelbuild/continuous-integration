load("@pip//:requirements.bzl", "requirement")
load("@rules_python//python:py_binary.bzl", "py_binary")
load("@rules_python//python:py_library.bzl", "py_library")
load("@rules_python//python:py_test.bzl", "py_test")
load(":lightweight_py_zipapp_binary.bzl", "lightweight_py_binary_zipapp")


py_library(
    name = "bazelci",
    srcs = ["bazelci.py", "collect_metrics.py"],
    deps = [
        requirement("pyyaml"),
        requirement("requests"),
    ],
)

py_test(
    name = "collect_metrics_test",
    srcs = [
        "collect_metrics_test.py",
    ],
    deps = [
        ":bazelci",
    ],
)

py_binary(
    name = "bazelci_bin",
    srcs = ["bazelci.py"],
    main = "bazelci.py",
    deps = [
        ":bazelci",
    ],
)


lightweight_py_binary_zipapp(
    name = "bazelci_zipapp_custom",
    binary = ":bazelci_bin",
    main = "buildkite.bazelci:main",
)

