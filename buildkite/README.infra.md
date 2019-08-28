## GCE Health Check

for project in bazel-public bazel-untrusted; do
    gcloud compute health-checks create http buildkite-check \
        --project $project \
        --port 8080 \
        --check-interval 30s \
        --healthy-threshold 1 \
        --timeout 10s \
        --unhealthy-threshold 3
done
