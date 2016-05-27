load("//jenkins:jenkins.bzl", "jenkins_job", "bazel_github_job")
load(":jobs.bzl", "LINUX_PLATFORMS", "UNIX_PLATFORMS", "RULES", "DISABLED_RULES", "BAZEL_JOBS", "JOBS", "JOBS_SUBSTITUTIONS")

[jenkins_job(
    name = job,
    config = "jobs-%s.xml.tpl" % job,
    platforms = BAZEL_JOBS[job],
    project_url = "http://bazel.io",
    substitutions = JOBS_SUBSTITUTIONS,
    deps = glob(["%s.sh.tpl" % job]),
) for job in BAZEL_JOBS.keys()]

# TODO(dmarting): activate Tensorflow on mac (missing dependencies)
bazel_github_job(
    name = "TensorFlow",
    build_opts = ["-c opt"],
    configure = ["./configure"],
    org = "tensorflow",
    platforms = LINUX_PLATFORMS,
    project_url = "https://tensorflow.org",
    targets = [],
    test_opts = [
        "--test_timeout=1800",
        "--test_output=errors",
    ],
    tests = ["filter(\":(lib|platform)_.*\", kind(test, //tensorflow/core:all))"],
)

bazel_github_job(
    name = "TensorFlow_Serving",
    configure = ["(cd tensorflow && ./configure)"],
    org = "tensorflow",
    platforms = LINUX_PLATFORMS,
    project = "serving",
    targets = [],
    tests = ["tensorflow_serving/..."],
)

bazel_github_job(
    name = "bazel-docker-tests",
    bazel_versions = [
        "HEAD",
        "latest",
    ],
    platforms = ["docker"],
    project = "bazel",
    org = "bazelbuild",
    enable_trigger = False,
    targets = [],
    tests = ["//tools/cpp/test/..."],
)

bazel_github_job(
    name = "continuous-integration",
    bazel_versions = [
        "HEAD",
        "latest",
    ],
    platforms = ["docker"],
    org = "bazelbuild",
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
    platforms = UNIX_PLATFORMS,
    project = "bazel",
    org = "bazelbuild",
    enable_trigger = False,
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
    name = "test-jobs",
    srcs = [j + "-test" for j in JOBS],
    visibility = ["//jenkins:__pkg__"],
)
