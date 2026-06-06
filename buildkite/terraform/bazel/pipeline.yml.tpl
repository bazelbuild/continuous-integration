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
    %{~ if try(steps.priority, null) != null ~}
    priority: ${steps.priority}
    %{~ endif ~}
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
          image: "${try(steps.image, "gcr.io/bazel-public/ubuntu2404")}"
          network: "host"
          privileged: true
          propagate-environment: true
          propagate-uid-gid: true
          volumes:
            - "/etc/group:/etc/group:ro"
            - "/etc/passwd:/etc/passwd:ro"
            - "/etc/shadow:/etc/shadow:ro"
            - "/opt/android-ndk-r15c:/opt/android-ndk-r15c:ro"
            - "/opt/android-ndk-r25b:/opt/android-ndk-r25b:ro"
            - "/opt/android-sdk-linux:/opt/android-sdk-linux:ro"
            - "/var/lib/buildkite-agent:/var/lib/buildkite-agent"
            - "/var/lib/gitmirrors:/var/lib/gitmirrors:ro"
            # The pipeline-upload bootstrap step only parses .bazelci/presubmit.yml
            # and uploads the generated steps; it never talks to Docker. Do not
            # bind-mount the host Docker socket here -- on the untrusted org this
            # step runs in the checkout of an external fork PR, and the socket is
            # equivalent to root on the host.
