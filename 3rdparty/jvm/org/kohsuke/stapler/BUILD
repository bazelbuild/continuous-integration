java_library(
    name = "json_lib",
    exports = [
        "//external:jar/org/kohsuke/stapler/json_lib"
    ],
    runtime_deps = [
        "//3rdparty/jvm/net/sf/ezmorph:ezmorph"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "stapler",
    exports = [
        "//external:jar/org/kohsuke/stapler/stapler"
    ],
    runtime_deps = [
        "//3rdparty/jvm/com/google/code/findbugs:jsr305",
        "//3rdparty/jvm/commons_discovery:commons_discovery",
        "//3rdparty/jvm/javax/annotation:javax_annotation_api",
        "//3rdparty/jvm/org/jvnet:tiger_types"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "stapler_adjunct_codemirror",
    exports = [
        "//external:jar/org/kohsuke/stapler/stapler_adjunct_codemirror"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "stapler_adjunct_timeline",
    exports = [
        "//external:jar/org/kohsuke/stapler/stapler_adjunct_timeline"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "stapler_adjunct_zeroclipboard",
    exports = [
        "//external:jar/org/kohsuke/stapler/stapler_adjunct_zeroclipboard"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "stapler_groovy",
    exports = [
        "//external:jar/org/kohsuke/stapler/stapler_groovy"
    ],
    runtime_deps = [
        ":stapler_jelly"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "stapler_jelly",
    exports = [
        "//external:jar/org/kohsuke/stapler/stapler_jelly"
    ],
    runtime_deps = [
        "//3rdparty/jvm/org/jenkins_ci/dom4j:dom4j",
        "//3rdparty/jvm/org/jenkins_ci:commons_jelly"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "stapler_jrebel",
    exports = [
        "//external:jar/org/kohsuke/stapler/stapler_jrebel"
    ],
    runtime_deps = [
        ":stapler"
    ],
    visibility = [
        "//visibility:public"
    ]
)


