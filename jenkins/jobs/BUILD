load("//jenkins:jenkins.bzl", "jenkins_job", "bazel_github_job")

LINUX_PLATFORMS = [
    "linux-x86_64",
    "ubuntu_15.10-x86_64",
]

DARWIN_PLATFORMS = ["darwin-x86_64"]

UNIX_PLATFORMS = LINUX_PLATFORMS + DARWIN_PLATFORMS

RULES = [
    "rules_appengine",
    "rules_closure",
    "rules_d",
    "rules_dotnet",
    "rules_go",
    "rules_rust",
    "rules_sass",
    "rules_scala",
    # This is not really a rule, but it is simpler to put here.
    "skydoc",
]

#
# Jobs
#
GITHUB_JOBS = [
    "TensorFlow",
    "TensorFlow_Serving",
    "re2",
    "protobuf",
    "dash",
] + RULES

BAZEL_JOBS = {
    "Bazel": UNIX_PLATFORMS + ["windows-x86_64"],
    "Bazel-Release": UNIX_PLATFORMS,
    "Bazel-Release-Trigger": UNIX_PLATFORMS,
    "Github-Trigger": UNIX_PLATFORMS,
    "Tutorial": UNIX_PLATFORMS,
}

JOBS = BAZEL_JOBS.keys() + GITHUB_JOBS

JOBS_SUBSTITUTIONS = {
    "BAZEL_JOBS": ", ".join(GITHUB_JOBS),
}

[jenkins_job(
    name = job,
    config = "jobs-%s.xml.tpl" % job,
    platforms = BAZEL_JOBS[job],
    project_url = "http://bazel.io",
    substitutions = JOBS_SUBSTITUTIONS,
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
    test_opts = ["--test_timeout=1800"],
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

[bazel_github_job(
    name = job,
    org = "bazelbuild",
    platforms = UNIX_PLATFORMS,
) for job in RULES]

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
