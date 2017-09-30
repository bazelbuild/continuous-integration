java_library(
    name = "j_interop",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_kohsuke_jinterop_j_interop//jar",
    ],
    runtime_deps = [
        ":j_interopdeps",
    ],
)

java_library(
    name = "j_interopdeps",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_kohsuke_jinterop_j_interopdeps//jar",
    ],
    runtime_deps = [
        "//3rdparty/jvm/org/samba/jcifs",
    ],
)
