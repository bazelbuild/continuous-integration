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

# Some definition to setup jenkins and build the corresponding docker images

load("@bazel_tools//tools/build_defs/docker:docker.bzl", "docker_build")
load("@bazel_tools//tools/build_defs/pkg:pkg.bzl", "pkg_tar")
load("//jenkins/base:plugins.bzl", "JENKINS_PLUGINS")

JENKINS_PLUGINS_VERSIONS = {
    ("JENKINS_PLUGIN_%s" % plugin.replace("-", "_")): ("%s@%s" % (
        plugin,
        JENKINS_PLUGINS[plugin][0],
)) for plugin in JENKINS_PLUGINS}

JENKINS_PORT = 80
JENKINS_HOST = "jenkins"

MAILS_SUBSTITUTIONS = {
    "BAZEL_BUILD_RECIPIENT": "bazel-ci@googlegroups.com",
    "BAZEL_RELEASE_RECIPIENT": "bazel-discuss+release@googlegroups.com",
    "SENDER_EMAIL": "noreply@bazel.io",
}

def expand_template_impl(ctx):
  """Simply spawn the template-engine in a rule."""
  variables = [
      "--variable=%s=%s" % (k, ctx.attr.substitutions[k])
      for k in ctx.attr.substitutions
  ]
  imports = [
      "--imports=%s=%s" % (ctx.attr.deps[i].label, ctx.files.deps[i].path)
      for i in range(0, len(ctx.attr.deps))
  ]
  ctx.action(
      executable = ctx.executable._engine,
      arguments = [
        "--executable" if ctx.attr.executable else "--noexecutable",
        "--template=%s" % ctx.file.template.path,
        "--output=%s" % ctx.outputs.out.path,
      ] + variables + imports,
      inputs = [ctx.file.template] + ctx.files.deps,
      outputs = [ctx.outputs.out],
      )

expand_template = rule(
    attrs = {
        "template": attr.label(
            mandatory = True,
            allow_files = True,
            single_file = True,
        ),
        "deps": attr.label_list(default = [], allow_files = True),
        "substitutions": attr.string_dict(mandatory = True),
        "out": attr.output(mandatory = True),
        "executable": attr.bool(default = True),
        "_engine": attr.label(
            default = Label("//templating:template_engine"),
            executable = True,
            cfg="host"),
    },
    implementation = expand_template_impl,
)

def _dest_path(f, strip_prefixes):
  """Returns the short path of f, stripped of strip_prefix."""
  for strip_prefix in strip_prefixes:
    if f.short_path.startswith(strip_prefix):
      return f.short_path[len(strip_prefix):]
  return f.short_path

def _format_path(path_format, path):
  dirsep = path.rfind("/")
  dirname = path[:dirsep] if dirsep > 0 else ""
  basename = path[dirsep+1:] if dirsep > 0 else path
  extsep = basename.rfind(".")
  extension = basename[extsep+1:] if extsep > 0 else ""
  basename = basename[:extsep] if extsep > 0 else basename
  flavor = ""
  if basename.endswith("-staging"):
    basename = basename[:-8]
    flavor = "staging"
  elif basename.endswith("-test"):
    basename = basename[:-5]
    flavor = "test"
  return path_format.format(
      path=path,
      dirname=dirname,
      basename=basename,
      flavor=flavor,
      extension=extension
  )

def _append_inputs(args, inputs, f, path, path_format):
  args.append("--file=%s=%s" % (
      f.path,
      _format_path(path_format, path)
  ))
  inputs.append(f)

def _merge_files_impl(ctx):
  """Merge a list of config files in a tar ball with the correct layout."""
  output = ctx.outputs.out
  build_tar = ctx.executable._build_tar
  inputs = []
  args = [
      "--output=" + output.path,
      "--directory=" + ctx.attr.directory,
      "--mode=0644",
      ]
  variables = [
      "--variable=%s=%s" % (k, ctx.attr.substitutions[k])
      for k in ctx.attr.substitutions
  ]
  for f in ctx.files.srcs:
    path = _dest_path(f, ctx.attr.strip_prefixes)
    if path.endswith(".tpl"):
      path = path[:-4]
      f2 = ctx.new_file(ctx.label.name + "/" + path)
      ctx.action(
          executable = ctx.executable._engine,
          arguments = [
            "--template=%s" % f.path,
            "--output=%s" % f2.path,
            "--noescape_xml",
          ] + variables,
          inputs = [f],
          outputs = [f2],
      )
      _append_inputs(args, inputs, f2, path, ctx.attr.path_format)
    else:
      _append_inputs(args, inputs, f, path, ctx.attr.path_format)
  ctx.action(
      executable = build_tar,
      arguments = args,
      inputs = inputs,
      outputs = [output],
      mnemonic="MergeFiles"
      )

_merge_files = rule(
    attrs = {
        "srcs": attr.label_list(allow_files=True),
        "template_extension": attr.string(default=".tpl"),
        "directory": attr.string(default="/"),
        "strip_prefixes": attr.string_list(default=[]),
        "substitutions": attr.string_dict(default={}),
        "path_format": attr.string(default="{path}"),
        "_build_tar": attr.label(
            default=Label("@bazel_tools//tools/build_defs/pkg:build_tar"),
            cfg="host",
            executable=True,
            allow_files=True),
        "_engine": attr.label(
            cfg="host",
            default = Label("//templating:template_engine"),
            executable = True),
    },
    outputs = {"out": "%{name}.tar"},
    implementation = _merge_files_impl,
)

def jenkins_job(name, config, substitutions = {}, deps = [],
                project='bazel', org='bazelbuild', git_url=None, project_url=None,
                platforms=[], test_platforms=["linux-x86_64"]):
  """Create a job configuration on Jenkins.

  Args:
     name: the name of the job to create
     config: the configuration file for the job
     substitutions: additional substitutions to pass to the template generation
     deps: list of dependencies (templates included by the config file)
     project: the project name on github
     org: the project organization on github, default 'bazelbuild'
     git_url: the URL to the git project, defaulted to the Github URL
     project_url: the project url, defaulted to the Git URL
     platforms: platforms on which to run that job, default None,
     test_platforms: platforms on which to run that job when inside of a
       dockerized test, by default only 'linux-x86_64'
  """
  github_project =  "%s/%s" % (org, project.lower())
  github_url = "https://github.com/" + github_project
  if not git_url:
    git_url = github_url
  if not project_url:
    project_url = git_url
  substitutions = substitutions + JENKINS_PLUGINS_VERSIONS + {
      "GITHUB_URL": github_url,
      "GIT_URL": git_url,
      "GITHUB_PROJECT": github_project,
      "PROJECT_URL": project_url,
      "PLATFORMS": "\n".join(platforms),
      } + MAILS_SUBSTITUTIONS
  substitutions["SEND_EMAIL"] = "1"
  expand_template(
      name = name,
      template = config,
      out = "%s.xml" % name,
      deps = deps,
      substitutions = JENKINS_PLUGINS_VERSIONS + substitutions,
    )
  substitutions["SEND_EMAIL"] = "0"
  expand_template(
      name = name + "-staging",
      template = config,
      out = "%s-staging.xml" % name,
      deps = deps,
      substitutions = JENKINS_PLUGINS_VERSIONS + substitutions,
    )

  if test_platforms:
    substitutions["PLATFORMS"] = "\n".join(test_platforms)
    expand_template(
      name = name + "-test",
      template = config,
      out = "%s-test.xml" % name,
      deps = deps,
      substitutions = JENKINS_PLUGINS_VERSIONS + substitutions,
    )

def bazel_git_job(**kwargs):
  """Override bazel_github_job to test a project that is not on GitHub."""
  kwargs["github_enabled"] = False
  if not "git_url" in kwargs:
    if not "project_url" in kwargs:
      fail("Neither project_url nor git_url was specified")
    kwargs["git_url"] = kwargs
  bazel_github_job(**kwargs)

def bazel_github_job(name, platforms=[], branch="master", project=None, org="google",
                     project_url=None, workspace=".", configure=[], git_url=None,
                     bazel_versions=["HEAD", "latest"],
                     tests=["//..."], targets=["//..."], substitutions={},
                     windows_configure=[],
                     windows_tests=["//..."], windows_targets=["//..."],
                     windows_tests_msys=["//..."], windows_targets_msys=["//..."],
                     test_opts=["--test_output=errors", "--build_tests_only"],
                     test_tag_filters=["-noci", "-manual"],
                     build_opts=["--verbose_failures"],
                     test_platforms=["linux-x86_64"],
                     enable_trigger=True,
                     gerrit_project=None,
                     enabled=True,
                     pr_enabled=True,
                     github_enabled=True,
                     run_sequential=False,
                     sauce_enabled=False):
  """Create a generic github job configuration to build against Bazel head."""
  if not project:
    project = name
  substitutions = substitutions + {
    "WORKSPACE": workspace,
    "PROJECT_NAME": project,
    "BRANCH": branch,
    "CONFIGURE": "\n".join(configure),
    "WINDOWS_CONFIGURE": "\n".join(windows_configure),
    "TEST_OPTS": " ".join(test_opts),
    "TEST_TAG_FILTERS": ",".join(test_tag_filters),
    "BUILD_OPTS": " ".join(build_opts),
    "TESTS": " + ".join(tests),
    "WINDOWS_TESTS": " ".join(windows_tests),
    # TODO(pcloudy): remove *_MSYS attributes when we don't need MSYS anymore
    "WINDOWS_TESTS_MSYS": " ".join(windows_tests_msys),
    "BUILDS": " ".join(targets),
    "WINDOWS_BUILDS": " ".join(windows_targets),
    "WINDOWS_BUILDS_MSYS": " ".join(windows_targets_msys),
    "BAZEL_VERSIONS": "\n".join(bazel_versions),
    "disabled": str(not enabled).lower(),
    "enable_trigger": str(enable_trigger and github_enabled).lower(),
    "github": str(github_enabled),
    "GERRIT_PROJECT": str(gerrit_project),
    "RUN_SEQUENTIAL": str(run_sequential).lower(),
    "SAUCE_ENABLED": str(sauce_enabled).lower(),
  }

  jenkins_job(
      name = name,
      config = "//jenkins:github-jobs.xml.tpl",
      deps = [
          "//jenkins:github-jobs.sh.tpl",
          "//jenkins:github-jobs.bat.tpl",
          "//jenkins:github-jobs.test-logs.sh.tpl",
          "//jenkins:github-jobs.test-logs.bat.tpl",
      ],
      substitutions=substitutions,
      git_url=git_url,
      project=project,
      org=org,
      project_url=project_url,
      platforms=platforms,
      test_platforms=test_platforms)
  substitutions["BAZEL_VERSIONS"] = "\n".join([
      v for v in bazel_versions if not v.startswith("HEAD")])
  if pr_enabled:
    jenkins_job(
        name = "PR-" + name,
        config = "//jenkins:github-jobs-PR.xml.tpl",
        deps = [
            "//jenkins:github-jobs.sh.tpl",
            "//jenkins:github-jobs.bat.tpl",
            "//jenkins:github-jobs.test-logs.sh.tpl",
            "//jenkins:github-jobs.test-logs.bat.tpl",
        ],
        substitutions=substitutions,
        project=project,
        org=org,
        project_url=project_url,
        platforms=platforms,
        test_platforms=test_platforms)
  if gerrit_project != None:
    jenkins_job(
        name = "Gerrit-" + name,
        config = "//jenkins:github-jobs-Gerrit.xml.tpl",
        deps = [
            "//jenkins:github-jobs.sh.tpl",
            "//jenkins:github-jobs.bat.tpl",
            "//jenkins:github-jobs.test-logs.sh.tpl",
            "//jenkins:github-jobs.test-logs.bat.tpl",
        ],
        substitutions=substitutions,
        project=project,
        org=org,
        project_url=project_url,
        platforms=platforms,
        test_platforms=test_platforms)


def jenkins_node(name, remote_fs = "/home/ci", num_executors = 1, mode = "NORMAL",
                 labels = [], docker_base = None, preference = 1,
                 visibility = None):
  """Create a node configuration on Jenkins, with possible docker image.

  Args:
    name: Name of the node on Jenkins.
    remote_fs: path to the home of the Jenkins user.
    num_executors: number of executors (i.e. concurrent build) this machine can have.
    mode: NORMAL for "Utilize this node as much as possible"
      EXCLUSIVE for "Only build jobs with label restrictions matching this node"
    labels: list of Jenkins labels for this node (the node name is always added).
    docker_base: base for the corresponding docker image to create if we should create one
      (if docker_base is not specified, then a corresponding machine should be configured
      to connect to the Jenkins master).
    preference: A preference factor, if a node as a factor of 1 and another a factor of
      4, then the second one will be scheduled 4 time more jobs than the first one.
    visibility: rule visibility.
  """
  native.genrule(
      name = name,
      cmd = """cat >$@ <<'EOF'
<?xml version='1.0' encoding='UTF-8'?>
<slave>
  <name>%s</name>
  <description></description>
  <remoteFS>%s</remoteFS>
  <numExecutors>%s</numExecutors>
  <mode>%s</mode>
  <retentionStrategy class="hudson.slaves.RetentionStrategy$$Always"/>
  <launcher class="hudson.slaves.JNLPLauncher"/>
  <label>%s</label>
  <nodeProperties>
    <jp.ikedam.jenkins.plugins.scoringloadbalancer.preferences.BuildPreferenceNodeProperty plugin="scoring-load-balancer@1.0.1">
      <preference>%s</preference>
    </jp.ikedam.jenkins.plugins.scoringloadbalancer.preferences.BuildPreferenceNodeProperty>
  </nodeProperties>
</slave>
EOF
""" % (name, remote_fs, num_executors, mode, " ".join([name] + labels), preference),
      outs = ["nodes/%s/config.xml" % name],
      visibility = visibility,
      )
  if docker_base:
    # Generate docker image startup script
    expand_template(
        name = name + ".docker-launcher",
        out = name + ".docker-launcher.sh",
        template = "slave_setup.sh",
        substitutions = {
            "NODE_NAME": name,
            "HOME_FS": remote_fs,
            "JENKINS_SERVER": "http://%s:%s" % (JENKINS_HOST, JENKINS_PORT),
            },
        executable = True,
        )
    # Generate docker image
    docker_build(
        name = name + ".docker",
        base = docker_base,
        volumes = [remote_fs],
        files = [":%s.docker-launcher.sh" % name],
        data_path = ".",
        entrypoint = [
            "/bin/bash",
            "/%s.docker-launcher.sh" % name,
        ],
        visibility = visibility,
        )

def jenkins_build(name, plugins = None, base = "//jenkins/base", configs = [],
                  jobs = [], substitutions = {}, visibility = None):
  """Build the docker image for the Jenkins instance."""
  substitutions = substitutions + MAILS_SUBSTITUTIONS
  # Expands config files in a tar ball
  _merge_files(
      name = "%s-configs" % name,
      srcs = configs,
      directory = "/usr/share/jenkins/ref",
      strip_prefixes = [
          "jenkins/config",
          "jenkins",
      ],
      substitutions = substitutions)

  # Create the structures for jobs
  _merge_files(
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
      ],
      base = base,
      directory = "/",
      visibility = visibility,
  )