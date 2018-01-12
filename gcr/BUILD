load(
    "@io_bazel_rules_docker//docker:docker.bzl",
    "docker_bundle",
)
load(
    "@io_bazel_rules_docker//contrib:push-all.bzl",
    "docker_push",
)

docker_bundle(
    name = "bundle",
    images = {
        "gcr.io/bazel-public/jenkins-master:latest": "//jenkins:jenkins",
        "gcr.io/bazel-public/deploy-slave:latest": "//jenkins:deploy.docker",
        "gcr.io/bazel-public/sync-gerrit-github:latest": "//gerrit-github-sync:gerrit-github-sync",
    },
)

docker_push(
    name = "deploy",
    bundle = ":bundle",
)
