This is the container that runs on https://slack.bazel.build/.

To build it:

```
docker build \
    -f slack-bazel-build/docker/Dockerfile \
    --target bazel-slack-inviter-slackin \
    -t "gcr.io/bazel-public/bazel-slack-inviter-slackin" \
    slack-bazel-build/docker
```

To push it to GCR:

```
docker push "gcr.io/bazel-public/bazel-slack-inviter-slackin"
```

In case the new container isn't picked up or slack.bazel.build starts to throw errors, go to [Cloud Run](https://console.cloud.google.com/run/deploy/us-central1/bazel-slack-inviter-slackin?project=bazel-public) and deploy a new version. The default settings should work fine.
