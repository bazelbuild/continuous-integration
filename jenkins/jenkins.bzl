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

# Some definition to setup jenkins and build the corresponding docker images

load("/tools/build_defs/docker/docker", "docker_build")

JENKINS_PORT = 80
JENKINS_HOST = "jenkins"

def expand_template_impl(ctx):
  """Simply spawm the template_action in a rule."""
  ctx.template_action(
      template = ctx.file.template,
      output = ctx.outputs.out,
      substitutions = ctx.attr.substitutions,
      executable = ctx.attr.executable,
      )

expand_template = rule(
    implementation = expand_template_impl,
    attrs = {
        "template": attr.label(mandatory=True,
                               allow_files=True,
                               single_file=True),
        "substitutions": attr.string_dict(mandatory=True),
        "out": attr.output(mandatory=True),
        "executable": attr.bool(default=True),
        },
    )

def jenkins_job(name, config, substitutions = {}):
  """Create a job configuration on Jenkins."""
  expand_template(
      name = name,
      template = config,
      out = "jobs/%s/config.xml" % name,
      substitutions = substitutions,
    )

def jenkins_node(name, remote_fs = "/home/ci", num_executors = 1,
                labels = [], base = None):
  """Create a node configuration on Jenkins, with possible docker image."""
  native.genrule(
      name = name,
      cmd = """cat >$@ <<'EOF'
<?xml version='1.0' encoding='UTF-8'?>
<slave>
  <name>%s</name>
  <description></description>
  <remoteFS>%s</remoteFS>
  <numExecutors>%s</numExecutors>
  <mode>NORMAL</mode>
  <retentionStrategy class="hudson.slaves.RetentionStrategy$$Always"/>
  <launcher class="hudson.slaves.JNLPLauncher"/>
  <label>%s</label>
  <nodeProperties/>
</slave>
""" % (name, remote_fs, num_executors, " ".join([name] + labels)),
      outs = ["nodes/%s/config.xml" % name],
      )
  if base:
    # Generate docker image startup script
    expand_template(
        name = name + ".docker-launcher",
        out = name + ".docker-launcher.sh",
        template = "slave_setup.sh",
        substitutions = {
            "%{NODE_NAME}": name,
            "%{HOME_FS}": remote_fs,
            "%{JENKINS_SERVER}": "http://%s:%s" % (JENKINS_HOST, JENKINS_PORT),
            },
        executable = True,
        )
    # Generate docker image
    docker_build(
        name = name + ".docker",
        base = base,
        volumes = [remote_fs],
        files = [":%s.docker-launcher.sh" % name],
        entrypoint = [
            "/bin/bash",
            "/%s.docker-launcher.sh" % name,
        ],
        )

def jenkins_build(name, plugins = [], base = "jenkins-base.tar", configs = []):
  """Build the docker image for the Jenkins instance."""
  ### BASE IMAGE ###
  # We don't have docker_pull yet, so the easiest way to do it:
  #   docker pull jenkins:1.609.1
  #   docker save jenkins:1.609.1 >jenkins-base.tar
  # We cannot perform it in a genrule because it needs access to the docker
  # environment variables.
  docker_build(
    name = "%s-docker-base" % name,
    base = base,
  )
  ### ADD JENKINS PLUGINS ###
  # TODO(dmarting): combine it with remote repositories.
  # TODO(dmarting): maybe we should make that possible from the docker rules
  # directly?
  [native.genrule(
      name = "%s-plugin-%s-rename" % (name, plugin),
      srcs = ["@jenkins-plugin-%s//file" % plugin],
      cmd = "cp $< $@",
      outs = ["%s-%s.jpi" % (name, plugin)],
  ) for plugin in plugins]
  docker_build(
      name = "%s-plugins-base" % name,
      base = "%s-docker-base" % name,
      files = [":%s-%s.jpi" % (name, plugin) for plugin in plugins],
      directory = "/usr/share/jenkins/ref/plugins"
  )
  # We ovewrite jenkins.sh because configuration files are to be replaced,
  # they are not a "reference setup".
  docker_build(
      name = "%s-jenkins-base" % name,
      base = "%s-plugins-base" % name,
      files = ["jenkins.sh"],
      entrypoint = [
          "/bin/bash",
          "/usr/local/bin/jenkins.sh",
      ],
      volumes = ["/opt/secrets"],
      directory = "/usr/local/bin",
  )
  ### FINAL IMAGE ###
  docker_build(
      name = name,
      files = configs,
      base = "%s-jenkins-base" % name,
      directory = "/usr/share/jenkins/ref"
  )
