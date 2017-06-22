load("//jenkins/build_defs:jenkins.bzl", "jenkins_job", "bazel_github_job", "bazel_git_job")
load(
    ":jobs.bzl",
    "LINUX_PLATFORMS",
    "UNIX_PLATFORMS",
    "DARWIN_PLATFORMS",
    "WINDOWS_PLATFORMS",
    "WINDOWS_MSVC_PLATFORMS",
    "ALL_PLATFORMS",
    "RULES",
    "DISABLED_RULES",
    "BAZEL_JOBS",
    "JOBS",
    "JOBS_SUBSTITUTIONS",
    "STAGING_JOBS",
)
load("//jenkins/lib:def.bzl", "bazel_job_configuration_test")

[bazel_job_configuration_test(
    name = s + "-test",
    configs = [s],
) for s in glob(["configs/*.json"])]

[jenkins_job(
    name = job,
    config = "jobs-%s.xml.tpl" % job,
    platforms = BAZEL_JOBS[job],
    project_url = "http://bazel.io",
    substitutions = JOBS_SUBSTITUTIONS,
    deps = glob(["%s.*.tpl" % job]),
) for job in BAZEL_JOBS.keys() if job != "Global/pipeline"]

jenkins_job(
    name = "Global/pipeline",
    config = "global.xml.tpl",
    deps = [
        ":configs/bootstrap.json",
        ":global.groovy",
    ],
)

# TODO(dmarting): activate Tensorflow on mac (missing dependencies)
bazel_github_job(
    name = "TensorFlow",
    build_opts = ["-c opt"],
    config = ":configs/tensorflow.json",
    configure = ["./tensorflow/tools/ci_build/builds/configured CPU"],
    org = "tensorflow",
    platforms = LINUX_PLATFORMS + WINDOWS_PLATFORMS + WINDOWS_MSVC_PLATFORMS,
    project_url = "https://tensorflow.org",
    targets = ["//tensorflow/tools/pip_package:build_pip_package"],
    test_opts = [
        "--test_timeout=1800",
        "--test_output=errors",
    ],
    tests = ["filter(\":(lib|platform)_.*\", kind(test, //tensorflow/core:all))"],
    windows_configure = [
        # run.bat invokes msys bash to run the shell script for building TF,
        # But msys bash doesn't inherit PATH from cmd.exe, so we make bazel avaiable by
        # copying it to c:\\tools\\msys64\\usr\\bin\\bazel.exe
        "del c:\\tools\\msys64\\usr\\bin\\bazel.exe",
        "copy %BAZEL% c:\\tools\\msys64\\usr\\bin\\bazel.exe",
        ".\\tensorflow\\tools\\ci_build\\windows\\cpu\\pip\\run.bat",
    ],
    windows_targets = [],
    windows_tests = [],
)

bazel_github_job(
    name = "TensorFlow_Serving",
    config = ":configs/tensorflow_serving.json",
    configure = ["(cd tensorflow && ln -s ../.bazelrc && ./tensorflow/tools/ci_build/builds/configured CPU)"],
    org = "tensorflow",
    platforms = LINUX_PLATFORMS,
    project = "serving",
    targets = [],
    tests = ["tensorflow_serving/..."],
)

bazel_github_job(
    name = "tf_models_syntaxnet",
    config = ":configs/tf_models_syntaxnet.json",
    configure = ["(cd tensorflow && ln -s ../.bazelrc && ./tensorflow/tools/ci_build/builds/configured CPU)"],
    org = "tensorflow",
    platforms = LINUX_PLATFORMS,
    project = "models",
    targets = [],
    tests = [
        "syntaxnet/...",
        "util/utf8/...",
    ],
    workspace = "syntaxnet",
)

bazel_github_job(
    name = "Tutorial",
    config = ":configs/tutorial.json",
    configure = ["source ./ci/setup_android_repositories.sh"],
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
    project = "examples",
    targets = ["//:all"],
    tests = [],
    workspace = "tutorial",
)

bazel_git_job(
    name = "gerrit",
    config = ":configs/gerrit.json",
    git_url = "https://gerrit.googlesource.com/gerrit",
    org = "GerritCodeReview",
    platforms = UNIX_PLATFORMS,
    project = "gerrit",
    project_url = "https://www.gerritcodereview.com",
    targets = ["//:release"],
    tests = ["//..."],
)

bazel_github_job(
    name = "bazel-docker-tests",
    bazel_versions = [
        "HEAD",
        "latest",
    ],
    config = ":configs/bazel-docker-tests.json",
    enable_trigger = False,
    git_url = "https://bazel.googlesource.com/bazel",
    org = "bazelbuild",
    platforms = ["docker"],
    pr_enabled = False,  # Do not vet PR because those tests are slow.
    project = "bazel",
    substitutions = {"GLOBAL_USE_UPSTREAM_BRANCH": "True"},
    targets = [],
    tests = ["//tools/cpp/test/..."],
)

bazel_github_job(
    name = "eclipse",
    bazel_versions = [
        "HEAD",
        "latest",
    ],
    gerrit_project = "eclipse",
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
)

bazel_github_job(
    name = "continuous-integration",
    bazel_versions = [
        "HEAD",
        "latest",
    ],
    config = ":configs/continuous-integration.json",
    gerrit_project = "continuous-integration",
    org = "bazelbuild",
    platforms = ["docker"],
)

bazel_github_job(
    name = "bazel-tests",
    bazel_versions = [
        "HEAD",
        "HEAD-jdk7",
        "latest",
        "latest-jdk7",
    ],
    config = ":configs/bazel-tests.json",
    configure = [
        "source scripts/ci/build.sh",
        "setup_android_repositories",
    ],
    enable_trigger = False,
    gerrit_project = "bazel",
    git_url = "https://bazel.googlesource.com/bazel",
    org = "bazelbuild",
    platforms = ALL_PLATFORMS,
    project = "bazel",
    substitutions = {"GLOBAL_USE_UPSTREAM_BRANCH": "True"},
    targets = [],
    test_opts = [
        "-k",
        "--test_output=errors",
        "--build_tests_only",
    ],
    tests = [
        "//scripts/...",
        "//src/...",
        "//third_party/ijar/...",
        "//tools/android/...",
    ],
    windows_targets = [
        "//src:bazel",
    ],
    windows_targets_msys = [
    ],
    windows_tests = [
        "//src/test/py/...",
        "//src/test/java/...",
        "//src/test/cpp/...",
        "//src/test/native:all_tests",
        "//src/test/shell/bazel:bazel_bootstrap_distfile_test",
    ],
    windows_tests_msys = [
        "//src/test/shell/bazel:bazel_windows_example_test",
    ],
)

bazel_github_job(
    name = "buildifier",
    config = ":configs/buildifier.json",
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
    # Repository was renamed
    project = "buildtools",
    targets = [],
    tests = [":tests"],
)

bazel_github_job(
    name = "rules_scala",
    config = ":configs/rules_scala.json",
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
    targets = ["//test/..."],
    tests = ["//test/..."],
)

bazel_github_job(
    name = "rules_rust",
    config = ":configs/rules_rust.json",
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
    targets = [
        "//...",
        "@examples//...",
    ],
    tests = [
        "//...",
        "@examples//...",
    ],
)

# Special case rules_dotnet that runs only on darwin platforms
bazel_github_job(
    name = "rules_dotnet",
    config = ":configs/rules_dotnet.json",
    org = "bazelbuild",
    platforms = DARWIN_PLATFORMS,
)

bazel_github_job(
    name = "rules_jsonnet",
    config = ":configs/rules_jsonnet.json",
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
    targets = [
        "//...",
        "@examples//...",
    ],
    tests = [
        "//...",
        "@examples//...",
    ],
)

[bazel_github_job(
    name = job,
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
) for job in RULES]

# rules_web was renamed to rules_webtesting, keep the legacy name
# for the job to keep history but use the new project name.
bazel_github_job(
    name = "rules_web",
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
    project = "rules_webtesting",
    run_sequential = True,
    sauce_enabled = True,
)

[bazel_github_job(
    name = job,
    enabled = False,
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
) for job in DISABLED_RULES]

bazel_github_job(
    name = "intellij",
    build_opts = ["--define=ij_product=intellij-latest"],
    config = ":configs/intellij.json",
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
    project = "intellij",
    project_url = "https://ij.bazel.io",
    targets = ["ijwb:ijwb_bazel"],
    test_opts = ["--define=ij_product=intellij-latest"],
    tests = [":ijwb_tests"],
)

bazel_github_job(
    name = "intellij-android-studio",
    build_opts = ["--define=ij_product=android-studio-latest"],
    # All config of Intellij are tested by the intellij job now
    config = "",
    enabled = False,
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
    project = "intellij",
    project_url = "https://ij.bazel.io",
    targets = ["aswb:aswb_bazel"],
    test_opts = ["--define=ij_product=android-studio-latest"],
    tests = [":aswb_tests"],
)

bazel_github_job(
    name = "intellij-clion",
    build_opts = ["--define=ij_product=clion-latest"],
    # All config of Intellij are tested by the intellij job now
    config = "",
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
    project = "intellij",
    project_url = "https://ij.bazel.io",
    targets = ["clwb:clwb_bazel"],
    test_opts = ["--define=ij_product=clion-latest"],
    tests = [":clwb_tests"],
)

bazel_github_job(
    name = "migration-tooling",
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
)

[bazel_github_job(
    name = n,
    config = ":configs/%s.json" % n,
    org = "google",
    platforms = UNIX_PLATFORMS,
    # on Linux protobuf tries to build objc target so filter by test only
    targets = [],
    tests = [":all"],
) for n in [
    "re2",
    "protobuf",
]]

filegroup(
    name = "jobs",
    srcs = ["%s/all" % j for j in JOBS],
    visibility = ["//jenkins:__pkg__"],
)

filegroup(
    name = "staging-jobs",
    srcs = ["%s/staging" % j for j in STAGING_JOBS],
    visibility = ["//jenkins:__pkg__"],
)

filegroup(
    name = "test-jobs",
    # We include all test but the docker ones (they needs access to the docker server).
    srcs = ["%s/test" % j for j in JOBS if not "docker" in j],
    visibility = ["//jenkins:__pkg__"],
)
