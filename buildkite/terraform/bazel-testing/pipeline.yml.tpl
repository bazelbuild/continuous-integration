---
steps:
  - command: |-
      curl -sS "https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)" -o bazelci.py
      python3.6 bazelci.py project_pipeline %{ for flag in flags ~} ${flag} %{ endfor ~} | buildkite-agent pipeline upload
    label: ":pipeline:"
    agents:
      - "queue=default"
    plugins:
      - docker#v3.8.0:
          always-pull: true
          environment:
            - "ANDROID_HOME"
            - "ANDROID_SDK_ROOT"
            - "ANDROID_NDK_HOME"
            - "BUILDKITE_ARTIFACT_UPLOAD_DESTINATION"
          image: "gcr.io/bazel-public/ubuntu1804-java11"
          network: "host"
          privileged: true
          propagate-environment: true
          propagate-uid-gid: true
          volumes:
            - "/etc/group:/etc/group:ro"
            - "/etc/passwd:/etc/passwd:ro"
            - "/opt:/opt:ro"
            - "/var/lib/buildkite-agent:/var/lib/buildkite-agent"
            - "/var/lib/gitmirrors:/var/lib/gitmirrors:ro"
            - "/var/run/docker.sock:/var/run/docker.sock"
