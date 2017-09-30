java_library(
    name = "workflow_api",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_plugins_workflow_workflow_api//jar",
    ],
)

java_library(
    name = "workflow_step_api",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_plugins_workflow_workflow_step_api//jar",
    ],
    runtime_deps = [
        "//3rdparty/jvm/org/jenkins_ci/plugins:structs",
    ],
)

java_library(
    name = "workflow_support",
    visibility = [
        "//visibility:public",
    ],
    exports = [
        "@org_jenkins_ci_plugins_workflow_workflow_support//jar",
    ],
    runtime_deps = [
        ":workflow_api",
        ":workflow_step_api",
        "//3rdparty/jvm/org/jboss/marshalling:jboss_marshalling_river",
        "//3rdparty/jvm/org/jenkins_ci/plugins:script_security",
    ],
)
