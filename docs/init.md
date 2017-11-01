# Initializing the Bazel CI

## Creating the project from scratch

This operation can be __very dangerous__:

*   it does not check for the disk existences
*   it can lead to formatting some disks

Only create the project from scratch if you know what you're doing.

### What to run

Run:

```
./gce/init.sh init <instance>
```

Where `<instance>` is `prod` or `staging`.

The command:

*   creates the `/volumes` disk
*   creates the GCP Network
*   sets up the GCP Firewall Rules

To regenerate the network rules:

```
./gce/init.sh firewall <instance>
```

Note: the Bazel CI's own firewall rules are managed automatically by GCP.

After this command, you can populate the `/volumes` disk of the Jenkins
controllers ("masters"). There's one controller for each `<instance>`, i.e.
there's a prod controller and a staging controller.

## `/volumes` disk

The Jenkins controller is connected to a persistent disk. This disk is
encrypted, and it is not erased between builds nor after Jenkins restarts.

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
        Name: Jenkins-staging
        Authorized redirect URIs: https://ci-staging.bazel.io/securityRealm/finishLogin
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
        bazel run //jenkins:test [-- -p <port>]
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
        ssh-keygen -t rsa -b 4096 -C "noreply@bazel.io" -N '' -f /volumes/secrets/github_id_rsa
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
    for the mail provider

    We use a jenkins-only identifier to send emails through
    [SendGrid](https://sendgrid.com).

## Next

You can now use the [`vm.sh` script to manipulate the Virtual Machines and
the `setup_mac.sh` script to setup mac nodes](machines.md).
