# Copyright 2015 Google Inc. All rights reserved.
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
]

JENKINS_PLUGINS_VERSIONS = {("%%{JENKINS_PLUGIN_%s}" % plugin[0]): ("%s@%s" % (
    plugin[0],
    plugin[1],
)) for plugin in JENKINS_PLUGINS}

GITHUB_PROJECT = "bazelbuild/bazel"
GITHUB_URL = "https://github.com/" + GITHUB_PROJECT

PLATFORMS = ["linux-x86_64", "darwin-x86_64"]  # TODO(dmarting): add darwin-x86_64

#
# Nodes
#

# We don't have docker_pull yet, so the easiest way to do it:
#   docker pull ubuntu:utopic
#   docker save ubuntu:utopic >ubuntu-utopic-base.tar
# Then generate the deb dependencies:
#   ./create_debs_repositories.sh docker:ubuntu:utopic ubuntu-utopic-amd64 \
#       ubuntu-utopic-base zip g++ zlib1g-dev openjdk-8-jdk openjdk-8-source \
#       wget git unzip python python3 curl \
#       > gen_debs
#   After ### WORKSPACE sits the workspace repository and after the ### BUILD
#   line sits the docker_build rule.
#   All that could be factorized using skylark repositories...
docker_build(
    name = "ubuntu-utopic-amd64",
    base = "ubuntu-utopic-base.tar",
    debs = [
        "@deb-ubuntu-utopic-amd64-binutils//file",
        "@deb-ubuntu-utopic-amd64-ca-certificates//file",
        "@deb-ubuntu-utopic-amd64-ca-certificates-java//file",
        "@deb-ubuntu-utopic-amd64-coreutils//file",
        "@deb-ubuntu-utopic-amd64-cpp//file",
        "@deb-ubuntu-utopic-amd64-cpp-4.9//file",
        "@deb-ubuntu-utopic-amd64-curl//file",
        "@deb-ubuntu-utopic-amd64-debconf//file",
        "@deb-ubuntu-utopic-amd64-default-jre//file",
        "@deb-ubuntu-utopic-amd64-default-jre-headless//file",
        "@deb-ubuntu-utopic-amd64-dh-python//file",
        "@deb-ubuntu-utopic-amd64-dpkg//file",
        "@deb-ubuntu-utopic-amd64-fontconfig//file",
        "@deb-ubuntu-utopic-amd64-fontconfig-config//file",
        "@deb-ubuntu-utopic-amd64-fonts-dejavu-core//file",
        "@deb-ubuntu-utopic-amd64-fonts-freefont-ttf//file",
        "@deb-ubuntu-utopic-amd64-gpp//file",
        "@deb-ubuntu-utopic-amd64-gpp-4.9//file",
        "@deb-ubuntu-utopic-amd64-gcc//file",
        "@deb-ubuntu-utopic-amd64-gcc-4.9//file",
        "@deb-ubuntu-utopic-amd64-gcc-4.9-base//file",
        "@deb-ubuntu-utopic-amd64-git//file",
        "@deb-ubuntu-utopic-amd64-git-man//file",
        "@deb-ubuntu-utopic-amd64-gsfonts//file",
        "@deb-ubuntu-utopic-amd64-gsfonts-x11//file",
        "@deb-ubuntu-utopic-amd64-install-info//file",
        "@deb-ubuntu-utopic-amd64-java-common//file",
        "@deb-ubuntu-utopic-amd64-libacl1//file",
        "@deb-ubuntu-utopic-amd64-libasan1//file",
        "@deb-ubuntu-utopic-amd64-libasn1-8-heimdal//file",
        "@deb-ubuntu-utopic-amd64-libasound2//file",
        "@deb-ubuntu-utopic-amd64-libasound2-data//file",
        "@deb-ubuntu-utopic-amd64-libasyncns0//file",
        "@deb-ubuntu-utopic-amd64-libatk-wrapper-java//file",
        "@deb-ubuntu-utopic-amd64-libatk-wrapper-java-jni//file",
        "@deb-ubuntu-utopic-amd64-libatk1.0-0//file",
        "@deb-ubuntu-utopic-amd64-libatk1.0-data//file",
        "@deb-ubuntu-utopic-amd64-libatomic1//file",
        "@deb-ubuntu-utopic-amd64-libattr1//file",
        "@deb-ubuntu-utopic-amd64-libavahi-client3//file",
        "@deb-ubuntu-utopic-amd64-libavahi-common-data//file",
        "@deb-ubuntu-utopic-amd64-libavahi-common3//file",
        "@deb-ubuntu-utopic-amd64-libbz2-1.0//file",
        "@deb-ubuntu-utopic-amd64-libc-dev-bin//file",
        "@deb-ubuntu-utopic-amd64-libc6//file",
        "@deb-ubuntu-utopic-amd64-libc6-dev//file",
        "@deb-ubuntu-utopic-amd64-libcairo2//file",
        "@deb-ubuntu-utopic-amd64-libcilkrts5//file",
        "@deb-ubuntu-utopic-amd64-libcloog-isl4//file",
        "@deb-ubuntu-utopic-amd64-libcomerr2//file",
        "@deb-ubuntu-utopic-amd64-libcups2//file",
        "@deb-ubuntu-utopic-amd64-libcurl3//file",
        "@deb-ubuntu-utopic-amd64-libcurl3-gnutls//file",
        "@deb-ubuntu-utopic-amd64-libdatrie1//file",
        "@deb-ubuntu-utopic-amd64-libdb5.3//file",
        "@deb-ubuntu-utopic-amd64-libdbus-1-3//file",
        "@deb-ubuntu-utopic-amd64-libdrm-intel1//file",
        "@deb-ubuntu-utopic-amd64-libdrm-nouveau2//file",
        "@deb-ubuntu-utopic-amd64-libdrm-radeon1//file",
        "@deb-ubuntu-utopic-amd64-libdrm2//file",
        "@deb-ubuntu-utopic-amd64-libedit2//file",
        "@deb-ubuntu-utopic-amd64-libelf1//file",
        "@deb-ubuntu-utopic-amd64-liberror-perl//file",
        "@deb-ubuntu-utopic-amd64-libexpat1//file",
        "@deb-ubuntu-utopic-amd64-libffi6//file",
        "@deb-ubuntu-utopic-amd64-libflac8//file",
        "@deb-ubuntu-utopic-amd64-libfontconfig1//file",
        "@deb-ubuntu-utopic-amd64-libfontenc1//file",
        "@deb-ubuntu-utopic-amd64-libfreetype6//file",
        "@deb-ubuntu-utopic-amd64-libgcc-4.9-dev//file",
        "@deb-ubuntu-utopic-amd64-libgcc1//file",
        "@deb-ubuntu-utopic-amd64-libgcrypt20//file",
        "@deb-ubuntu-utopic-amd64-libgdbm3//file",
        "@deb-ubuntu-utopic-amd64-libgdk-pixbuf2.0-0//file",
        "@deb-ubuntu-utopic-amd64-libgdk-pixbuf2.0-common//file",
        "@deb-ubuntu-utopic-amd64-libgif4//file",
        "@deb-ubuntu-utopic-amd64-libgl1-mesa-dri//file",
        "@deb-ubuntu-utopic-amd64-libgl1-mesa-glx//file",
        "@deb-ubuntu-utopic-amd64-libglapi-mesa//file",
        "@deb-ubuntu-utopic-amd64-libglib2.0-0//file",
        "@deb-ubuntu-utopic-amd64-libgmp10//file",
        "@deb-ubuntu-utopic-amd64-libgnutls-deb0-28//file",
        "@deb-ubuntu-utopic-amd64-libgomp1//file",
        "@deb-ubuntu-utopic-amd64-libgpg-error0//file",
        "@deb-ubuntu-utopic-amd64-libgraphite2-3//file",
        "@deb-ubuntu-utopic-amd64-libgssapi-krb5-2//file",
        "@deb-ubuntu-utopic-amd64-libgssapi3-heimdal//file",
        "@deb-ubuntu-utopic-amd64-libgtk2.0-0//file",
        "@deb-ubuntu-utopic-amd64-libgtk2.0-common//file",
        "@deb-ubuntu-utopic-amd64-libharfbuzz0b//file",
        "@deb-ubuntu-utopic-amd64-libhcrypto4-heimdal//file",
        "@deb-ubuntu-utopic-amd64-libheimbase1-heimdal//file",
        "@deb-ubuntu-utopic-amd64-libheimntlm0-heimdal//file",
        "@deb-ubuntu-utopic-amd64-libhogweed2//file",
        "@deb-ubuntu-utopic-amd64-libhx509-5-heimdal//file",
        "@deb-ubuntu-utopic-amd64-libidn11//file",
        "@deb-ubuntu-utopic-amd64-libisl10//file",
        "@deb-ubuntu-utopic-amd64-libitm1//file",
        "@deb-ubuntu-utopic-amd64-libjasper1//file",
        "@deb-ubuntu-utopic-amd64-libjbig0//file",
        "@deb-ubuntu-utopic-amd64-libjpeg-turbo8//file",
        "@deb-ubuntu-utopic-amd64-libjpeg8//file",
        "@deb-ubuntu-utopic-amd64-libjson-c2//file",
        "@deb-ubuntu-utopic-amd64-libk5crypto3//file",
        "@deb-ubuntu-utopic-amd64-libkeyutils1//file",
        "@deb-ubuntu-utopic-amd64-libkrb5-26-heimdal//file",
        "@deb-ubuntu-utopic-amd64-libkrb5-3//file",
        "@deb-ubuntu-utopic-amd64-libkrb5support0//file",
        "@deb-ubuntu-utopic-amd64-liblcms2-2//file",
        "@deb-ubuntu-utopic-amd64-libldap-2.4-2//file",
        "@deb-ubuntu-utopic-amd64-libllvm3.5//file",
        "@deb-ubuntu-utopic-amd64-liblsan0//file",
        "@deb-ubuntu-utopic-amd64-liblzma5//file",
        "@deb-ubuntu-utopic-amd64-libmpc3//file",
        "@deb-ubuntu-utopic-amd64-libmpdec2//file",
        "@deb-ubuntu-utopic-amd64-libmpfr4//file",
        "@deb-ubuntu-utopic-amd64-libncursesw5//file",
        "@deb-ubuntu-utopic-amd64-libnettle4//file",
        "@deb-ubuntu-utopic-amd64-libnspr4//file",
        "@deb-ubuntu-utopic-amd64-libnspr4-0d//file",
        "@deb-ubuntu-utopic-amd64-libnss3//file",
        "@deb-ubuntu-utopic-amd64-libnss3-nssdb//file",
        "@deb-ubuntu-utopic-amd64-libogg0//file",
        "@deb-ubuntu-utopic-amd64-libp11-kit0//file",
        "@deb-ubuntu-utopic-amd64-libpango-1.0-0//file",
        "@deb-ubuntu-utopic-amd64-libpangocairo-1.0-0//file",
        "@deb-ubuntu-utopic-amd64-libpangoft2-1.0-0//file",
        "@deb-ubuntu-utopic-amd64-libpciaccess0//file",
        "@deb-ubuntu-utopic-amd64-libpcre3//file",
        "@deb-ubuntu-utopic-amd64-libpcsclite1//file",
        "@deb-ubuntu-utopic-amd64-libpixman-1-0//file",
        "@deb-ubuntu-utopic-amd64-libpng12-0//file",
        "@deb-ubuntu-utopic-amd64-libpulse0//file",
        "@deb-ubuntu-utopic-amd64-libpython-stdlib//file",
        "@deb-ubuntu-utopic-amd64-libpython2.7-minimal//file",
        "@deb-ubuntu-utopic-amd64-libpython2.7-stdlib//file",
        "@deb-ubuntu-utopic-amd64-libpython3-stdlib//file",
        "@deb-ubuntu-utopic-amd64-libpython3.4-minimal//file",
        "@deb-ubuntu-utopic-amd64-libpython3.4-stdlib//file",
        "@deb-ubuntu-utopic-amd64-libquadmath0//file",
        "@deb-ubuntu-utopic-amd64-libreadline6//file",
        "@deb-ubuntu-utopic-amd64-libroken18-heimdal//file",
        "@deb-ubuntu-utopic-amd64-librtmp1//file",
        "@deb-ubuntu-utopic-amd64-libsasl2-2//file",
        "@deb-ubuntu-utopic-amd64-libsasl2-modules-db//file",
        "@deb-ubuntu-utopic-amd64-libselinux1//file",
        "@deb-ubuntu-utopic-amd64-libsndfile1//file",
        "@deb-ubuntu-utopic-amd64-libsqlite3-0//file",
        "@deb-ubuntu-utopic-amd64-libssl1.0.0//file",
        "@deb-ubuntu-utopic-amd64-libstdcpp-4.9-dev//file",
        "@deb-ubuntu-utopic-amd64-libstdcpp6//file",
        "@deb-ubuntu-utopic-amd64-libtasn1-6//file",
        "@deb-ubuntu-utopic-amd64-libthai-data//file",
        "@deb-ubuntu-utopic-amd64-libthai0//file",
        "@deb-ubuntu-utopic-amd64-libtiff5//file",
        "@deb-ubuntu-utopic-amd64-libtinfo5//file",
        "@deb-ubuntu-utopic-amd64-libtsan0//file",
        "@deb-ubuntu-utopic-amd64-libubsan0//file",
        "@deb-ubuntu-utopic-amd64-libudev1//file",
        "@deb-ubuntu-utopic-amd64-libuuid1//file",
        "@deb-ubuntu-utopic-amd64-libvorbis0a//file",
        "@deb-ubuntu-utopic-amd64-libvorbisenc2//file",
        "@deb-ubuntu-utopic-amd64-libwind0-heimdal//file",
        "@deb-ubuntu-utopic-amd64-libwrap0//file",
        "@deb-ubuntu-utopic-amd64-libx11-6//file",
        "@deb-ubuntu-utopic-amd64-libx11-data//file",
        "@deb-ubuntu-utopic-amd64-libx11-xcb1//file",
        "@deb-ubuntu-utopic-amd64-libxau6//file",
        "@deb-ubuntu-utopic-amd64-libxcb-dri2-0//file",
        "@deb-ubuntu-utopic-amd64-libxcb-dri3-0//file",
        "@deb-ubuntu-utopic-amd64-libxcb-glx0//file",
        "@deb-ubuntu-utopic-amd64-libxcb-present0//file",
        "@deb-ubuntu-utopic-amd64-libxcb-render0//file",
        "@deb-ubuntu-utopic-amd64-libxcb-shm0//file",
        "@deb-ubuntu-utopic-amd64-libxcb-sync1//file",
        "@deb-ubuntu-utopic-amd64-libxcb1//file",
        "@deb-ubuntu-utopic-amd64-libxcomposite1//file",
        "@deb-ubuntu-utopic-amd64-libxcursor1//file",
        "@deb-ubuntu-utopic-amd64-libxdamage1//file",
        "@deb-ubuntu-utopic-amd64-libxdmcp6//file",
        "@deb-ubuntu-utopic-amd64-libxext6//file",
        "@deb-ubuntu-utopic-amd64-libxfixes3//file",
        "@deb-ubuntu-utopic-amd64-libxfont1//file",
        "@deb-ubuntu-utopic-amd64-libxi6//file",
        "@deb-ubuntu-utopic-amd64-libxinerama1//file",
        "@deb-ubuntu-utopic-amd64-libxml2//file",
        "@deb-ubuntu-utopic-amd64-libxrandr2//file",
        "@deb-ubuntu-utopic-amd64-libxrender1//file",
        "@deb-ubuntu-utopic-amd64-libxshmfence1//file",
        "@deb-ubuntu-utopic-amd64-libxtst6//file",
        "@deb-ubuntu-utopic-amd64-libxxf86vm1//file",
        "@deb-ubuntu-utopic-amd64-linux-libc-dev//file",
        "@deb-ubuntu-utopic-amd64-lsb-base//file",
        "@deb-ubuntu-utopic-amd64-mime-support//file",
        "@deb-ubuntu-utopic-amd64-multiarch-support//file",
        "@deb-ubuntu-utopic-amd64-openjdk-7-jre//file",
        "@deb-ubuntu-utopic-amd64-openjdk-7-jre-headless//file",
        "@deb-ubuntu-utopic-amd64-openjdk-8-jdk//file",
        "@deb-ubuntu-utopic-amd64-openjdk-8-jre//file",
        "@deb-ubuntu-utopic-amd64-openjdk-8-jre-headless//file",
        "@deb-ubuntu-utopic-amd64-openjdk-8-source//file",
        "@deb-ubuntu-utopic-amd64-openssl//file",
        "@deb-ubuntu-utopic-amd64-perl//file",
        "@deb-ubuntu-utopic-amd64-perl-base//file",
        "@deb-ubuntu-utopic-amd64-perl-modules//file",
        "@deb-ubuntu-utopic-amd64-python//file",
        "@deb-ubuntu-utopic-amd64-python-minimal//file",
        "@deb-ubuntu-utopic-amd64-python2.7//file",
        "@deb-ubuntu-utopic-amd64-python2.7-minimal//file",
        "@deb-ubuntu-utopic-amd64-python3//file",
        "@deb-ubuntu-utopic-amd64-python3-minimal//file",
        "@deb-ubuntu-utopic-amd64-python3.4//file",
        "@deb-ubuntu-utopic-amd64-python3.4-minimal//file",
        "@deb-ubuntu-utopic-amd64-readline-common//file",
        "@deb-ubuntu-utopic-amd64-shared-mime-info//file",
        "@deb-ubuntu-utopic-amd64-tar//file",
        "@deb-ubuntu-utopic-amd64-ttf-bitstream-vera//file",
        "@deb-ubuntu-utopic-amd64-tzdata//file",
        "@deb-ubuntu-utopic-amd64-tzdata-java//file",
        "@deb-ubuntu-utopic-amd64-ucf//file",
        "@deb-ubuntu-utopic-amd64-unzip//file",
        "@deb-ubuntu-utopic-amd64-wget//file",
        "@deb-ubuntu-utopic-amd64-x11-common//file",
        "@deb-ubuntu-utopic-amd64-xfonts-encodings//file",
        "@deb-ubuntu-utopic-amd64-xfonts-utils//file",
        "@deb-ubuntu-utopic-amd64-zip//file",
        "@deb-ubuntu-utopic-amd64-zlib1g//file",
        "@deb-ubuntu-utopic-amd64-zlib1g-dev//file",
    ],
    env = {
        "JAVA_HOME": "/usr/lib/jvm/java-8-openjdk-amd64",
    },
    symlinks = {"/usr/local/bin/java": "/usr/lib/jvm/java-8-openjdk-amd64/bin/java"},
    visibility = ["//visibility:public"],
)

# OS X machine are not docker images
jenkins_node(
    name = "darwin-x86_64",
    remote_fs = "/Users/ci",
    labels = ["safe"],
)

jenkins_node(
    name = "ubuntu_14.04-x86_64",
    labels = [
        "linux-x86_64",
        "safe",
    ],
    # We don't use docker for this image, Bazel tests are too resource
    # consuming, we run them in a standalone VM.
    # base = "ubuntu-utopic-amd64"
)

# Image support golang and make
docker_build(
    name = "ubuntu-utopic-amd64-golang",
    base = "ubuntu-utopic-amd64",
    debs = [
        "@deb-ubuntu-utopic-amd64-golang-golang//file",
        "@deb-ubuntu-utopic-amd64-golang-golang-doc//file",
        "@deb-ubuntu-utopic-amd64-golang-golang-go//file",
        "@deb-ubuntu-utopic-amd64-golang-golang-go-linux-amd64//file",
        "@deb-ubuntu-utopic-amd64-golang-golang-src//file",
        "@deb-ubuntu-utopic-amd64-golang-make//file",
    ],
    symlinks = {"/usr/local/bin/go": "/usr/bin/golang-go"},
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
    base = "ubuntu-utopic-amd64-golang",
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
    "%{BAZEL_BUILD_RECIPIENT}": "bazel-dev+builds@googlegroups.com",
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

#
# Finally the Jenkins image
#
jenkins_build(
    name = "jenkins",
    configs = glob([
            "*.xml",
            "*.xml.tpl",
            "secrets/*",
        ],
        exclude = ["jobs-*.xml.tpl"],
    ) + [
        ":ubuntu_14.04-x86_64",
        ":darwin-x86_64",
        ":deploy",
    ] + JOBS,
    substitutions = JOBS_SUBSTITUTIONS,
    plugins = [plugin[0] for plugin in JENKINS_PLUGINS],
)
