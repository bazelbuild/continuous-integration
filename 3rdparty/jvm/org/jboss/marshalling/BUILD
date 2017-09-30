java_library(
    name = "jboss_marshalling",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jboss_marshalling_jboss_marshalling//jar",
    ],
)

java_library(
    name = "jboss_marshalling_river",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jboss_marshalling_jboss_marshalling_river//jar",
    ],
    runtime_deps = [
        ":jboss_marshalling",
    ],
)
