---
steps:
  - command: |-
      curl -sS "https://raw.githubusercontent.com/bazelbuild/continuous-integration/testing/buildkite/bazelci.py?$(date +%s)" -o bazelci.py
      python3.6 bazelci.py %{ for flag in flags ~} ${flag} %{ endfor ~} | buildkite-agent pipeline upload
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
            - "/opt/android-ndk-r15c:/opt/android-ndk-r15c:ro"
            - "/opt/android-sdk-linux:/opt/android-sdk-linux:ro"
            - "/var/lib/buildkite-agent:/var/lib/buildkite-agent"
            - "/var/lib/gitmirrors:/var/lib/gitmirrors:ro"
