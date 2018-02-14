import argparse
import codecs
import json
import os.path
import shutil
import subprocess
import sys
import urllib.request
from shutil import copyfile
from urllib.parse import urlparse

OUTPUT_DIRECTORY = ".bazelci_outputs/"
BEP_OUTPUT_FILENAME = OUTPUT_DIRECTORY + "test.json"

def supported_platforms():
    return {
        "ubuntu1404" : "Ubuntu 14.04", 
        "ubuntu1604" : "Ubuntu 16.04",
        "macos" : "macOS"
    }

def fetch_configs(http_config):
    if http_config is None:
        with open(".bazelci/config.json", "r") as fd:
            return json.load(fd)
    with urllib.request.urlopen(http_config) as resp:
        reader = codecs.getreader("utf-8")
        return json.load(reader(resp))

def run(config, platform, bazel_binary, git_repository):
    try:
        if git_repository:
            clone_repository(git_repository)
            cleanup(bazel_binary)
        else:
            cleanup(bazel_binary)
        os.mkdir(OUTPUT_DIRECTORY)
        shell_commands(config.get("shell_commands", None))
        bazel_run(bazel_binary, config.get("run_targets", None))
        bazel_build(bazel_binary, config.get("build_flags", []), config.get("build_targets", None))
        exit_code = bazel_test(bazel_binary, config.get("test_flags", []), config.get("test_targets", None))
        upload_failed_test_logs(BEP_OUTPUT_FILENAME)
        if git_repository:
            delete_repository(git_repository)
        exit(exit_code)
    finally:
        cleanup(bazel_binary)

def clone_repository(git_repository):
    run_command(["git", "clone", git_repository, "downstream-repo"])
    os.chdir("downstream-repo")

def delete_repository(git_repository):
    os.chdir("..")
    shutil.rmtree("downstream-repo")

def shell_commands(commands):
    if not commands:
        return
    print("--- Shell Commands")
    shell_command = "\n".join(commands)
    run_command(shell_command, shell=True)

def bazel_run(bazel_binary, targets):
    if not targets:
        return
    print("--- Run Targets")
    for target in targets:
        run_command([bazel_binary, "run", target])

def bazel_build(bazel_binary, flags, targets):
    if not targets:
        return
    print("+++ Build")
    run_command([bazel_binary, "build", "--color=yes"] + flags + targets)

def bazel_test(bazel_binary, flags, targets):
    if not targets:
        return
    print("+++ Test")
    res = subprocess.run([bazel_binary, "test", "--color=yes", "--build_event_json_file=" + BEP_OUTPUT_FILENAME] + flags + targets)
    return res.returncode

def upload_failed_test_logs(bep_path):
    for logfile in failed_test_logs(bep_path):
        run_command(["buildkite-agent", "artifact", "upload", logfile])

def failed_test_logs(bep_path):
    test_logs = []
    raw_data = ""
    with open(bep_path) as f:
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
                        new_path = label_to_path(json_dict["id"]["testResult"]["label"])
                        os.makedirs(os.path.dirname(new_path), exist_ok=True)
                        copyfile(urlparse(output["uri"]).path, new_path)
                        test_logs.append(new_path)
        pos += size + 1
    return test_logs

def label_to_path(label):
  # remove leading //
  path = label[2:]
  path = path.replace(":", "/")
  return OUTPUT_DIRECTORY + path + ".log"

def cleanup(bazel_binary):
    print("--- Cleanup")
    if os.path.exists("WORKSPACE"):
        run_command([bazel_binary, "clean", "--expunge"])
    if os.path.exists(OUTPUT_DIRECTORY):
        shutil.rmtree(OUTPUT_DIRECTORY)
    if os.path.exists("downstream-repo"):
        shutil.rmtree("downstream-repo")

def run_command(args, shell=False):
    print(" ".join(args))
    res = subprocess.run(args, shell)
    if res.returncode != 0:
        exit(res.returncode)

def generate_pipeline(configs, http_config):
    if not configs:
        print("The CI config is empty.")
        exit(1)
    pipeline_steps = []
    for platform, config in configs.items():
        if platform not in supported_platforms():
            print("'{0}' is not a supported platform on Bazel CI".format(platform))
            exit(1)
        pipeline_steps.append(command_step(supported_platforms()[platform], platform, http_config))
    if not pipeline_steps:
        print("The CI config is empty.")
        exit(1)
    write_pipeline_file(pipeline_steps)

def write_pipeline_file(steps):
    print("steps:")
    for step in steps:
        print(step)

def command_step(label, platform, http_config):
  return """
 - label: \"{0}\"
   command: \"curl -s https://raw.githubusercontent.com/bazelbuild/continuous-integration/master/buildkite/pipelines/bazelci.py > bazelci.py\\n{1}\"
   agents:
     - \"os={2}\"""".format(label, "{0} --platform={1} {2} ".format(runner_command(platform), platform, http_config_flag(http_config)), platform)

def runner_command(platform):
    return "python3 bazelci.py --runner=true"

def http_config_flag(http_config):
    if http_config is not None:
        return "--http_config=" + http_config
    return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bazel Continous Integration Runner')
    parser.add_argument("--generate_pipeline", type=bool)
    parser.add_argument("--runner", type=bool)
    parser.add_argument("--platform", type=str, help="The platform the script is running on. Required.")
    parser.add_argument("--bazel_binary", type=str, help="The path to the Bazel binary. Optional.")
    parser.add_argument("--http_config", type=str, help="The URL of the config file. Optional.")
    args = parser.parse_args()

    if args.generate_pipeline:
        configs = fetch_configs(args.http_config)
        generate_pipeline(configs.get("platforms", None), args.http_config)
    elif args.runner:
        configs = fetch_configs(args.http_config)
        bazel_binary = "bazel"
        if args.bazel_binary is not None:
            bazel_binary = args.bazel_binary
        git_repository = configs.get("git_repository", None)
        if args.platform not in configs["platforms"]:
            print("No configuration exists for '{0}'".format(args.platform))
        run(configs["platforms"][args.platform], args.platform, bazel_binary, git_repository)
    else:
        print("Need to specify either --runner or --generate_pipeline")
        exit(1)
