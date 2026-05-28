load("@rules_python//python:py_binary.bzl", "py_binary")
load("@rules_python//python:py_library.bzl", "py_library")
load("@rules_python//python:py_test.bzl", "py_test")
load("@rules_python//python/zipapp:py_zipapp_binary.bzl", "py_zipapp_binary")

py_library(
    name = "collect_metrics",
    srcs = [
        "collect_metrics.py",
    ],
)

py_test(
    name = "collect_metrics_test",
    srcs = [
        "collect_metrics_test.py",
    ],
    deps = [
        ":collect_metrics",
    ],
)

py_binary(
    name = "bazelci",
    srcs = [
        "collect_metrics.py",
        "bazelci.py",
    ],
)

py_zipapp_binary(
    name = "bazelci_zipapp",
    binary = ":bazelci",
)
