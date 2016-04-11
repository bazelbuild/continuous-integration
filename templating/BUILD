py_binary(
    name = "template_engine",
    srcs = ["main.py"],
    main = "main.py",
    visibility = ["//visibility:public"],
    deps = [
        "@gflags//:gflags",
        "@jinja2//:jinja2",
    ],
)

py_test(
    name = "integration_test",
    srcs = [
        "integration_test.py",
        "main.py",
    ],
    deps = [
        "@gflags//:gflags",
        "@jinja2//:jinja2",
    ],
)
