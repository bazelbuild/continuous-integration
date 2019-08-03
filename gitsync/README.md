# Building the Docker container

```
$ docker build -t gcr.io/bazel-public/gitsync .
$ docker push gcr.io/bazel-public/gitsync
```

# Starting the VM that hosts the Docker container

```
$ gcloud compute instances delete --project bazel-public gitsync
$ gcloud compute instances create-with-container \
    --project bazel-public \
    --boot-disk-size 200GB \
    --container-image gcr.io/bazel-public/gitsync:latest \
    --machine-type n1-standard-2 \
    --zone us-central1-a \
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

You can view the Docker logs by navigating to the VM in GCE and then by either clicking on "Stackdriver logging" or ssh-ing into the machine and running `docker logs`.
