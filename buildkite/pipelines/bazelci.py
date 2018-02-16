from __future__ import print_function
import argparse
import codecs
import json
import os.path
import shutil
import subprocess
import sys
import stat
import tempfile
import urllib.request
from shutil import copyfile
from urllib.parse import urlparse


def downstream_projects():
  return {
      "BUILD_file_generator": {
          "git_repository": "https://github.com/bazelbuild/BUILD_file_generator.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/BUILD_file_generator-postsubmit.json"
      },
      "buildtools": {
          "git_repository": "https://github.com/bazelbuild/buildtools.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/buildtools-postsubmit.json"
      },
      "examples": {
          "git_repository": "https://github.com/bazelbuild/examples.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/examples-postsubmit.json"
      },
      "migration-tooling": {
          "git_repository": "https://github.com/bazelbuild/migration-tooling.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/migration-tooling-postsubmit.json"
      },
      "protobuf": {
          "git_repository": "https://github.com/google/protobuf.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/protobuf-postsubmit.json"
      },
      "re2": {
          "git_repository": "https://github.com/google/re2.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/re2-postsubmit.json"
      },
      "rules_appengine": {
          "git_repository": "https://github.com/bazelbuild/rules_appengine.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_appengine-postsubmit.json"
      },
      "rules_closure": {
          "git_repository": "https://github.com/bazelbuild/rules_closure.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_closure-postsubmit.json"
      },
      "rules_go": {
          "git_repository": "https://github.com/bazelbuild/rules_go.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_go-postsubmit.json"
      },
      "rules_groovy": {
          "git_repository": "https://github.com/bazelbuild/rules_groovy.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_groovy-postsubmit.json"
      },
      "rules_gwt": {
          "git_repository": "https://github.com/bazelbuild/rules_gwt.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_gwt-postsubmit.json"
      },
      "rules_jsonnet": {
          "git_repository": "https://github.com/bazelbuild/rules_jsonnet.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_jsonnet-postsubmit.json"
      },
      "rules_k8s": {
          "git_repository": "https://github.com/bazelbuild/rules_k8s.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_k8s-postsubmit.json"
      },
      "rules_nodejs": {
          "git_repository": "https://github.com/bazelbuild/rules_nodejs.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_nodejs-postsubmit.json"
      },
      "rules_perl": {
          "git_repository": "https://github.com/bazelbuild/rules_perl.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_perl-postsubmit.json"
      },
      "rules_python": {
          "git_repository": "https://github.com/bazelbuild/rules_python.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_python-postsubmit.json"
      },
      "rules_scala": {
          "git_repository": "https://github.com/bazelbuild/rules_scala.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_scala-postsubmit.json"
      },
      "rules_typescript": {
          "git_repository": "https://github.com/bazelbuild/rules_typescript.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/rules_typescript-postsubmit.json"
      },
      "skydoc": {
          "git_repository": "https://github.com/bazelbuild/skydoc.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/skydoc-postsubmit.json"
      },
      "subpar": {
          "git_repository": "https://github.com/google/subpar.git",
          "http_config": "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/subpar-postsubmit.json"
      }
  }


def python_binary():
  return "python3.6"


def bazelcipy_url():
  '''
  URL to the latest version of this script.
  '''
  return "https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/bazelci.py"


def eprint(*args, **kwargs):
  '''
  Print to stderr and exit the process.
  '''
  print(*args, file=sys.stderr, **kwargs)
  exit(1)

def platforms_info():
  '''
  Returns a map containing all supported platform names as keys, with the
  values being the platform name in a human readable format, and a the
  buildkite-agent's working directory.
  '''
  return {
      "ubuntu1404":
      {
          "name": "Ubuntu 14.04",
          "agent-directory": " /var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/"
      },
      "ubuntu1604":
      {
          "name": "Ubuntu 16.04",
          "agent-directory": " /var/lib/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/"
      },
      "macos":
      {
          "name": "macOS",
          "agent-directory": "/usr/local/var/buildkite-agent/builds/${BUILDKITE_AGENT_NAME}/"
      },
  }


def supported_platforms():
    return set(platforms_info().keys())


def platform_name(platform):
    return platforms_info()[platform]["name"]


def git_clone_path():
  return "project-under-test"


def fetch_configs(http_url):
  '''
  If specified fetches the build configuration from http_url, else tries to
  read it from .bazelci/config.json.
  Returns the json configuration as a python data structure.
  '''
  if http_url is None:
    with open(".bazelci/config.json", "r") as fd:
      return json.load(fd)
  with urllib.request.urlopen(http_url) as resp:
    reader = codecs.getreader("utf-8")
    return json.load(reader(resp))


def execute_commands(config, platform, git_repository, use_but, save_but,
                     build_only, test_only):
  exit_code = -1
  tmpdir = None
  bazel_binary = "bazel"
  try:
    tmpdir = tempfile.mkdtemp()
    if use_but:
      source_step = create_label(platform_name(platform), "Bazel",
                                 build_only=True, test_only=False)
      bazel_binary = download_bazel_binary(tmpdir, source_step)
    if git_repository:
      clone_git_repository(git_repository)
      os.chdir(git_clone_path())
      cleanup(bazel_binary)
    else:
      cleanup(bazel_binary)
    execute_shell_commands(config.get("shell_commands", None))
    execute_bazel_run(bazel_binary, config.get("run_targets", None))
    if not test_only:
      execute_bazel_build(bazel_binary, config.get("build_flags", []),
                          config.get("build_targets", None))
      if save_but:
        upload_bazel_binary()
    if not build_only:
      bep_file = os.path.join(tmpdir, "build_event_json_file.json")
      exit_code = execute_bazel_test(bazel_binary, config.get("test_flags", []),
                                     config.get("test_targets", None), bep_file)
      upload_failed_test_logs(bep_file, tmpdir)
  finally:
    if git_repository:
      os.chdir("..")
      delete_git_checkout()
    if tmpdir:
      shutil.rmtree(tmpdir)
    if exit_code > -1:
      exit(exit_code)


def upload_bazel_binary():
  print("\n--- Uploading Bazel under test")
  fail_if_nonzero(execute_command(["buildkite-agent", "artifact", "upload",
                                   "bazel-bin/src/bazel"]))


def download_bazel_binary(dest_dir, source_step):
  print("\n--- Downloading Bazel under test")
  fail_if_nonzero(execute_command(["buildkite-agent", "artifact", "download",
                                   "bazel-bin/src/bazel", dest_dir, "--step", source_step]))
  bazel_binary_path = os.path.join(dest_dir, "bazel-bin/src/bazel")
  st = os.stat(bazel_binary_path)
  os.chmod(bazel_binary_path, st.st_mode | stat.S_IEXEC)
  return bazel_binary_path


def clone_git_repository(git_repository):
  delete_git_checkout()
  fail_if_nonzero(execute_command(["git", "clone", git_repository,
                                   git_clone_path()]))


def delete_git_checkout():
  if os.path.exists(git_clone_path()):
    shutil.rmtree(git_clone_path())


def cleanup(bazel_binary):
  print("\n--- Cleanup")
  if os.path.exists("WORKSPACE"):
    fail_if_nonzero(execute_command([bazel_binary, "clean", "--expunge"]))
  delete_git_checkout()


def delete_git_repository(git_repository):
  os.chdir("..")
  shutil.rmtree(git_clone_path())


def execute_shell_commands(commands):
  if not commands:
    return
  print("\n--- Shell Commands")
  shell_command = "\n".join(commands)
  fail_if_nonzero(execute_command([shell_command], shell=True))


def execute_bazel_run(bazel_binary, targets):
  if not targets:
    return
  print("\n--- Run Targets")
  for target in targets:
    fail_if_nonzero(execute_command([bazel_binary, "run", target]))


def execute_bazel_build(bazel_binary, flags, targets):
  if not targets:
    return
  print("\n+++ Build")
  fail_if_nonzero(execute_command([bazel_binary, "build", "--color=yes",
                                   "--keep_going"] + flags + targets))


def execute_bazel_test(bazel_binary, flags, targets, bep_file):
  if not targets:
    return 0
  print("\n+++ Test")
  return execute_command([bazel_binary, "test", "--color=yes", "--keep_going",
                          "--build_tests_only", "--build_event_json_file=" + bep_file] + flags +
                         targets)


def fail_if_nonzero(exitcode):
  if exitcode is not 0:
    exit(exitcode)


def upload_failed_test_logs(bep_file, tmpdir):
  if not os.path.exists(bep_file):
    return
  for logfile in failed_logs_from_bep(bep_file, tmpdir):
    fail_if_nonzero(execute_command(["buildkite-agent", "artifact", "upload",
                                     logfile]))


def failed_logs_from_bep(bep_file, tmpdir):
  test_logs = []
  raw_data = ""
  with open(bep_file) as f:
    raw_data = f.read()
  decoder = json.JSONDecoder()

  pos = 0
  while pos < len(raw_data):
    json_dict, size = decoder.raw_decode(raw_data[pos:])
    if "testResult" in json_dict:
      test_result = json_dict["testResult"]
      if test_result["status"] != "PASSED":
        outputs = test_result["testActionOutput"]
        for output in outputs:
          if output["name"] == "test.log":
            new_path = label_to_path(
                tmpdir, json_dict["id"]["testResult"]["label"])
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            copyfile(urlparse(output["uri"]).path, new_path)
            test_logs.append(new_path)
    pos += size + 1
  return test_logs


def label_to_path(tmpdir, label):
  # remove leading //
  path = label[2:]
  path = path.replace(":", "/")
  return os.path.join(tmpdir, path + ".log")


def execute_command(args, shell=False):
  print(" ".join(args))
  res = subprocess.run(args, shell=shell)
  return res.returncode


def print_project_pipeline(platform_configs, project_name, http_config,
                           git_repository, use_but):
  pipeline_steps = []
  for platform, config in platform_configs.items():
    step = runner_step(platform, project_name, http_config, git_repository,
                       use_but)
    pipeline_steps.append(step)

  print_pipeline(pipeline_steps)


def runner_step(platform, project_name=None, http_config=None,
                git_repository=None, use_but=False, save_but=False, build_only=False,
                test_only=False):
  command = python_binary() + " bazelci.py runner --platform=" + platform
  if http_config:
    command = command + " --http_config=" + http_config
  if git_repository:
    command = command + " --git_repository=" + git_repository
  if use_but:
    command = command + " --use_but"
  if save_but:
    command = command + " --save_but"
  if build_only:
    command = command + " --build_only"
  if test_only:
    command = command + " --test_only"
  label = create_label(platform_name(platform),
                       project_name, build_only, test_only)
  return """
  - label: \"{0}\"
    command: \"{1}\\n{2}\"
    agents:
      - \"os={3}\"""".format(label, fetch_bazelcipy_command(), command, platform)


def print_pipeline(steps):
  print("steps:")
  for step in steps:
    print(step)


def wait_step():
  return """
  - wait"""


def http_config_flag(http_config):
  if http_config is not None:
    return "--http_config=" + http_config
  return ""


def fetch_bazelcipy_command():
  return "curl -s {0} > bazelci.py".format(bazelcipy_url())


def upload_project_pipeline_step(project_name, git_repository, http_config):
  pipeline_command = ("{0} bazelci.py project_pipeline --project_name=\\\"{1}\\\" " +
                      "--use_but --git_repository={2}").format(python_binary(), project_name,
                                                               git_repository)
  if http_config:
    pipeline_command = pipeline_command + " --http_config=" + http_config
  pipeline_command = pipeline_command + " | buildkite-agent pipeline upload"

  return """
  - label: \"Setup {0}\"
    command: \"{1}\\n{2}\"
    agents:
      - \"pipeline=true\"""".format(project_name, fetch_bazelcipy_command(),
                                    pipeline_command)


def create_label(platform_name, project_name=None, build_only=False,
                 test_only=False):
  label = ""
  if build_only:
    label = "Build "
  if test_only:
    label = "Test "
  if project_name:
    label = label + "{0} ({1})".format(project_name, platform_name)
  else:
    label = label + platform_name
  return label


def bazel_build_step(platform, project_name, http_config=None,
                     build_only=False, test_only=False):
  pipeline_command = python_binary() + " bazelci.py runner"
  if build_only:
    pipeline_command = pipeline_command + " --build_only --save_but"
  if test_only:
    pipeline_command = pipeline_command + " --test_only"
  if http_config:
    pipeline_command = pipeline_command + " --http_config=" + http_config
  label = create_label(platform_name(platform), project_name, build_only=build_only,
                       test_only=test_only)
  pipeline_command = pipeline_command + " --platform=" + platform

  return """
  - label: \"{0}\"
    command: \"{1}\\n{2}\"
    agents:
      - \"os={3}\"""".format(label, fetch_bazelcipy_command(),
                             pipeline_command, platform)


def print_bazel_postsubmit_pipeline(configs, http_config):
  if not configs:
    eprint("Bazel postsubmit pipeline configuration is empty.")
  if set(configs.keys()) != set(supported_platforms()):
    eprint("Bazel postsubmit pipeline needs to build Bazel on all " +
           "supported platforms.")

  pipeline_steps = []
  for platform, config in configs.items():
    pipeline_steps.append(bazel_build_step(platform, "Bazel",
                                           http_config, build_only=True))
  pipeline_steps.append(wait_step())
  for platform, config in configs.items():
    pipeline_steps.append(bazel_build_step(platform, "Bazel",
                                           http_config, test_only=True))
  for project, config in downstream_projects().items():
    git_repository = config["git_repository"]
    http_config = config.get("http_config", None)
    pipeline_steps.append(upload_project_pipeline_step(project,
                                                       git_repository, http_config))

  print_pipeline(pipeline_steps)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      description='Bazel Continuous Integration Script')

  subparsers = parser.add_subparsers(dest="subparsers_name")
  bazel_postsubmit_pipeline = subparsers.add_parser(
      "bazel_postsubmit_pipeline")
  bazel_postsubmit_pipeline.add_argument("--http_config", type=str)
  bazel_postsubmit_pipeline.add_argument("--git_repository", type=str)

  project_pipeline = subparsers.add_parser("project_pipeline")
  project_pipeline.add_argument("--project_name", type=str)
  project_pipeline.add_argument("--http_config", type=str)
  project_pipeline.add_argument("--git_repository", type=str)
  project_pipeline.add_argument(
      "--use_but", type=bool, nargs="?", const=True)

  runner = subparsers.add_parser("runner")
  runner.add_argument("--platform", action="store",
                      choices=list(supported_platforms()))
  runner.add_argument("--http_config", type=str)
  runner.add_argument("--git_repository", type=str)
  runner.add_argument("--use_but", type=bool, nargs="?", const=True)
  runner.add_argument("--save_but", type=bool, nargs="?", const=True)
  runner.add_argument("--build_only", type=bool, nargs="?", const=True)
  runner.add_argument("--test_only", type=bool, nargs="?", const=True)

  args=parser.parse_args()

  if args.subparsers_name == "bazel_postsubmit_pipeline":
    configs=fetch_configs(args.http_config)
    print_bazel_postsubmit_pipeline(configs.get("platforms", None),
                                    args.http_config)
  elif args.subparsers_name == "project_pipeline":
    configs=fetch_configs(args.http_config)
    print_project_pipeline(configs.get("platforms", None), args.project_name,
                           args.http_config, args.git_repository, args.use_but)
  elif args.subparsers_name == "runner":
    configs=fetch_configs(args.http_config)
    execute_commands(configs.get("platforms", None)[args.platform],
                     args.platform, args.git_repository, args.use_but, args.save_but,
                     args.build_only, args.test_only)
  else:
    parser.print_help()
