# Starting the VM that hosts the Docker container

```bash
gcloud compute instances delete \
    --project bazel-public \
    --zone us-central1-a \
    --quiet \
    buildkite-agent-metrics

gcloud compute instances create \
    --project bazel-public \
    --boot-disk-size 20GB \
    --machine-type n1-standard-1 \
    --network buildkite \
    --zone us-central1-a \
    --image-project=ubuntu-os-cloud \
    --image-family=ubuntu-1804-lts \
    --scopes cloud-platform \
    --service-account buildkite-agent-metrics@bazel-public.iam.gserviceaccount.com \
    --metadata-from-file=startup-script=start.sh \
    buildkite-agent-metrics
```

# About the service account

The service account used for the VM must have at least the following permissions:

- `Cloud KMS Decryption` for the Buildkite agent tokens.
- `Logging > Logs Writer` to write logs to Stackdriver Logging.
- `Monitoring > Monitoring Metric Writer` to write to the Stackdriver Metrics.
