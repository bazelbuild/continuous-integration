import json
import urllib.request

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
        return json.loads(resp.read())