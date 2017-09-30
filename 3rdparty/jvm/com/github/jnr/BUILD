java_library(
    name = "jffi",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@com_github_jnr_jffi//jar",
    ],
)

java_library(
    name = "jnr_constants",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@com_github_jnr_jnr_constants//jar",
    ],
)

java_library(
    name = "jnr_ffi",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@com_github_jnr_jnr_ffi//jar",
    ],
    runtime_deps = [
        ":jffi",
        ":jnr_x86asm",
        "//3rdparty/jvm/org/ow2/asm",
        "//3rdparty/jvm/org/ow2/asm:asm_analysis",
        "//3rdparty/jvm/org/ow2/asm:asm_commons",
        "//3rdparty/jvm/org/ow2/asm:asm_tree",
        "//3rdparty/jvm/org/ow2/asm:asm_util",
    ],
)

java_library(
    name = "jnr_posix",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@com_github_jnr_jnr_posix//jar",
    ],
    runtime_deps = [
        ":jnr_constants",
        ":jnr_ffi",
    ],
)

java_library(
    name = "jnr_x86asm",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@com_github_jnr_jnr_x86asm//jar",
    ],
)
