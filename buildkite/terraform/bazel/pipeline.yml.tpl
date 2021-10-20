---%{ if length(envs) > 0 }
env:%{ for key, value in envs }
  ${key}: "${value}"%{ endfor ~}

%{ endif }
steps:
  - command: |-
%{ for command in steps.commands ~}
      ${command}
%{ endfor ~}
    label: "${try(steps.label, ":pipeline:")}"
    agents:
      - "queue=default"%{ if try(length(steps.artifact_paths), 0) > 0 }
    artifact_paths:%{ for artifact_path in steps.artifact_paths }
      - "${artifact_path}"%{ endfor }%{ endif }
    plugins:
      - docker#v3.8.0:
          always-pull: true
          environment:
            - "ANDROID_HOME"
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
            - "/etc/shadow:/etc/shadow:ro"
            - "/opt/android-ndk-r15c:/opt/android-ndk-r15c:ro"
            - "/opt/android-sdk-linux:/opt/android-sdk-linux:ro"
            - "/var/lib/buildkite-agent:/var/lib/buildkite-agent"
            - "/var/lib/gitmirrors:/var/lib/gitmirrors:ro"
            - "/var/run/docker.sock:/var/run/docker.sock"
