import argparse
import json
import os.path
import shutil
import subprocess
import sys
from common import fetch_configs
from common import OUTPUT_DIRECTORY
from common import BEP_OUTPUT_FILENAME
from urllib.parse import urlparse

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bazel Continous Integration Runner')
    parser.add_argument("--platform", type=str, required=True, help="The platform the script is running on. Required.")
    parser.add_argument("--bazel_binary", type=str, help="The path to the Bazel binary. Optional.")
    parser.add_argument("--http_config", type=str, help="The URL of the config file. Optional.")
    args = parser.parse_args()

    configs = fetch_configs(args.http_config)
    bazel_binary = "bazel"
    if args.bazel_binary is not None:
        bazel_binary = args.bazel_binary
    git_repository = configs.get("git_repository", None)
    if args.platform not in configs["platforms"]:
        print("No configuration exists for '{0}'".format(args.platform))
    run(configs["platforms"][args.platform], args.platform, bazel_binary, git_repository)
