load("//jenkins:jenkins.bzl", "jenkins_job", "bazel_github_job", "bazel_git_job")
load(
    ":jobs.bzl",
    "LINUX_PLATFORMS",
    "UNIX_PLATFORMS",
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

[jenkins_job(
    name = job,
    config = "jobs-%s.xml.tpl" % job,
    platforms = BAZEL_JOBS[job],
    project_url = "http://bazel.io",
    substitutions = JOBS_SUBSTITUTIONS,
    deps = glob(["%s.*.tpl" % job]),
) for job in BAZEL_JOBS.keys()]

# TODO(dmarting): activate Tensorflow on mac (missing dependencies)
bazel_github_job(
    name = "TensorFlow",
    build_opts = ["-c opt"],
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
    configure = ["(cd tensorflow && ./tensorflow/tools/ci_build/builds/configured CPU)"],
    org = "tensorflow",
    platforms = LINUX_PLATFORMS,
    project = "serving",
    targets = [],
    tests = ["tensorflow_serving/..."],
)

bazel_github_job(
    name = "tf_models_syntaxnet",
    configure = ["(cd tensorflow && ./tensorflow/tools/ci_build/builds/configured CPU)"],
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
    configure = ["""
# Gerrit needs nodejs to be installed on the platform
if [[ "${PLATFORM_NAME}" =~ .*darwin.* ]]; then
  node_dir="node-v6.9.1-darwin-x64"
else
  node_dir="node-v6.9.1-linux-x64"
fi
if [ ! -d "${HOME}/node" ]; then
  mkdir -p "${HOME}/node"
  (cd "${HOME}/node" && curl "https://nodejs.org/dist/v6.9.1/${node_dir}.tar.gz" | tar zx)
fi
export PATH="${HOME}/node/${node_dir}/bin:${PATH}"
# This is because bazel 0.4 has a bug, normally --action_env=PATH should be enough.
# TODO(dmarting): Remove when bazel 0.4.1 get released.
cat >>${ROOT}/bazel.bazelrc <<EOF
build --action_env=PATH=${PATH}
EOF
"""],
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
    enable_trigger = False,
    org = "bazelbuild",
    platforms = ["docker"],
    pr_enabled = False,  # Do not vet PR because those tests are slow.
    project = "bazel",
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
    configure = [
        "source scripts/ci/build.sh",
        "setup_android_repositories",
    ],
    enable_trigger = False,
    gerrit_project = "bazel",
    org = "bazelbuild",
    platforms = ALL_PLATFORMS,
    project = "bazel",
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
    ],
    windows_targets = [
        "//src:bazel",
    ],
    windows_targets_msys = [
    ],
    windows_tests = [
        "//src/test/java/...",
        "//src/test/cpp/...",
        "//src/test/native:all_tests",
        # TODO(pcloudy): Re-enable this test when 0.5 is released.
        #"//src/test/shell/bazel:bazel_bootstrap_distfile_test",
    ],
    windows_tests_msys = [
        "//src/test/shell/bazel:bazel_windows_example_test",
    ],
)

bazel_github_job(
    name = "buildifier",
    org = "bazelbuild",
    # Repository was renamed
    project = "buildtools",
    platforms = UNIX_PLATFORMS,
    targets = [],
    tests = [":tests"],
)

bazel_github_job(
    name = "rules_scala",
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
    targets = ["//test/..."],
    tests = ["//test/..."],
)

bazel_github_job(
    name = "rules_rust",
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

bazel_github_job(
    name = "rules_jsonnet",
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
    platforms = RULES[job],
) for job in RULES.keys()]

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
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
    project = "intellij",
    project_url = "https://ij.bazel.io",
    targets = ["clwb:clwb_bazel"],
    test_opts = ["--define=ij_product=clion-latest"],
    tests = [":clwb_tests"],
)

bazel_github_job(
    name = "dash",
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
)

[bazel_github_job(
    name = n,
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
    srcs = JOBS,
    visibility = ["//jenkins:__pkg__"],
)

filegroup(
    name = "staging-jobs",
    srcs = [j + "-staging" for j in STAGING_JOBS],
    visibility = ["//jenkins:__pkg__"],
)

filegroup(
    name = "test-jobs",
    # We include all test but the docker ones (they needs access to the docker server).
    srcs = [j + "-test" for j in JOBS if not "docker" in j],
    visibility = ["//jenkins:__pkg__"],
)
