#!/bin/bash

set -euxo pipefail

# Get all the Buildkite agent tokens.
mkdir -p /etc/buildkite-agent-metrics
cat > /etc/buildkite-agent-metrics/trusted <<EOF
BUILDKITE_AGENT_TOKEN=$(gsutil cat "gs://bazel-trusted-encrypted-secrets/buildkite-trusted-agent-token.enc" | \
    gcloud kms decrypt --project bazel-public --location global --keyring buildkite --key buildkite-trusted-agent-token --ciphertext-file - --plaintext-file -)
GCP_PROJECT=bazel-public
EOF
cat > /etc/buildkite-agent-metrics/testing <<EOF
BUILDKITE_AGENT_TOKEN=$(gsutil cat "gs://bazel-testing-encrypted-secrets/buildkite-testing-agent-token.enc" | \
    gcloud kms decrypt --project bazel-untrusted --location global --keyring buildkite --key buildkite-testing-agent-token --ciphertext-file - --plaintext-file -)
GCP_PROJECT=bazel-untrusted
EOF
cat > /etc/buildkite-agent-metrics/untrusted <<EOF
BUILDKITE_AGENT_TOKEN=$(gsutil cat "gs://bazel-untrusted-encrypted-secrets/buildkite-untrusted-agent-token.enc" | \
    gcloud kms decrypt --project bazel-untrusted --location global --keyring buildkite --key buildkite-untrusted-agent-token --ciphertext-file - --plaintext-file -)
GCP_PROJECT=bazel-untrusted
EOF

# Download the latest buildkite-agent-metrics release.
curl -fsSL -o /usr/local/bin/buildkite-agent-metrics \
    https://github.com/buildkite/buildkite-agent-metrics/releases/download/v5.1.0/buildkite-agent-metrics-linux-amd64
chmod +x /usr/local/bin/buildkite-agent-metrics

# Create systemd unit files for each service.
cat > /etc/systemd/system/buildkite-agent-metrics@.service <<'EOF'
[Unit]
Description=Buildkite Agent Metrics (%i)
After=network.target

[Service]
Type=exec
Restart=always
RestartSec=10
StartLimitIntervalSec=0
EnvironmentFile=/etc/buildkite-agent-metrics/%i
ExecStart=/usr/local/bin/buildkite-agent-metrics -token $BUILDKITE_AGENT_TOKEN -interval 30s -backend stackdriver -stackdriver-projectid $GCP_PROJECT

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start buildkite-agent-metrics@trusted.service
systemctl start buildkite-agent-metrics@testing.service
systemctl start buildkite-agent-metrics@untrusted.service
