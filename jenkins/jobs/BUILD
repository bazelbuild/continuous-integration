load("//jenkins:jenkins.bzl", "jenkins_job", "bazel_github_job")
load(
    ":jobs.bzl",
    "LINUX_PLATFORMS",
    "UNIX_PLATFORMS",
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
    platforms = LINUX_PLATFORMS,
    project_url = "https://tensorflow.org",
    targets = ["//tensorflow/tools/pip_package:build_pip_package"],
    test_opts = [
        "--test_timeout=1800",
        "--test_output=errors",
    ],
    tests = ["filter(\":(lib|platform)_.*\", kind(test, //tensorflow/core:all))"],
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
    name = "Tutorial",
    configure = ["source ./ci/setup_android_repositories.sh"],
    org = "bazelbuild",
    platforms =  UNIX_PLATFORMS,
    project = "examples",
    targets = ["//:all"],
    tests = [],
    workspace = "tutorial",
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
    platforms = UNIX_PLATFORMS,
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
)

[bazel_github_job(
    name = job,
    org = "bazelbuild",
    platforms = RULES[job],
) for job in RULES.keys()]

[bazel_github_job(
    name = job,
    enabled = False,
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
) for job in DISABLED_RULES]

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
