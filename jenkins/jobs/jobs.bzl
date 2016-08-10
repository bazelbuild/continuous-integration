LINUX_PLATFORMS = [
    "linux-x86_64",
    "ubuntu_15.10-x86_64",
]

DARWIN_PLATFORMS = ["darwin-x86_64"]

UNIX_PLATFORMS = LINUX_PLATFORMS + DARWIN_PLATFORMS

RULES = {
    "rules_appengine": UNIX_PLATFORMS,
    "rules_closure": UNIX_PLATFORMS,
    "rules_d": UNIX_PLATFORMS,
    # rules_dotnet is disabled on Linux until bazelbuild/rules_dotnet#13 is fixed.
    "rules_dotnet": DARWIN_PLATFORMS,
    "rules_go": UNIX_PLATFORMS,
    "rules_rust": UNIX_PLATFORMS,
    "rules_sass": UNIX_PLATFORMS,
    "rules_scala": UNIX_PLATFORMS,
    # These are not really rules, but it is simpler to put here.
    "skydoc": UNIX_PLATFORMS,
    "buildifier": UNIX_PLATFORMS,
}

DISABLED_RULES = []

GERRIT_JOBS = [
    "bazel-tests",
    "continuous-integration",
]

GITHUB_JOBS = [
    "TensorFlow",
    "TensorFlow_Serving",
    "re2",
    "protobuf",
    "dash",
] + GERRIT_JOBS + RULES.keys() + DISABLED_RULES

NO_PR_JOBS = ["bazel-docker-tests"]

BAZEL_JOBS = {
    "Bazel": UNIX_PLATFORMS + ["windows-x86_64"],
    "Bazel-Release": UNIX_PLATFORMS,
    "Bazel-Release-Trigger": UNIX_PLATFORMS,
    "Github-Trigger": UNIX_PLATFORMS,
    "Tutorial": UNIX_PLATFORMS,
    "Bazel-Install": [],
    "Bazel-Install-Trigger": [],
    "Bazel-Publish-Site": [],
}

JOBS = BAZEL_JOBS.keys() + GITHUB_JOBS + NO_PR_JOBS + [
    "PR-" + k for k in GITHUB_JOBS] + [
        "Gerrit-" + j for j in GERRIT_JOBS]

JOBS_SUBSTITUTIONS = {
    "GITHUB_JOBS": ", ".join(GITHUB_JOBS + NO_PR_JOBS),
    "BAZEL_JOBS": ", ".join(BAZEL_JOBS.keys()),
}

STAGING_JOBS = BAZEL_JOBS.keys()
