java_library(
    name = "spring_aop",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_springframework_spring_aop//jar",
    ],
)

java_library(
    name = "spring_beans",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_springframework_spring_beans//jar",
    ],
)

java_library(
    name = "spring_context",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_springframework_spring_context//jar",
    ],
)

java_library(
    name = "spring_context_support",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_springframework_spring_context_support//jar",
    ],
)

java_library(
    name = "spring_core",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_springframework_spring_core//jar",
    ],
)

java_library(
    name = "spring_dao",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_springframework_spring_dao//jar",
    ],
)

java_library(
    name = "spring_jdbc",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_springframework_spring_jdbc//jar",
    ],
    runtime_deps = [
        ":spring_dao",
    ],
)

java_library(
    name = "spring_web",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_springframework_spring_web//jar",
    ],
)

java_library(
    name = "spring_webmvc",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_springframework_spring_webmvc//jar",
    ],
    runtime_deps = [
        ":spring_beans",
        ":spring_context",
        ":spring_context_support",
        ":spring_web",
    ],
)
