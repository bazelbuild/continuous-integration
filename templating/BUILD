py_binary(
    name = "template_engine",
    srcs = ["main.py"],
    main = "main.py",
    visibility = ["//visibility:public"],
    deps = [
        "@com_github_google_python_gflags//:gflags",
        "@org_pocoo_jinja_jinja2//:jinja2",
    ],
)

py_test(
    name = "integration_test",
    srcs = [
        "integration_test.py",
        "main.py",
    ],
    deps = [
        "@com_github_google_python_gflags//:gflags",
        "@org_pocoo_jinja_jinja2//:jinja2",
    ],
)
