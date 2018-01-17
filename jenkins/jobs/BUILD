load("//jenkins/build_defs:jenkins.bzl", "jenkins_job", "bazel_github_job", "bazel_git_job")
load(":jobs.bzl", "job_lists")
load("//jenkins/lib:def.bzl", "bazel_job_configuration_test")

# Tests
[bazel_job_configuration_test(
    name = s + "-test",
    configs = [s],
) for s in glob(["configs/*.json"])]

# Some common jobs
[jenkins_job(
    name = "bazel/" + job,
    config = "global/%s.xml.tpl" % job,
    deps = [
        ":configs/bootstrap.json",
    ],
) for job in [
    "nightly",
    "presubmit",
    "release",
]]

jenkins_job(
    name = "maintenance/install-bazel",
    config = "install-bazel.xml.tpl",
    deps = [":install-bazel.groovy"],
)

##
## list of projects
##

# Jobs from the tensorflow org
bazel_github_job(
    name = "TensorFlow",
    config = ":configs/tensorflow.json",
    org = "tensorflow",
    project = "tensorflow",
    project_url = "https://tensorflow.org",
)

bazel_github_job(
    name = "TensorFlow_Serving",
    config = ":configs/tensorflow_serving.json",
    org = "tensorflow",
    project = "serving",
)

bazel_github_job(
    name = "tf_models_syntaxnet",
    config = ":configs/tf_models_syntaxnet.json",
    org = "tensorflow",
    project = "models",
    workspace = "research/syntaxnet",
)

# Job for testing Gerrit
bazel_git_job(
    name = "gerrit",
    config = ":configs/gerrit.json",
    git_url = "https://gerrit.googlesource.com/gerrit",
    org = "GerritCodeReview",
    project = "gerrit",
    project_url = "https://www.gerritcodereview.com",
)

# Jobs from the bazelbuild org with customization
bazel_github_job(
    name = "Tutorial",
    config = ":configs/tutorial.json",
    project = "examples",
    workspace = "tutorial",
)

bazel_github_job(
    name = "bazel-slow-tests",
    config = ":configs/empty.json",
    git_url = "https://bazel.googlesource.com/bazel",
    pr_enabled = False,  # Do not vet PR because those tests are slow.
    project = "bazel",
    use_upstream_branch = True,
)

bazel_github_job(
    name = "eclipse",
    gerrit_project = "eclipse",
)

bazel_github_job(
    name = "continuous-integration",
    config = ":configs/continuous-integration.json",
    gerrit_project = "continuous-integration",
)

bazel_github_job(
    name = "bazel-tests-remote",
    config = ":configs/empty.json",
    gerrit_project = "bazel",
    git_url = "https://bazel.googlesource.com/bazel",
    pr_enabled = False,  # Do not vet PR because it seems to cancel bazel-tests.
    project = "bazel",
    use_upstream_branch = True,
)

bazel_github_job(
    name = "bazel-tests",
    config = ":configs/empty.json",
    gerrit_project = "bazel",
    git_url = "https://bazel.googlesource.com/bazel",
    project = "bazel",
    use_upstream_branch = True,
)

bazel_github_job(
    name = "buildifier",
    config = ":configs/buildifier.json",
    # Repository was renamed
    project = "buildtools",
)

bazel_github_job(
    name = "bazel-toolchains",
    config = ":configs/empty.json",
    gerrit_project = "bazel-toolchains",
    git_url = "https://bazel.googlesource.com/bazel-toolchains",
    project = "bazel-toolchains",
)

bazel_github_job(
    name = "rules_webtesting",
    config = ":configs/rules_webtesting.json",
    project = "rules_webtesting",
    run_sequential = True,
    sauce_enabled = True,
)

bazel_github_job(
    name = "intellij",
    config = ":configs/intellij.json",
    project = "intellij",
    project_url = "https://ij.bazel.build",
)

# Jobs from the bazelbuild org that have a specific config on continuous-integration
# side.
# TODO(dmarting): merge with the next list once we move those configuration file
# on the repository side.
[bazel_github_job(
    name = n,
    config = ":configs/%s.json" % n,
) for n in [
    "rules_dotnet",
    "rules_jsonnet",
    "rules_rust",
    "rules_scala",
]]

# Jobs from the bazelbuild org using the default configuration
[bazel_github_job(name = n) for n in [
    "bazel-watcher",
    "migration-tooling",
    "rules_appengine",
    "rules_closure",
    "rules_d",
    "rules_docker",
    "rules_go",
    "rules_perl",
    "rules_sass",
    "skydoc",
]]

# Jobs without tests
[bazel_github_job(
    name = n,
    config = ":configs/no-tests.json",
) for n in [
    "rules_groovy",
    "rules_gwt",
]]

# Jobs from the bazelbuild org using a dummy configuration
[bazel_github_job(
    name = n,
    config = ":configs/empty.json",
) for n in [
    "bazel-integration-testing",
    "BUILD_file_generator",
    "rules_apple",
    "rules_k8s",
    "rules_nodejs",
    "rules_python",
    "rules_typescript",
]]

# Jobs from the abseil org
[bazel_github_job(
    name = n,
    config = ":configs/empty.json",
    org = "abseil",
    poll = False,
) for n in [
    "abseil-cpp",
    "abseil-py",
]]

# Jobs from the google org
bazel_github_job(
    name = "glog",
    org = "google",
)

bazel_github_job(
    name = "re2",
    config = ":configs/re2.json",
    org = "google",
)

bazel_github_job(
    name = "protobuf",
    config = ":configs/protobuf.json",
    org = "google",
    poll = False,  # protobuf had added the robots
)

bazel_github_job(
    name = "subpar",
    org = "google",
    poll = False,
)

# End of project list
job_lists(visibility = ["//jenkins:__pkg__"])
