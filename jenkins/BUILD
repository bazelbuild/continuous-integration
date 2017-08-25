# Copyright 2015 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

package(default_visibility = ["//jenkins:__subpackages__"])

# Configuration for our Jenkins instance
load("@io_bazel_rules_docker//docker:docker.bzl", "docker_build")
load("//jenkins/build_defs:jenkins.bzl", "jenkins_node", "jenkins_docker_build", "jenkins_job", "jenkins_nodes", "jenkins_node_names")

#
# Nodes
#

DARWIN_PREFIX = "darwin-x86_64"

DARWIN_COUNT = 8

WINDOWS_PREFIX = "windows-x86_64"

WINDOWS_COUNT = 4

UBUNTU_1404_PREFIX = "ubuntu_14.04-x86_64"

UBUNTU_1404_COUNT = 8

UBUNTU_1604_BENCHMARK_PREFIX = "ubuntu_16.04-x86_64-benchmark"

UBUNTU_1604_BENCHMARK_COUNT = 1

UBUNTU_1604_PREFIX = "ubuntu_16.04-x86_64"

UBUNTU_1604_COUNT = 8

UBUNTU_DOCKER_PREFIX = "ubuntu_15.10-x86_64-docker"

UBUNTU_DOCKER_COUNT = 4

FREEBSD_11_PREFIX = "freebsd-11"

FREEBSD_11_COUNT = 4

FREEBSD_12_PREFIX = "freebsd-12"

FREEBSD_12_COUNT = 4

# Physical machines
jenkins_nodes(
    DARWIN_PREFIX,
    DARWIN_COUNT,
    num_executors = 1,
    remote_fs = "/Users/ci",
)

# GCE machines
jenkins_nodes(
    WINDOWS_PREFIX,
    WINDOWS_COUNT,
    num_executors = 1,
    preference = 1,
    remote_fs = "c:\\jenkins",
)

jenkins_nodes(
    UBUNTU_1404_PREFIX,
    UBUNTU_1404_COUNT,
    labels = ["linux-x86_64"],
)

jenkins_nodes(
    UBUNTU_1604_BENCHMARK_PREFIX,
    UBUNTU_1604_BENCHMARK_COUNT,
    install_bazel = False,
    labels = ["benchmark"],
    mode = "EXCLUSIVE",
)

jenkins_nodes(
    UBUNTU_DOCKER_PREFIX,
    UBUNTU_DOCKER_COUNT,
    labels = ["docker"],
)

# Non-release nodes
jenkins_nodes(
    UBUNTU_1604_PREFIX,
    UBUNTU_1604_COUNT,
    labels = ["no-release"],
)

jenkins_nodes(
    FREEBSD_11_PREFIX,
    FREEBSD_11_COUNT,
    labels = ["no-release"],
)

jenkins_nodes(
    FREEBSD_12_PREFIX,
    FREEBSD_12_COUNT,
    labels = ["no-release"],
)

#
# A deploy slave used for release work and syncing
# our repositories.
#

# A little hack to remove path consideration
DEPLOY_FILES = [
    "hoedown",
    "github_release",
]

genrule(
    name = "deploy-files",
    srcs = ["@%s//file" % f for f in DEPLOY_FILES],
    outs = ["%s.tar.gz" % f for f in DEPLOY_FILES],
    cmd = "\n".join([
        "cp $(location @%s//file) $(location %s.tar.gz)" % (f, f)
        for f in DEPLOY_FILES
    ]),
)

docker_build(
    name = "deploy-base",
    base = "//base:ubuntu-wily-amd64-deploy",
    directory = "/opt/data",
    env = {
        # We have to put those files on some secrets volume.
        "BOTO_CONFIG": "/opt/secrets/boto_config",
        "GITHUB_TOKEN_FILE": "/opt/secrets/github_token",
        "GSUTIL": "/opt/data/gsutil/gsutil",
        "GITHUB_RELEASE": "/opt/data/github-release/github-release",
        "HOEDOWN": "/opt/data/hoedown/hoedown",
        "APT_GPG_KEY_PATH": "/opt/secrets/apt-key.sec.gpg",
        "APT_GPG_KEY_ID_FILE": "/opt/secrets/apt-key.id",
    },
    files = [":deploy-files"],
    volumes = ["/opt/secrets"],
)

docker_build(
    name = "deploy-full",
    base = ":deploy-base",
    directory = "/opt/run",
    files = ["setup-deploy.sh"],
)

jenkins_node(
    name = "deploy",
    docker_base = "deploy-full",
    num_executors = 2,
    visibility = ["//visibility:public"],
)

jenkins_node(
    name = "deploy-staging",
    docker_base = "deploy-full",
    labels = ["deploy"],
    num_executors = 2,
    visibility = ["//visibility:public"],
)

docker_build(
    name = "ubuntu-with-bazel-installer",
    base = "//base:ubuntu-wily-amd64-deploy",
    data_path = "/gce",
    directory = "/opt/run",
    files = ["//gce:bootstrap-bazel.sh"],
)

jenkins_node(
    name = "ubuntu-docker",
    docker_base = ":ubuntu-with-bazel-installer",
    labels = [
        "linux-x86_64",
        "install-bazel",
    ],
)

# Jenkins job for Gerrit vetting
jenkins_job(
    name = "maintenance/gerrit-verifier",
    config = "gerrit-verifier.xml.tpl",
    project_url = "https://bazel-review.googlesource.com",
    deps = ["gerrit-verifier.groovy"],
)

#
# Jenkins permissions
#

# Public permissions
PUBLIC_PERMS = [
    "Hudson.Read",  # Read the public dashboard
    "Item.Read",  # Read the result of a build
    "Item.Workspace",  # Read a job workspace
    "View.Read",  # Read views
    "Computer.Connect",  # Connect a new node, needed by the node themselves
]

# Permissions for @google.com emails
AUTHENTICATED_PERMS = PUBLIC_PERMS

# Permissions for admin users (Beware it is dangerous)
ADMIN_PERMS = AUTHENTICATED_PERMS + [
    "Item.Build",  # Launch a build
    "Item.Cancel",  # Cancel a build
    "Run.Delete",  # Delete one build's information
    "Run.Update",  # Run one build's information
    "View.Configure",  # Configure views
    "View.Create",  # Create a new view
    "View.Delete",  # Delete existing view
    # Dangerous area: touch to nodes
    "Computer.Disconnect",  # Disconnect a node, normally never needed
    "Computer.Configure",  # Configure a node, normally never needed
    "Computer.Delete",  # Delete a node, almost never needed
    "Computer.Build",  # Build on a node, needed for debugging
    # Very dangerous area, administer jenkins
    "Hudson.Administer",  # Only used for restarting jenkins.
]

PERMS_TEMPLATE = "<permission>hudson.model.%s:%s</permission>"

#
# Creates the permissions info
#
# This is a config file generated by the build.sh script.
load(":config.bzl", "ADMIN_USERS")

SECURITY_CONFIG = """
  <useSecurity>true</useSecurity>
  <authorizationStrategy class="hudson.security.GlobalMatrixAuthorizationStrategy">
    %s
  </authorizationStrategy>
  <securityRealm class="org.jenkinsci.plugins.googlelogin.GoogleOAuth2SecurityRealm" plugin="google-login@1.1">
    <clientId>##SECRET:google.oauth.clientid##</clientId>
    <clientSecret>##SECRET:google.oauth.secret##</clientSecret>
    <domain>google.com</domain>
  </securityRealm>
""" % "\n".join([
    PERMS_TEMPLATE % (perm, "anonymous")
    for perm in PUBLIC_PERMS
] + [
    PERMS_TEMPLATE % (perm, "authenticated")
    for perm in AUTHENTICATED_PERMS
] + [
    PERMS_TEMPLATE % (perm, user)
    for user in ADMIN_USERS
    for perm in ADMIN_PERMS
])

#
# Finally the Jenkins image
#
jenkins_docker_build(
    name = "jenkins",
    configs = [
                  ":deploy",
                  ":jenkins-common-configs",
                  ":config/org.jenkinsci.plugins.ghprb.GhprbTrigger.xml",
              ] + jenkins_node_names(DARWIN_PREFIX, DARWIN_COUNT) +
              jenkins_node_names(WINDOWS_PREFIX, WINDOWS_COUNT) +
              jenkins_node_names(UBUNTU_DOCKER_PREFIX, UBUNTU_DOCKER_COUNT) +
              jenkins_node_names(UBUNTU_1404_PREFIX, UBUNTU_1404_COUNT) +
              jenkins_node_names(UBUNTU_1604_BENCHMARK_PREFIX, UBUNTU_1604_BENCHMARK_COUNT) +
              jenkins_node_names(UBUNTU_1604_PREFIX, UBUNTU_1604_COUNT) +
              jenkins_node_names(FREEBSD_11_PREFIX, FREEBSD_11_COUNT) +
              jenkins_node_names(FREEBSD_12_PREFIX, FREEBSD_12_COUNT),
    jobs = [
        "//jenkins/jobs",
        ":maintenance/gerrit-verifier",
    ],
    substitutions = {
        "SECURITY_CONFIG": SECURITY_CONFIG,
        "PUBLIC_JENKINS_URL": "http://ci.bazel.io/",
    },
    tars = ["//jenkins/lib"],
    visibility = ["//visibility:public"],
)

jenkins_docker_build(
    name = "jenkins-staging",
    configs = [
        ":darwin-x86_64-staging",
        ":deploy-staging",
        ":freebsd-11-staging",
        ":freebsd-12-staging",
        ":jenkins-common-configs",
        ":ubuntu_14.04-x86_64-staging",
        ":ubuntu_15.10-x86_64-docker-staging",
        ":ubuntu_16.04-x86_64-staging",
        ":windows-x86_64-staging",
    ],
    jobs = [
        "//jenkins/jobs:staging-jobs",
        ":maintenance/gerrit-verifier/staging",
    ],
    substitutions = {
        "SECURITY_CONFIG": SECURITY_CONFIG,
        "PUBLIC_JENKINS_URL": "http://ci-staging.bazel.io/",
    },
    tars = ["//jenkins/lib"],
    visibility = ["//gcr:__pkg__"],
)

#
# A jenkins image for testing purpose
jenkins_docker_build(
    name = "jenkins-test",
    configs = [
        ":deploy",
        ":jenkins-common-configs",
        ":ubuntu-docker",
    ],
    jobs = [
        "//jenkins/jobs:test-jobs",
        ":maintenance/gerrit-verifier/test",
    ],
    substitutions = {
        "SECURITY_CONFIG": "<useSecurity>false</useSecurity>",
        "PUBLIC_JENKINS_URL": "##ENV:JENKINS_SERVER##",
    },
    tars = ["//jenkins/lib"],
)

filegroup(
    name = "jenkins-common-configs",
    srcs = glob(
        ["config/**"],
        exclude = ["config/org.jenkinsci.plugins.ghprb.GhprbTrigger.xml"],
    ),
)

alias(
    name = "test",
    actual = "//jenkins/test",
)
