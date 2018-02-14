import argparse
from common import supported_platforms
from common import fetch_configs

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
   command: \"{1}\"
   agents:
     - \"os={2}\"""".format(label, "{0} --platform={1} {2} ".format(runner_command(platform), platform, http_config_flag(http_config)), platform)

def runner_command(platform):
    return "python3 buildkite/pipelines/runner.py"

def http_config_flag(http_config):
    if http_config is not None:
        return "--http_config=" + http_config
    return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bazel Continous Integration Pipeline Generator')
    parser.add_argument("--http_config", type=str, help="The URL of the config file. Optional.")
    args = parser.parse_args()

    configs = fetch_configs(args.http_config)
    generate_pipeline(configs.get("platforms", None), args.http_config)
