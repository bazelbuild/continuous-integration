load("@pip//:requirements.bzl", "requirement")
load("@python_versions//3.11:defs.bzl", compile_pip_requirements_3_11 = "compile_pip_requirements")
load("@rules_python//python:defs.bzl", "py_binary", "py_library", "py_test")

compile_pip_requirements_3_11(
    name = "requirements",
    requirements_in = "requirements.in",
    requirements_txt = "requirements_lock.txt",
)
