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

# Configuration for our Jenkins instance
load("/tools/build_defs/docker/docker", "docker_build")
load("jenkins", "jenkins_job", "jenkins_node", "jenkins_build")

#
# Common definitions
#

# TODO(dmarting): this is a repeat of what appears in the WORKSPACE file,
# skylark remote repositories should make possible to factor that.
JENKINS_PLUGINS = [
    [
        "conditional-buildstep",
        "1.3.3",
        "1bc0999a164ec666779fa604dd4018ab812c1ffa2cac1b69da9dbd9584973b5c",
    ],
    [
        "javadoc",
        "1.3",
        "cd2efb569827d66565483eec00877b0897941aee8334ad945c310d7b3b5815af",
    ],
    [
        "scm-api",
        "0.2",
        "cc856d8dc8b951cf9a195baa2bf7bbff0d12368534a6b973e43e2909141eff3f",
    ],
    [
        "ssh-credentials",
        "1.11",
        "e80f36af0162794d80164ae479d7cc36077174f50d57d04f2d814b4bbe4eab18",
    ],
    [
        "parameterized-trigger",
        "2.27",
        "81fc5111dd2c62a6a87d6e4234fabad0ebac4ef053357e8fb89be357feb38a0a",
    ],
    [
        "copyartifact",
        "1.35.2",
        "0d0143318487ffa61d6c159a0157dcdcbf66a71e3aa17eb4bac7707fc6ae512a",
    ],
    [
        "mailer",
        "1.15",
        "1633a780e8ffd8bc3deea0892253587ace67aec76bfc6933c392116095d9a6f5",
    ],
    [
        "run-condition",
        "1.0",
        "4e55ebf4bde1202784404d856f98f7de85470ed145cde06feb45f641891780fb",
    ],
    [
        "script-security",
        "1.13",
        "3bc90fb65369d47c89f67fd55dac55f8c5da27da4fdccf6c234aab39ebbd5d4c",
    ],
    [
        "matrix-project",
        "1.6",
        "3c6fd1c5807f197fe7649449661b2c1a103efb1f88c39fc330391e7d372877dd",
    ],
    [
        "junit",
        "1.2",
        "3d288600ab6a5d8117d427813c7693a1ccbe7a0ccd6a58b536e896471c3378dc",
    ],
    [
        "credentials",
        "1.22",
        "5b5529ecc40121863aadb94b7bd066a682ba817a351deaec4cdf40a1715330c6",
    ],
    [
        "git-parameter",
        "0.4.0",
        "4450c2bdb4e161e6fb25515439254f702054994401c92367f26ad6821e418899",
    ],
    [
        "github-api",
        "1.67",
        "bd9d0af9d3cd43db7dbff5d4f2fc79036771bab0fa33624ff78227b76101ad01",
    ],
    [
        "git-client",
        "1.18.0",
        "2179d7a4e9dacd707cec9c4475b08f5c0285c3e02e80a58ff4f6a132a3641b4d",
    ],
    [
        "github",
        "1.12.0",
        "f880fb8085070eee7277d50fe9afeb39a7b6bae00ecd502b8aa692f9b5068a55",
    ],
    [
        "maven-plugin",
        "2.10",
        "ad227ae45f68608795958fad758d1e062862169ab91671f6efd4f9b89935c3c8",
    ],
    [
        "git",
        "2.4.0",
        "742bb27aee23c43f0371340fe5e2a389db64805747718573ef3ab3c84f17ed62",
    ],
    [
        "token-macro",
        "1.10",
        "bf4fe99beb72044242260336ffcd8fe4632eb897b60eba5483690ddf56dc83dc",
    ],
    [
        "nodelabelparameter",
        "1.5.1",
        "ec9a56993e16bdcc37d592bed0cb48ed8f3231ef46569632061fe066fdd2b7ed",
    ],
    [
        "jquery",
        "1.11.2-0",
        "acf4940bd5a0d918d781b51a6f42f7a0cb9381ede8235582c629a5d347495029",
    ],
    [
        "email-ext",
        "2.40.5",
        "85d6d5323b346c40ba18ecc4265d141f5fef416d174b1ceed8404b90e9e69815",
    ],
    [
        "google-login",
        "1.1",
        "6be817f78f40048aa8802edba9f0070599397c0305a43f5ac6156ef0dedccdd3",
    ],
    [
        "fail-the-build-plugin",
        "1.0",
        "",
    ],
]

JENKINS_PLUGINS_VERSIONS = {("%%{JENKINS_PLUGIN_%s}" % plugin[0]): ("%s@%s" % (
    plugin[0],
    plugin[1],
)) for plugin in JENKINS_PLUGINS}

GITHUB_PROJECT = "bazelbuild/bazel"

GITHUB_URL = "https://github.com/" + GITHUB_PROJECT

PLATFORMS = [
    "linux-x86_64",
    "darwin-x86_64",
    "ubuntu_15.10-x86_64",
]

#
# Nodes
#

# OS X machine are not docker images
jenkins_node(
    name = "darwin-x86_64",
    labels = [
        "darwin-x86_64",
        "safe",
    ],
    remote_fs = "/Users/ci",
)

jenkins_node(
    name = "ubuntu_14.04-x86_64",
    labels = [
        "linux-x86_64",
        "safe",
    ],
    # We don't use docker for this image, Bazel tests are too resource
    # consuming, we run them in a standalone VM.
)

# Non-release nodes
jenkins_node(
    name = "ubuntu_15.10-x86_64",
    labels = [
        "no-release",
        "safe",
    ],
)

# A little hack to remove path consideration
DEPLOY_FILES = [
    "hoedown",
    "github-release",
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
    base = "//base:ubuntu-wily-amd64-golang",
    directory = "/opt/data",
    env = {
        # We have to put those files on some secrets volume.
        "BOTO_CONFIG": "/opt/secrets/boto_config",
        "GITHUB_TOKEN_FILE": "/opt/secrets/github_token",
        "GSUTIL": "/opt/data/gsutil/gsutil",
        "GITHUB_RELEASE": "/opt/data/github-release/github-release",
        "HOEDOWN": "/opt/data/hoedown/hoedown",
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
    base = "deploy-full",
)

#
# Jobs
#
JOBS_SUBSTITUTIONS = JENKINS_PLUGINS_VERSIONS + {
    "%{GITHUB_URL}": GITHUB_URL,
    "%{GITHUB_PROJECT}": GITHUB_PROJECT,
    "%{PLATFORMS}": "".join(["<string>%s</string>" % p for p in PLATFORMS]),
    "%{BAZEL_BUILD_RECIPIENT}": "bazel-ci@googlegroups.com",
    "%{BAZEL_RELEASE_RECIPIENT}": "bazel-discuss+release@googlegroups.com",
    "%{SENDER_EMAIL}": "noreply@bazel.io",
}

JOBS = [
    "Bazel",
    "Bazel-Release",
    "Bazel-Release-Trigger",
    "Bazel-Incremental",
    "Github-Trigger",
    "Tutorial",
]

[jenkins_job(
    name = job,
    config = "jobs-%s.xml.tpl" % job,
    substitutions = JOBS_SUBSTITUTIONS,
) for job in JOBS]

# Jenkins permissions
# Public permissions
PUBLIC_PERMS = [
    "Hudson.Read",  # Read the public dashboard
    "Item.Read",  # Read the result of a build
    "Item.Workspace",  # Read a job workspace
    "View.Read",  # Read views
    "Computer.Connect",  # Connect a new slave, needed by slaves
]

# Permissions for @google.com emails
AUTHENTICATED_PERMS = PUBLIC_PERMS + [
    # Special permissions
    "Item.Build",  # Launch a build
    "Item.Cancel",  # Cancel a build
]

# Permissions for admin users (Beware it is dangerous)
ADMIN_PERMS = AUTHENTICATED_PERMS + [
    "Run.Delete",  # Delete one build's information
    "Run.Update",  # Run one build's information
    "View.Configure",  # Configure views
    "View.Create",  # Create a new view
    "View.Delete",  # Delete existing view
    # Dangerous area: touch to slaves
    "Computer.Disconnect",  # Disconnect a slave, normally never needed
    "Computer.Configure",  # Configure a slave, normally never needed
    "Computer.Delete",  # Delete a slave, almost never needed
    "Computer.Build",  # Build on a slave, needed for debugging
    # Very dangerous area, administer jenkins
    "Hudson.Administer",  # Only used for restarting jenkins.
]

PERMS_TEMPLATE = "<permission>hudson.model.%s:%s</permission>"

#
# Creates the permissions info
#
# This is a config file generated by the build.sh script.
load("config", "ADMIN_USERS")

JENKINS_PERMISSIONS = {
    "%{JENKINS_PERMISSIONS}": "\n".join([
        PERMS_TEMPLATE % (perm, "anonymous")
        for perm in PUBLIC_PERMS
    ] + [
        PERMS_TEMPLATE % (perm, "authenticated")
        for perm in AUTHENTICATED_PERMS
    ] + [
        PERMS_TEMPLATE % (perm, user)
        for user in ADMIN_USERS
        for perm in ADMIN_PERMS
    ]),
}

#
# Finally the Jenkins image
#
jenkins_build(
    name = "jenkins",
    configs = glob(
        [
            "*.xml",
            "*.xml.tpl",
            "secrets/*",
            "init.groovy.d/*",
        ],
        exclude = ["jobs-*.xml.tpl"],
    ) + [
        ":ubuntu_14.04-x86_64",
        ":ubuntu_15.10-x86_64",
        ":darwin-x86_64",
        ":deploy",
    ] + JOBS,
    plugins = [plugin[0] for plugin in JENKINS_PLUGINS],
    substitutions = JOBS_SUBSTITUTIONS + JENKINS_PERMISSIONS,
)
