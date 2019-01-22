import os

CLOUD_PROJECT = (
    "bazel-public"
    if os.environ.get("BUILDKITE_ORGANIZATION_SLUG") == "bazel-trusted"
    else "bazel-untrusted"
)

DOWNSTREAM_PROJECTS = {
    "Android Testing": {
        "git_repository": "https://github.com/googlesamples/android-testing.git",
        "http_config": "https://raw.githubusercontent.com/googlesamples/android-testing/master/bazelci/buildkite-pipeline.yml",
        "pipeline_slug": "android-testing",
    },
    "Bazel": {
        "git_repository": "https://github.com/bazelbuild/bazel.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel/master/.bazelci/postsubmit.yml",
        "pipeline_slug": "bazel-bazel",
    },
    "Bazel Remote Execution": {
        "git_repository": "https://github.com/bazelbuild/bazel.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/bazel-remote-execution-postsubmit.yml",
        "pipeline_slug": "remote-execution",
    },
    "Bazel Watcher": {
        "git_repository": "https://github.com/bazelbuild/bazel-watcher.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-watcher/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-watcher",
    },
    "BUILD_file_generator": {
        "git_repository": "https://github.com/bazelbuild/BUILD_file_generator.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/BUILD_file_generator/master/.bazelci/presubmit.yml",
        "pipeline_slug": "build-file-generator",
    },
    "bazel-toolchains": {
        "git_repository": "https://github.com/bazelbuild/bazel-toolchains.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-toolchains/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-toolchains",
    },
    "bazel-skylib": {
        "git_repository": "https://github.com/bazelbuild/bazel-skylib.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/bazel-skylib/master/.bazelci/presubmit.yml",
        "pipeline_slug": "bazel-skylib",
    },
    "buildtools": {
        "git_repository": "https://github.com/bazelbuild/buildtools.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/buildtools/master/.bazelci/presubmit.yml",
        "pipeline_slug": "buildtools",
    },
    "CLion Plugin": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/clion-postsubmit.yml",
        "pipeline_slug": "clion-plugin",
    },
    "Gerrit": {
        "git_repository": "https://gerrit.googlesource.com/gerrit.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/gerrit-postsubmit.yml",
        "pipeline_slug": "gerrit",
    },
    "Google Logging": {
        "git_repository": "https://github.com/google/glog.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/glog-postsubmit.yml",
        "pipeline_slug": "google-logging",
    },
    "IntelliJ Plugin": {
        "git_repository": "https://github.com/bazelbuild/intellij.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/intellij-postsubmit.yml",
        "pipeline_slug": "intellij-plugin",
    },
    "migration-tooling": {
        "git_repository": "https://github.com/bazelbuild/migration-tooling.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/migration-tooling/master/.bazelci/presubmit.yml",
        "pipeline_slug": "migration-tooling",
    },
    "protobuf": {
        "git_repository": "https://github.com/google/protobuf.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/protobuf-postsubmit.yml",
        "pipeline_slug": "protobuf",
    },
    "re2": {
        "git_repository": "https://github.com/google/re2.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/re2-postsubmit.yml",
        "pipeline_slug": "re2",
    },
    "rules_appengine": {
        "git_repository": "https://github.com/bazelbuild/rules_appengine.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_appengine/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-appengine-appengine",
    },
    "rules_apple": {
        "git_repository": "https://github.com/bazelbuild/rules_apple.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_apple/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-apple-darwin",
    },
    "rules_closure": {
        "git_repository": "https://github.com/bazelbuild/rules_closure.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_closure/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-closure-closure-compiler",
    },
    "rules_d": {
        "git_repository": "https://github.com/bazelbuild/rules_d.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_d/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-d",
    },
    "rules_docker": {
        "git_repository": "https://github.com/bazelbuild/rules_docker.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_docker/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-docker-docker",
    },
    "rules_foreign_cc": {
        "git_repository": "https://github.com/bazelbuild/rules_foreign_cc.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_foreign_cc/master/.bazelci/config.yaml",
        "pipeline_slug": "rules-foreign-cc",
    },
    "rules_go": {
        "git_repository": "https://github.com/bazelbuild/rules_go.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_go/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-go-golang",
    },
    "rules_groovy": {
        "git_repository": "https://github.com/bazelbuild/rules_groovy.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_groovy/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-groovy",
    },
    "rules_gwt": {
        "git_repository": "https://github.com/bazelbuild/rules_gwt.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_gwt/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-gwt",
    },
    "rules_jsonnet": {
        "git_repository": "https://github.com/bazelbuild/rules_jsonnet.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_jsonnet/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-jsonnet",
    },
    "rules_kotlin": {
        "git_repository": "https://github.com/bazelbuild/rules_kotlin.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_kotlin/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-kotlin-kotlin",
    },
    "rules_k8s": {
        "git_repository": "https://github.com/bazelbuild/rules_k8s.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_k8s/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-k8s-k8s",
    },
    "rules_nodejs": {
        "git_repository": "https://github.com/bazelbuild/rules_nodejs.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_nodejs/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-nodejs-nodejs",
    },
    "rules_perl": {
        "git_repository": "https://github.com/bazelbuild/rules_perl.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_perl/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-perl",
    },
    "rules_python": {
        "git_repository": "https://github.com/bazelbuild/rules_python.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_python/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-python-python",
    },
    "rules_rust": {
        "git_repository": "https://github.com/bazelbuild/rules_rust.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_rust/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-rust-rustlang",
    },
    "rules_sass": {
        "git_repository": "https://github.com/bazelbuild/rules_sass.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_sass/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-sass",
    },
    "rules_scala": {
        "git_repository": "https://github.com/bazelbuild/rules_scala.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_scala/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-scala-scala",
    },
    "rules_typescript": {
        "git_repository": "https://github.com/bazelbuild/rules_typescript.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_typescript/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-typescript-typescript",
    },
    "rules_webtesting": {
        "git_repository": "https://github.com/bazelbuild/rules_webtesting.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/rules_webtesting/master/.bazelci/presubmit.yml",
        "pipeline_slug": "rules-webtesting-saucelabs",
    },
    "skydoc": {
        "git_repository": "https://github.com/bazelbuild/skydoc.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/skydoc/master/.bazelci/presubmit.yml",
        "pipeline_slug": "skydoc",
    },
    "subpar": {
        "git_repository": "https://github.com/google/subpar.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/subpar-postsubmit.yml",
        "pipeline_slug": "subpar",
    },
    "TensorFlow": {
        "git_repository": "https://github.com/tensorflow/tensorflow.git",
        "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/tensorflow-postsubmit.yml",
        "pipeline_slug": "tensorflow",
    },
}

# A map containing all supported platform names as keys, with the values being
# the platform name in a human readable format, and a the buildkite-agent's
# working directory.
PLATFORMS = {
    "ubuntu1404": {
        "name": "Ubuntu 14.04, JDK 8",
        "emoji-name": ":ubuntu: 14.04 (JDK 8)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": True,
        "java": "8",
        "docker-image": f"gcr.io/{CLOUD_PROJECT}/ubuntu1404:java8",
    },
    "ubuntu1604": {
        "name": "Ubuntu 16.04, JDK 8",
        "emoji-name": ":ubuntu: 16.04 (JDK 8)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": False,
        "java": "8",
        "docker-image": f"gcr.io/{CLOUD_PROJECT}/ubuntu1604:java8",
    },
    "ubuntu1804": {
        "name": "Ubuntu 18.04, JDK 8",
        "emoji-name": ":ubuntu: 18.04 (JDK 8)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": False,
        "java": "8",
        "docker-image": f"gcr.io/{CLOUD_PROJECT}/ubuntu1804:java8",
    },
    "ubuntu1804_nojava": {
        "name": "Ubuntu 18.04, no JDK",
        "emoji-name": ":ubuntu: 18.04 (no JDK)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": False,
        "java": "no",
        "docker-image": f"gcr.io/{CLOUD_PROJECT}/ubuntu1804:nojava",
    },
    "ubuntu1804_java9": {
        "name": "Ubuntu 18.04, JDK 9",
        "emoji-name": ":ubuntu: 18.04 (JDK 9)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": False,
        "java": "9",
        "docker-image": f"gcr.io/{CLOUD_PROJECT}/ubuntu1804:java9",
    },
    "ubuntu1804_java10": {
        "name": "Ubuntu 18.04, JDK 10",
        "emoji-name": ":ubuntu: 18.04 (JDK 10)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": False,
        "java": "10",
        "docker-image": f"gcr.io/{CLOUD_PROJECT}/ubuntu1804:java10",
    },
    "ubuntu1804_java11": {
        "name": "Ubuntu 18.04, JDK 11",
        "emoji-name": ":ubuntu: 18.04 (JDK 11)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": False,
        "java": "11",
        "docker-image": f"gcr.io/{CLOUD_PROJECT}/ubuntu1804:java11",
    },
    "macos": {
        "name": "macOS, JDK 8",
        "emoji-name": ":darwin: (JDK 8)",
        "agent-directory": "/Users/buildkite/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": True,
        "java": "8",
    },
    "windows": {
        "name": "Windows, JDK 8",
        "emoji-name": ":windows: (JDK 8)",
        "agent-directory": "d:/b/${BUILDKITE_AGENT_NAME}",
        "publish_binary": True,
        "java": "8",
    },
    "rbe_ubuntu1604": {
        "name": "RBE (Ubuntu 16.04, JDK 8)",
        "emoji-name": ":gcloud: (JDK 8)",
        "agent-directory": "/var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}",
        "publish_binary": False,
        "host-platform": "ubuntu1604",
        "java": "8",
        "docker-image": f"gcr.io/{CLOUD_PROJECT}/ubuntu1604:java8",
    },
}
