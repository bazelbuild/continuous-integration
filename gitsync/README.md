# Building the Docker container

```
$ docker build -t gcr.io/bazel-public/gitsync .
$ docker push gcr.io/bazel-public/gitsync
```

# Starting the VM that hosts the Docker container

```
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
