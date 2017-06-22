load("//jenkins/build_defs:jenkins.bzl", "jenkins_job", "bazel_github_job", "bazel_git_job")
load(":jobs.bzl", "job_lists")
load("//jenkins/lib:def.bzl", "bazel_job_configuration_test")

# Tests
[bazel_job_configuration_test(
    name = s + "-test",
    configs = [s],
) for s in glob(["configs/*.json"])]

# Some common jobs
jenkins_job(
    name = "Github-Trigger",
    config = "jobs-Github-Trigger.xml.tpl",
    project_url = "http://bazel.io",
)

[jenkins_job(
    name = job,
    config = "jobs-%s.xml.tpl" % job,
    project_url = "http://bazel.io",
) for job in [
    "Bazel-Benchmark",
    "Bazel-Push-Benchmark-Output",
]]

jenkins_job(
    name = "Global/pipeline",
    config = "global.xml.tpl",
    deps = [
        ":configs/bootstrap.json",
        ":global.groovy",
    ],
)

jenkins_job(
    name = "CR/global-verifier",
    config = "CR-global.xml.tpl",
    deps = [
        ":configs/bootstrap.json",
        ":global.groovy",
    ],
)

jenkins_job(
    name = "install-bazel",
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
    workspace = "syntaxnet",
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
    name = "bazel-docker-tests",
    config = ":configs/bazel-docker-tests.json",
    enable_trigger = False,
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
    name = "bazel-tests",
    config = ":configs/bazel-tests.json",
    enable_trigger = False,
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

# rules_web was renamed to rules_webtesting, keep the legacy name
# for the job to keep history but use the new project name.
bazel_github_job(
    name = "rules_web",
    project = "rules_webtesting",
    run_sequential = True,
    sauce_enabled = True,
)

bazel_github_job(
    name = "intellij",
    config = ":configs/intellij.json",
    project = "intellij",
    project_url = "https://ij.bazel.io",
)

# Jobs from the bazelbuild org that have a specific config on continuous-integration
# side.
# TODO(dmarting): merge with the next list once we move those configuration file
# on the repository side.
[bazel_github_job(
    name = n,
    config = ":configs/%s.json" % n,
) for n in [
    "rules_scala",
    "rules_rust",
    "rules_dotnet",
    "rules_jsonnet",
    "rules_typescript",
]]

# Jobs from the bazelbuild org using the default configuration
[bazel_github_job(name = n) for n in [
    "rules_appengine",
    "rules_closure",
    "rules_d",
    "rules_go",
    "rules_sass",
    "rules_gwt",
    "rules_groovy",
    "rules_perl",
    "rules_docker",
    "skydoc",
    "bazel-watcher",
    "migration-tooling",
]]

# Jobs from the google org
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

# End of project list
job_lists(visibility = ["//jenkins:__pkg__"])
