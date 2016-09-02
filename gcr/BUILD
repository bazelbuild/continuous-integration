load(":docker_push.bzl", "docker_push")

docker_push(
    name = "deploy",
    images = {
        "//jenkins:jenkins": "jenkins-master",
        "//jenkins:deploy.docker": "deploy-slave",
        "//gerrit-github-sync:gerrit-github-sync": "sync-gerrit-github",
    },
    repository = "gcr.io/bazel-public",
)

docker_push(
    name = "deploy-staging",
    images = {
        "//jenkins:jenkins-staging": "jenkins-master-staging",
    },
    repository = "gcr.io/bazel-public",
)
