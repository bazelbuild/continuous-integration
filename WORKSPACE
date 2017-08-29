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
    commit = "db1b348dfdf161a784bc1efc5a1020395572b996",
)

load(
  "@io_bazel_rules_docker//docker:docker.bzl",
  "docker_repositories"
)
docker_repositories()

# For testing with docker
load("//jenkins/test:docker_repository.bzl", "docker_repository")
docker_repository()

# Docker base images
load("//base:docker_pull.bzl", "docker_pull")

[[docker_pull(
    name = "ubuntu-%s-amd64%s" % (ubuntu_version, ext),
    dockerfile = "//base:Dockerfile.ubuntu-%s-amd64%s" % (ubuntu_version, ext),
    tag = "local:ubuntu-%s-amd64%s" % (ubuntu_version, ext),
) for ubuntu_version in [
    "wily",
    "xenial",
]] for ext in [
    "",
    "-deploy",
    "-ssh",
]]

# Jenkins
load("//jenkins/base:plugins.bzl", "JENKINS_PLUGINS")
load("//jenkins/base:jenkins_base.bzl", "jenkins_base")

jenkins_base(
    name = "jenkins",
    plugins = JENKINS_PLUGINS,
    version = "2.60.2",
    volumes = ["/opt/secrets"],
)

# Releases stuff
http_file(
    name = "hoedown",
    sha256 = "779b75397043f6f6cf2ca8c8a716da58bb03ac42b1a21b83ff66b69bc60c016c",
    url = "https://github.com/hoedown/hoedown/archive/3.0.4.tar.gz",
)

http_file(
    name = "github_release",
    sha256 = "d6994f8a43aaa7c5a7c8c867fe69cfe302cd8eda0df3d371d0e69413999c83d8",
    url = "https://github.com/c4milo/github-release/archive/v1.0.7.tar.gz",
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
    sha256 = "a4ec1aff59b95a14b45eb2e23761a0179e98319da5a7eb76b56ea8cdc7b871c3",
    strip_prefix = "MarkupSafe-0.23",
    url = "https://pypi.python.org/packages/source/M/MarkupSafe/MarkupSafe-0.23.tar.gz#md5=f5ab3deee4c37cd6a922fb81e730da6e",
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
    sha256 = "bc1ff2ff88dbfacefde4ddde471d1417d3b304e8df103a7a9437d47269201bf4",
    strip_prefix = "Jinja2-2.8",
    url = "https://pypi.python.org/packages/source/J/Jinja2/Jinja2-2.8.tar.gz#md5=edb51693fe22c53cee5403775c71a99e",
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
maven_jar(
    name = "org_codehaus_groovy_all",
    artifact = "org.codehaus.groovy:groovy-all:jar:2.4.4",
)

maven_jar(
    name = "org_hamcrest",
    artifact = "org.hamcrest:hamcrest-all:jar:1.3",
)
