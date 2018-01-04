java_library(
    name = "workflow_api",
    exports = [
        "//external:jar/org/jenkins_ci/plugins/workflow/workflow_api"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "workflow_step_api",
    exports = [
        "//external:jar/org/jenkins_ci/plugins/workflow/workflow_step_api"
    ],
    runtime_deps = [
        "//3rdparty/jvm/org/jenkins_ci/plugins:structs"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "workflow_support",
    exports = [
        "//external:jar/org/jenkins_ci/plugins/workflow/workflow_support"
    ],
    runtime_deps = [
        "//3rdparty/jvm/org/jboss/marshalling:jboss_marshalling_river",
        "//3rdparty/jvm/org/jenkins_ci/plugins:scm_api",
        "//3rdparty/jvm/org/jenkins_ci/plugins:script_security",
        ":workflow_api",
        ":workflow_step_api"
    ],
    visibility = [
        "//visibility:public"
    ]
)


