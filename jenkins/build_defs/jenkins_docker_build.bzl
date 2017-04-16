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

# Creation of the docker container for the jenkins master.

load("@bazel_tools//tools/build_defs/docker:docker.bzl", "docker_build")
load(":templates.bzl", "merge_files")
load(":vars.bzl", "MAIL_SUBSTITUTIONS")

def jenkins_docker_build(name, plugins = None, base = "//jenkins/base", configs = [],
                  jobs = [], substitutions = {}, visibility = None, tars = []):
  """Build the docker image for the Jenkins instance."""
  substitutions = substitutions + MAIL_SUBSTITUTIONS
  # Expands config files in a tar ball
  merge_files(
      name = "%s-configs" % name,
      srcs = configs,
      directory = "/usr/share/jenkins/ref",
      strip_prefixes = [
          "jenkins/config",
          "jenkins",
      ],
      substitutions = substitutions)

  # Create the structures for jobs
  merge_files(
      name = "%s-jobs" % name,
      srcs = jobs,
      path_format = "jobs/{basename}/config.xml",
      directory = "/usr/share/jenkins/ref",
  )

  ### FINAL IMAGE ###
  docker_build(
      name = name,
      tars = [
          ":%s-jobs" % name,
          ":%s-configs" % name,
      ] + tars,
      # Workaround no way to specify owner in pkg_tar
      # TODO(dmarting): use https://cr.bazel.build/10255 when it hits a release.
      user = "root",
      entrypoint = [
          "/bin/tini",
          "--",
          "/bin/bash",
          "-c",
          "[ -d /opt/lib ] && chown -R jenkins /opt/lib; su jenkins -c /usr/local/bin/jenkins.sh",
      ],
      # End of workaround
      base = base,
      directory = "/",
      visibility = visibility,
  )
