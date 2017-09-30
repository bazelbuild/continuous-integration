java_library(
    name = "json_lib",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_kohsuke_stapler_json_lib//jar",
    ],
    runtime_deps = [
        "//3rdparty/jvm/net/sf/ezmorph",
    ],
)

java_library(
    name = "stapler",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_kohsuke_stapler_stapler//jar",
    ],
    runtime_deps = [
        "//3rdparty/jvm/commons_discovery",
        "//3rdparty/jvm/javax/annotation:javax_annotation_api",
        "//3rdparty/jvm/org/jvnet:tiger_types",
    ],
)

java_library(
    name = "stapler_adjunct_codemirror",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_kohsuke_stapler_stapler_adjunct_codemirror//jar",
    ],
)

java_library(
    name = "stapler_adjunct_timeline",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_kohsuke_stapler_stapler_adjunct_timeline//jar",
    ],
)

java_library(
    name = "stapler_adjunct_zeroclipboard",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_kohsuke_stapler_stapler_adjunct_zeroclipboard//jar",
    ],
)

java_library(
    name = "stapler_groovy",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_kohsuke_stapler_stapler_groovy//jar",
    ],
    runtime_deps = [
        ":stapler_jelly",
    ],
)

java_library(
    name = "stapler_jelly",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_kohsuke_stapler_stapler_jelly//jar",
    ],
    runtime_deps = [
        "//3rdparty/jvm/org/jenkins_ci:commons_jelly",
        "//3rdparty/jvm/org/jenkins_ci/dom4j",
    ],
)

java_library(
    name = "stapler_jrebel",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_kohsuke_stapler_stapler_jrebel//jar",
    ],
    runtime_deps = [
        ":stapler",
    ],
)
