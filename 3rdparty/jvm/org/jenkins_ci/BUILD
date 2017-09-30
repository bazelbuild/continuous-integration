java_library(
    name = "annotation_indexer",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_annotation_indexer//jar",
    ],
)

java_library(
    name = "bytecode_compatibility_transformer",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_bytecode_compatibility_transformer//jar",
    ],
    runtime_deps = [
        "//3rdparty/jvm/org/kohsuke:asm5",
    ],
)

java_library(
    name = "commons_jelly",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_commons_jelly//jar",
    ],
)

java_library(
    name = "commons_jexl",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_commons_jexl//jar",
    ],
)

java_library(
    name = "constant_pool_scanner",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_constant_pool_scanner//jar",
    ],
)

java_library(
    name = "crypto_util",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_crypto_util//jar",
    ],
)

java_library(
    name = "jmdns",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_jmdns//jar",
    ],
)

java_library(
    name = "memory_monitor",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_memory_monitor//jar",
    ],
)

java_library(
    name = "symbol_annotation",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_symbol_annotation//jar",
    ],
    runtime_deps = [
        ":annotation_indexer",
    ],
)

java_library(
    name = "task_reactor",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_task_reactor//jar",
    ],
)

java_library(
    name = "trilead_ssh2",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_trilead_ssh2//jar",
    ],
    runtime_deps = [
        "//3rdparty/jvm/net/i2p/crypto:eddsa",
        "//3rdparty/jvm/org/connectbot/jbcrypt",
    ],
)

java_library(
    name = "version_number",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_version_number//jar",
    ],
)
