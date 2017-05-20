# Copyright 2017 The Bazel Authors. All rights reserved.
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

# Jenkins job creation

load(":templates.bzl", "expand_template")
load(":vars.bzl", "MAIL_SUBSTITUTIONS")

def _to_groovy_list(lst):
  return "[%s]" % (",".join(['"%s"' % e for e in lst]))

def jenkins_job(name, config, substitutions = {}, deps = [], deps_aliases = {},
                project='bazel', org='bazelbuild', git_url=None, project_url=None,
                folder=None, platforms=[], test_platforms=["linux-x86_64"],
                create_filegroups=True):
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
     create_filegroups: create filegroups named <name>/all, <name>/staging
       and <name>/test that contains the files needed to be included
       to include that job respectively for the production service, the
       staging service and the docker test version. This is to be set
       to false is the calling macros already creates those filegroups.
  """
  github_project =  "%s/%s" % (org, project.lower())
  github_url = "https://github.com/" + github_project
  if not git_url:
    git_url = github_url
  if not project_url:
    project_url = git_url
  deps += [deps_aliases[k] for k in deps_aliases]
  substitutions = substitutions + {
      "GITHUB_URL": github_url,
      "GIT_URL": git_url,
      "GITHUB_PROJECT": github_project,
      "PROJECT_URL": project_url,
      "PLATFORMS": "\n".join(platforms),
      } + MAIL_SUBSTITUTIONS
  substitutions["SEND_EMAIL"] = "1"
  # RESTRICT_CONFIGURATION can be use to restrict configuration of the groovy jobs
  if (not "RESTRICT_CONFIGURATION" in substitutions) or (
      not substitutions["RESTRICT_CONFIGURATION"]):
    substitutions["RESTRICT_CONFIGURATION"] = "[:]"
  expand_template(
      name = name,
      template = config,
      out = "%s.xml" % name,
      deps = deps,
      deps_aliases = deps_aliases,
      substitutions = substitutions,
    )
  if create_filegroups:
    native.filegroup(name = name + "/all", srcs = [name])
  substitutions["SEND_EMAIL"] = "0"
  substitutions["BAZEL_BUILD_RECIPIENT"] = ""
  expand_template(
      name = name + "-staging",
      template = config,
      out = "%s-staging.xml" % name,
      deps = deps,
      deps_aliases = deps_aliases,
      substitutions = substitutions,
    )
  if create_filegroups:
    native.filegroup(name = name + "/staging", srcs = [name + "-staging"])

  if test_platforms:
    substitutions["PLATFORMS"] = "\n".join(test_platforms)
    substitutions["RESTRICT_CONFIGURATION"] += " + [node:%s]" % _to_groovy_list(test_platforms)
    expand_template(
      name = name + "-test",
      template = config,
      out = "%s-test.xml" % name,
      deps = deps,
      deps_aliases = deps_aliases,
      substitutions = substitutions,
    )
    if create_filegroups:
      native.filegroup(name = name + "/test", srcs = [name + "-test"])

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
                     config="//jenkins/build_defs:default.json",
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
    "NAME": name,
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

  all_files = [name + ".xml"]
  test_files = [name + "-test.xml"]
  staging_files = [name + "-staging.xml"]

  jenkins_job(
      name = name,
      config = "//jenkins/build_defs:github-jobs.xml.tpl",
      deps = [
          "//jenkins/build_defs:github-jobs.sh.tpl",
          "//jenkins/build_defs:github-jobs.bat.tpl",
          "//jenkins/build_defs:github-jobs.test-logs.sh.tpl",
          "//jenkins/build_defs:github-jobs.test-logs.bat.tpl",
      ],
      substitutions=substitutions,
      git_url=git_url,
      project=project,
      org=org,
      project_url=project_url,
      platforms=platforms,
      test_platforms = test_platforms,
      create_filegroups=False)

  substitutions["BAZEL_VERSIONS"] = "\n".join([
      v for v in bazel_versions if not v.startswith("HEAD")])

  if enabled and config:
    jenkins_job(
        name = "Global/" + name,
        config = "//jenkins/build_defs:bazel-job-Global.xml.tpl",
        deps_aliases = {
          "JSON_CONFIGURATION": config,
        },
        substitutions=substitutions,
        project=project,
        org=org,
        project_url=project_url,
        platforms=platforms,
        test_platforms=test_platforms,
        create_filegroups=False)
    all_files.append("Global/%s.xml" % name)
    test_files.append("Global/%s-test.xml" % name)
    staging_files.append("Global/%s-staging.xml" % name)

  if pr_enabled:
    jenkins_job(
        name = "PR/" + name,
        config = "//jenkins/build_defs:github-jobs-PR.xml.tpl",
        deps = [
            "//jenkins/build_defs:github-jobs.sh.tpl",
            "//jenkins/build_defs:github-jobs.bat.tpl",
            "//jenkins/build_defs:github-jobs.test-logs.sh.tpl",
            "//jenkins/build_defs:github-jobs.test-logs.bat.tpl",
        ],
        substitutions=substitutions,
        project=project,
        org=org,
        project_url=project_url,
        platforms=platforms,
        test_platforms=test_platforms,
        create_filegroups=False)
    all_files.append("PR/%s.xml" % name)
    test_files.append("PR/%s-test.xml" % name)
    staging_files.append("PR/%s-staging.xml" % name)

  if gerrit_project != None:
    jenkins_job(
        name = "CR/" + name,
        config = "//jenkins/build_defs:github-jobs-Gerrit.xml.tpl",
        deps = [
            "//jenkins/build_defs:github-jobs.sh.tpl",
            "//jenkins/build_defs:github-jobs.bat.tpl",
            "//jenkins/build_defs:github-jobs.test-logs.sh.tpl",
            "//jenkins/build_defs:github-jobs.test-logs.bat.tpl",
        ],
        substitutions=substitutions,
        project=project,
        org=org,
        project_url=project_url,
        platforms=platforms,
        test_platforms=test_platforms)
    all_files.append("CR/%s.xml" % name)
    test_files.append("CR/%s-test.xml" % name)
    staging_files.append("CR/%s-staging.xml" % name)

  native.filegroup(name = "%s/all" % name, srcs = all_files)
  if test_platforms:
    native.filegroup(name = "%s/test" % name, srcs = test_files)
  native.filegroup(name = "%s/staging" % name, srcs = staging_files)
