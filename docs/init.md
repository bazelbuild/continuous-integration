# Creating the project from scratch

To create the project from scratch you can simply do `./gce/init.sh init prod`
(or `./gce/init.sh init staging` for the staging instance).

This operation can be __very dangerous__ (it does not check for the disk existences and
can lead to formatting some disk), so do not use unless really sure.

It will create the network and set-up the firewall rules correctly. If you needs to
regenerate those network rules, you can do `./gce/init.sh firewall prod` (respectively
`./gce/init.sh firewall staging` for the staging instance).

After this command, you can populate the `/volumes` drive of the Jenkins controllers.

# Volumes persistent disk

The Jenkins controller is connected to a persistent disk that is not erased between each build.
This disk is mounted under `/volumes` on the controller and has two folder:

* `secrets` for storing the various credentials needed for ci.
* `jenkins_home` store permanent files for the jenkins controller so we keep history
   even after reimaging the controller.

This drive is encrypted. It is created automatically by the `init.sh` script.

## Populating the secrets directory

   The`secrets` directory is filled with various RSA keys, authentication tokens,
   and passwords. Each file refers to one particular secret, some of which have
   corresponding placeholders in the `jenkins/config/secrets/*.xml` files.

   Currently the list of secrets is:

   * `google.oauth.clientid` and `google.oauth.secret`: OAuth authentication token
     to the Google Cloud APIs.

     Go to the Cloud Console:
     https://console.cloud.google.com/apis/credentials?project=bazel-public

     Click on "Create credentials" > "OAuth client ID".

     ```text
     Application type: Web application
     Name: Jenkins-staging
     Authorized redirect URIs: http://ci-staging.bazel.io/securityRealm/finishLogin
     ```

     Click create, copy the resulting Client ID and Client secret into the
     two files in the `secrets` directory, without a newline at the end:

     ```sh
     echo -n '<client id>' > google.oauth.clientid
     echo -n '<client secret>' > google.oauth.secret
     ```

   * `gerritcookies`: it is the git cookies file for the CI user on Gerrit,
     that can be fetched from
     https://bazel-review.googlesource.com/#/settings/http-password.

   * `github.bazel-io.jenkins.password`: the password for the CI user on Github.

      Run the local, testing instance of Jenkins:

      ```sh
      bazel run //jenkins:test [-- -p <port>]
      ```

      This deploys a couple of Docker images on your local machine and starts a
      testing Jenkins instance on port 8080 by default. Wait for the server to
      start on `localhost:8080` then click "Manage Jenkins" > "Manage
      Credentials". Enter the password for the github account, then
      click on "Save". This updates `/var/jenkins_home/credentials.xml` inside
      the local Docker container with the secret.

      Then find the container's ID and open an interactive terminal in it, then
      grep the transformed password:

      ```sh
      docker ps | grep "jenkins-test"
      ```

      ```sh
      docker exec -t -i <container ID> bash
      ```

      ```sh
      # inside jenkins@<container ID>
      cat /var/jenkins_home/credentials.xml | grep password
      ```

      Copy the value of the `<password>` tag and write it to
      `github.bazel-io.jenkins.password`.

   * `boto_config`: a boto config file with oauth token to access GCS.

   * `github_id.rsa` and `github_id_rsa.pub`

      Private and public SSH keys for pushing to github for syncing
      the gerrit repository and the GitHub repository. You can
      generate it by SSH into the node and typing
      `ssh-keygen -t rsa -b 4096 -C "noreply@bazel.io" -N ''
      -f /volumes/secrets/github_id_rsa`. You must add the public
      key to the list of deploy keys of all repositories to sync (i.e.,
      for Bazel at `https://github.com/bazelbuild/bazel/settings/keys`).

   * `github_token`

      The Jenkins controller uses this to push Bazel releases to GitHub.
      This is the "Bazel Release Token" of the "Personal access tokens" of the
      "ci.bazel" user on GitHub.

      You can't see the token itself, but you can update it and then GitHub
      shows you the new value.

   * `github_trigger_auth_token`

      The Jenkins controller uses this to post comments on GitHub pull
      requests, e.g. "All tests passed". This is the "Jenkins GitHub Pull
      Request Builder" of the "Personal access tokens" of the "ci.bazel" user on
      GitHub.

      You can't see the token itself, but you can update it and then GitHub
      shows you the new value.

   * `apt-key.id` and `apt-key.sec.gpg`: GPG key to sign the Debian packages.

   * `smtp.auth.password` and `smtp.auth.username`: authentication information
     for the mail provider. We currently use a jenkins-only identifier
     to send through [SendGrid](https://sendgrid.com)

# Next

You can now use the [`vm.sh` script to manipulate the Virtual Machines and
the `setup_mac.sh` script to setup mac nodes](machines.md).
