load("@pip//:requirements.bzl", "requirement")
load("@rules_python//python:py_binary.bzl", "py_binary")
load("@rules_python//python:py_library.bzl", "py_library")
load("@rules_python//python:py_test.bzl", "py_test")
load("@rules_python//python/zipapp:py_zipapp_binary.bzl", "py_zipapp_binary")


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

# py_binary(
#     name = "bazelci_bin",
#     main = "bazelci.py",
#     deps = [
#         ":bazelci",
#     ],
# )

# py_zipapp_binary(
#     name = "bazelci_zipapp",
#     binary = ":bazelci_bin",
# )
