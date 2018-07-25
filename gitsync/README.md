# Building the Docker container

```
$ docker build -t gcr.io/bazel-public/gitsync .
$ docker push gcr.io/bazel-public/gitsync
```

# Starting the VM that hosts the Docker container

```
$ gcloud compute instances delete gitsync
$ gcloud beta compute instances create-with-container \
    --boot-disk-size 200GB \
    --container-image gcr.io/bazel-public/gitsync:latest \
    --machine-type n1-standard-1 \
    --network buildkite \
    --zone europe-west1-d \
    --image-project cos-cloud \
    --image-family cos-stable \
    --metadata cos-metrics-enabled=true \
    --scopes cloud-platform \
    --service-account gitsync@bazel-public.iam.gserviceaccount.com \
    gitsync
```

# About the service account

The service account used for the container must have at least the following
permissions:

- `Cloud KMS Decryption` for the gitcookies and SSH key files only.
- `Logging > Logs Writer` to write the Docker logs to Google Cloud Logging.

# Getting logs from the container

Print the logs of the last minute in an easily readable format:

```
$ gcloud logging read --freshness 1m \
    --format 'value(receiveTimestamp,jsonPayload.data)' \
    'logName="projects/bazel-public/logs/gcplogs-docker-driver" AND
    jsonPayload.instance.name="gitsync"' | tail -r
```
