java_library(
    name = "jcommon",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@jfree_jcommon//jar",
    ],
)

java_library(
    name = "jfreechart",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@jfree_jfreechart//jar",
    ],
    runtime_deps = [
        ":jcommon",
    ],
)
