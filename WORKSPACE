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
workspace(name = "io_bazel_ci")

git_repository(
    name = "io_bazel_rules_docker",
    remote = "https://github.com/bazelbuild/rules_docker.git",
    tag = "v0.3.0",
)

load(
    "@io_bazel_rules_docker//container:container.bzl",
    "container_pull",
    container_repositories = "repositories",
)

# This is NOT needed when going through the language lang_image
# "repositories" function(s).
container_repositories()

# Docker base images
load("//base:docker_base.bzl", "docker_bases")
docker_bases()

# Jenkins
load("//jenkins/base:plugins.bzl", "JENKINS_PLUGINS")
load("//jenkins/base:jenkins_base.bzl", "jenkins_base")

jenkins_base(
    name = "jenkins",
    plugins = JENKINS_PLUGINS,
    version = "2.105",
    digest = "sha256:d2b9c9e7c373f365364d9be87d21f29157d267cfe063e64d1bdf6097018772a5",
    volumes = ["/opt/secrets"],
)

# Releases stuff
http_file(
    name = "hoedown",
    sha256 = "01b6021b1ec329b70687c0d240b12edcaf09c4aa28423ddf344d2bd9056ba920",
    url = "https://github.com/hoedown/hoedown/archive/3.0.7.tar.gz",
)

http_file(
    name = "github_release",
    sha256 = "bb647fb89f086a78bfc51c0b3264338f3471fb5b275829a7d1f08cf76af17da2",
    url = "https://github.com/c4milo/github-release/archive/v1.1.0.tar.gz",
)

# Use Jinja for templating our files
new_http_archive(
    name = "markupsafe_archive",
    build_file_content = """
py_library(
    name = "markupsafe",
    srcs = glob(["markupsafe/*.py"]),
    srcs_version = "PY2AND3",
    visibility = ["//visibility:public"],
)
""",
    sha256 = "a6be69091dac236ea9c6bc7d012beab42010fa914c459791d627dad4910eb665",
    strip_prefix = "MarkupSafe-1.0",
    url = "https://pypi.python.org/packages/4d/de/32d741db316d8fdb7680822dd37001ef7a448255de9699ab4bfcbdf4172b/MarkupSafe-1.0.tar.gz#md5=2fcedc9284d50e577b5192e8e3578355",
)

new_http_archive(
    name = "org_pocoo_jinja_jinja2",
    build_file_content = """
py_library(
    name = "jinja2",
    srcs = glob(["jinja2/*.py"]),
    srcs_version = "PY2AND3",
    deps = [
        "@markupsafe_archive//:markupsafe",
    ],
    visibility = ["//visibility:public"],
)
""",
    sha256 = "f84be1bb0040caca4cea721fcbbbbd61f9be9464ca236387158b0feea01914a4",
    strip_prefix = "Jinja2-2.10",
    url = "https://pypi.python.org/packages/56/e6/332789f295cf22308386cf5bbd1f4e00ed11484299c5d7383378cf48ba47/Jinja2-2.10.tar.gz#md5=61ef1117f945486472850819b8d1eb3d",
)

# Our template engine use gflags
new_git_repository(
    name = "com_github_google_python_gflags",
    build_file_content = """
py_library(
    name = "gflags",
    srcs = [
        "gflags.py",
        "gflags_validators.py",
    ],
    visibility = ["//visibility:public"],
)
""",
    remote = "https://github.com/google/python-gflags",
    tag = "python-gflags-2.0",
)

# Testing Jenkins pipeline library
# TODO(dmarting): the groovy support is really rudimentary we should fix it:
#   - Need for adding more dependency
#   - Groovy test absolutely want you to declare a specific structure
#   - The release is not working with latest bazel
#   - Repository overrely on bind() and does not respect naming conventions
http_archive(
    name = "io_bazel_rules_groovy",
    url = "https://github.com/bazelbuild/rules_groovy/archive/6b8e32ce0f7e33ae1b859706c2dc0c169b966e7e.zip",
    sha256 = "9dac7ddcf9e0004b1eeaf53dd9324350601eaee8c252f77423330af3effe2f5c",
    strip_prefix = "rules_groovy-6b8e32ce0f7e33ae1b859706c2dc0c169b966e7e",
)
load("@io_bazel_rules_groovy//groovy:groovy.bzl", "groovy_repositories")
groovy_repositories()

# For groovy tests
load("//3rdparty:workspace.bzl", "maven_dependencies")
maven_dependencies()
