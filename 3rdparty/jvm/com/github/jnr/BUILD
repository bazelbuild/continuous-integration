java_library(
    name = "jffi",
    exports = [
        "//external:jar/com/github/jnr/jffi"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "jnr_constants",
    exports = [
        "//external:jar/com/github/jnr/jnr_constants"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "jnr_ffi",
    exports = [
        "//external:jar/com/github/jnr/jnr_ffi"
    ],
    runtime_deps = [
        "//3rdparty/jvm/org/ow2/asm:asm",
        "//3rdparty/jvm/org/ow2/asm:asm_analysis",
        "//3rdparty/jvm/org/ow2/asm:asm_commons",
        "//3rdparty/jvm/org/ow2/asm:asm_tree",
        "//3rdparty/jvm/org/ow2/asm:asm_util",
        ":jffi",
        ":jnr_x86asm"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "jnr_posix",
    exports = [
        "//external:jar/com/github/jnr/jnr_posix"
    ],
    runtime_deps = [
        ":jnr_constants",
        ":jnr_ffi"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "jnr_x86asm",
    exports = [
        "//external:jar/com/github/jnr/jnr_x86asm"
    ],
    visibility = [
        "//visibility:public"
    ]
)


