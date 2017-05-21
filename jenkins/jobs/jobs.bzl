LINUX_PLATFORMS = [
    "linux-x86_64",
    "ubuntu_16.04-x86_64",
]

BSD_PLATFORMS = ["freebsd-11", "freebsd-12"]

DARWIN_PLATFORMS = ["darwin-x86_64"]

WINDOWS_PLATFORMS = ["windows-x86_64"]

UNIX_PLATFORMS = LINUX_PLATFORMS + DARWIN_PLATFORMS

ALL_PLATFORMS = UNIX_PLATFORMS + WINDOWS_PLATFORMS

RULES = [
    "rules_appengine",
    "rules_closure",
    "rules_d",
    "rules_go",
    "rules_sass",
    "rules_gwt",
    "rules_groovy",
    "rules_perl",
    "rules_docker",
    # These are not really rules, but it is simpler to put here.
    "skydoc",
    "bazel-watcher",
]

DISABLED_RULES = []

GERRIT_JOBS = [
    "bazel-tests",
    "continuous-integration",
    "eclipse",
]

GITHUB_JOBS = [
    "TensorFlow",
    "TensorFlow_Serving",
    "tf_models_syntaxnet",
    "Tutorial",
    "re2",
    "protobuf",
    "gerrit",
    # rules_dotnet is disabled on Linux until bazelbuild/rules_dotnet#13 is fixed.
    "rules_dotnet",
    # rules_web was renamed to rules_webtesting, keep the legacy name
    # for the job to keep history but use the new project name.
    "rules_web",
    "intellij",
    "buildifier",
    "rules_jsonnet",
    "rules_rust",
    "rules_scala",
    "migration-tooling",
] + GERRIT_JOBS + RULES + DISABLED_RULES

NO_PR_JOBS = ["bazel-docker-tests"]

BAZEL_STAGING_JOBS = {
    "Bazel": ALL_PLATFORMS + BSD_PLATFORMS,
    "Github-Trigger": UNIX_PLATFORMS,
    "Global/pipeline": [],
    "CR/global-verifier": [],
    "Bazel-Install": [],
    "Bazel-Install-Trigger": [],
}

BAZEL_JOBS = BAZEL_STAGING_JOBS + {
    "Bazel-Release": UNIX_PLATFORMS,
    "Bazel-Release-Trigger": UNIX_PLATFORMS,
    "Bazel-Publish-Site": [],
    "Bazel-Benchmark": [],
    "Bazel-Push-Benchmark-Output": [],
}

JOBS = BAZEL_JOBS.keys() + GITHUB_JOBS + NO_PR_JOBS

JOBS_SUBSTITUTIONS = {
    "GITHUB_JOBS": ", ".join(GITHUB_JOBS + NO_PR_JOBS),
    "BAZEL_JOBS": ", ".join(BAZEL_JOBS.keys()),
    "IMPORTANT_JOBS": ", ".join(GITHUB_JOBS + NO_PR_JOBS + ["Bazel", "Bazel-Publish-Site", "Bazel-Install-Trigger"])
}

STAGING_GITHUB_JOBS = GERRIT_JOBS + ["TensorFlow", "Tutorial"]
STAGING_JOBS = BAZEL_STAGING_JOBS.keys() + STAGING_GITHUB_JOBS
STAGING_JOBS_SUBSTITUTIONS = {
    "GITHUB_JOBS": ", ".join(STAGING_GITHUB_JOBS),
    "BAZEL_JOBS": ", ".join(BAZEL_STAGING_JOBS.keys()),
    "IMPORTANT_JOBS": ", ".join(STAGING_GITHUB_JOBS + ["Bazel", "Bazel-Publish-Site", "Bazel-Install-Trigger"])
}
