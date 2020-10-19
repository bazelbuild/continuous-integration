#!/usr/bin/env python3
#
# Requirements:
# - Install dependencies: `pip3 install pybuildkite requests`
# - Get a Buildkite API token with read_agents and write_agents permissions
#   and put it into the BUILDKITE_TOKEN environment variable.
# - Optional: Modify "FILTER" below to restart different groups of agents.
#   For example, you can put "windows" there to restart Windows agents.

import os
from pybuildkite.buildkite import Buildkite
from requests.exceptions import HTTPError

FILTER = "docker"
ORGANIZATION = "bazel"

print("Using Buildkite API Token: {}".format(os.environ["BUILDKITE_TOKEN"]))

buildkite = Buildkite()
buildkite.set_access_token(os.environ["BUILDKITE_TOKEN"])

response = buildkite.agents().list_all(
    organization=ORGANIZATION, page=1, with_pagination=True
)
agents = response.body

# Keep looping until next_page is not populated
while response.next_page:
    response = buildkite.agents().list_all(
        organization=ORGANIZATION, page=response.next_page, with_pagination=True
    )
    agents += response.body

for agent in agents:
    if FILTER in agent["name"]:
        print(
            "Stopping agent {} (https://buildkite.com/organizations/{}/agents/{}): ".format(
                agent["name"], ORGANIZATION, agent["id"]
            ),
            end="",
        )
        try:
            buildkite.agents().stop_agent(
                organization=ORGANIZATION, agent_id=agent["id"], force=False
            )
        except HTTPError:
            print("Error")
        else:
            print("OK")
