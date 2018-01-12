# Initializing Google Cloud for Bazel's CI

This document describes how to setup our Google Cloud project so that it can
host Bazel's Jenkins CI.

## Network

For CI we're using a normal 'auto' mode network:

```bash
gcloud compute networks create "default"
```

We'll also need a static IP address for Jenkins:

```bash
gcloud compute addresses create "ci"
```

## `/volumes` disk

The Jenkins controller is connected to a persistent disk. This disk is
encrypted, and it is not erased between builds nor after Jenkins restarts.

Let's create one:

```bash
gcloud compute disks create "jenkins-volumes" --size=4TB
```

This disk is mounted under `/volumes` on the Jenkins controller and has two
subdirectories:

*   `/volumes/secrets`: stores credentials needed for CI
*   `/volumes/jenkins_home`: stores permanent files for the Jenkins controller,
    to keep history (logs and build artifacts) even after reimaging the
    controller

## Populating the `/volumes/secrets` directory

`/volumes/secrets` directory is filled with RSA keys, authentication tokens, and
passwords. Each file refers to one particular secret, some of which have
corresponding placeholders in the `//jenkins/config/secrets/*.xml` files.

The secrets are:

*   `google.oauth.clientid` and `google.oauth.secret`: OAuth authentication
    token to the Google Cloud APIs.

    To regenerate:

    1.  Go to the Cloud Console:
        https://console.cloud.google.com/apis/credentials?project=bazel-public

    2.  Click on "Create credentials" > "OAuth client ID".

        ```text
        Application type: Web application
        Name: Jenkins
        Authorized redirect URIs: https://ci.bazel.build/securityRealm/finishLogin
        ```

    3.  Click create, copy the resulting Client ID and Client secret into the
        two files in `/volumes/secrets`, without a newline at the end:

        ```sh
        echo -n '<client id>' > google.oauth.clientid
        echo -n '<client secret>' > google.oauth.secret
        ```

*   `gerritcookies`: the Git cookies file for the CI user on Gerrit

    You can fetch this from
    https://bazel-review.googlesource.com/#/settings/http-password.

*   `github.bazel-io.jenkins.password`: the password for the CI user on Github

    To regenerate:

    1.  Run the local, testing instance of Jenkins:

        ```sh
        bazel run //jenkins/test [-- -p <port>]
        ```

        This deploys some Docker images on your local machine and starts a
        testing Jenkins instance, by default on port 8080.

    2.  Wait for the server to start on `localhost:8080`
    3.  Click "Manage Jenkins" > "Manage Credentials".
    4.  Enter the password for the GitHub account
    5.  Click on "Save".

        This updates `/var/jenkins_home/credentials.xml` inside
        the local Docker container with the secret.

    6.  Find the container's ID and open an interactive terminal in it:

        ```sh
        docker ps | grep "jenkins-test"
        docker exec -t -i <container ID> bash
        ```

    7.  In the interactive terminal, grep the transformed password:

        ```sh
        # inside jenkins@<container ID>
        cat /var/jenkins_home/credentials.xml | grep password
        ```

    8.  Copy the value of the `<password>` tag and write it to
        `/volumes/secrets/github.bazel-io.jenkins.password`.

*   `boto_config`: a boto config file with oauth token to access GCS

*   `github_id.rsa` and `github_id_rsa.pub`: private and public SSH keys for
    pushing to GitHub

    The Jenkins job pushes to GitHub to sync the Gerrit and GitHub
    repositories.

    To regenerate:

    1.  SSH into the Jenkins controller
    2.  Run:

        ```sh
        ssh-keygen -t rsa -b 4096 -C "noreply@bazel.build" -N '' -f /volumes/secrets/github_id_rsa
        ```

    You must add the public key to the list of deploy keys of all repositories
    to sync (e.g. for Bazel at `https://github.com/bazelbuild/bazel/settings/keys`).

*   `github_token`: the "Bazel Release Token" of the "Personal access tokens"
    of the "ci.bazel" user on GitHub

    The Jenkins controller uses this token to push Bazel releases to GitHub.

    You can't see the token itself, but you can update it and then GitHub
    shows you the new value.

*   `github_trigger_auth_token`: the "Jenkins GitHub Pull Request Builder" of
    the "Personal access tokens" of the "ci.bazel" user on GitHub

    The Jenkins controller uses this token to post comments on GitHub pull
    requests, e.g. "All tests passed".

    You can't see the token itself, but you can update it and then GitHub
    shows you the new value.

*   `apt-key.id` and `apt-key.sec.gpg`: GPG key to sign the Debian packages

*   `smtp.auth.password` and `smtp.auth.username`: authentication information
    for the mail provider.

    We use bazel.build's G Suite to send e-mails.

## Next

You can now use the [`vm.sh` script to create the virtual machines and the
`setup_mac.sh` script to setup mac nodes](machines.md).
