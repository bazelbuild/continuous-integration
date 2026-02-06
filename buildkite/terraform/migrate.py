import json
import yaml
import requests
import os

import json
import yaml
import requests
import os
from typing import Any, Dict, List, TextIO


def load_data() -> Any:
    token = os.environ["BUILDKITE_API_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    org_slug = os.environ["BUILDKITE_ORGANIZATION_SLUG"]
    print(f"Importing pipelines under {org_slug}")
    query = r"""query AllPipelinesQuery($org_slug: ID!) {
  organization(slug: $org_slug) {
    name
    slug
    pipelines(first: 500) {
      edges {
        node {
          id
          slug
          name          
          repository {
            url
          }          
          steps {
            yaml
          }  
          description
          defaultBranch
          branchConfiguration
          skipIntermediateBuilds
          skipIntermediateBuildsBranchFilter
          cancelIntermediateBuilds
          cancelIntermediateBuildsBranchFilter
          teams(first: 500) {
            edges {
              node {
                team {
                  slug
                }
                accessLevel
              }
            }
          }
        }
      }
    }
  }
}
"""
    return requests.post(
        "https://graphql.buildkite.com/v1",
        json={"query": query, "variables": {"org_slug": org_slug}},
        headers=headers,
    ).json()


def get_pipeline(org_slug: str, pipeline_slug: str) -> Any:
    token = os.environ["BUILDKITE_API_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(
        f"https://api.buildkite.com/v2/organizations/{org_slug}/pipelines/{pipeline_slug}",
        headers=headers,
    ).json()


def gen_steps(node: Dict[str, Any]) -> str:
    template = 'templatefile("pipeline.yml.tpl", {'

    steps = yaml.safe_load(node["steps"]["yaml"])
    if "env" in steps:
        envs = steps["env"]
        envs_json = json.dumps(envs)
        envs_json = envs_json.replace('"', '\\"')
        template += f' envs = jsondecode("{envs_json}"),'
    else:
        template += " envs = {},"

    template += " steps = {"
    commands = steps["steps"][0]["command"].split("\n")
    commands_json = json.dumps(commands)
    template += f" commands = {commands_json}"

    label = steps["steps"][0]["label"]
    if label != ":pipeline:":
        template += f', label = "{label}"'

    template += " } })"

    return template


def gen_teams(node: Dict[str, Any]) -> str:
    teams = "["
    for team_edge in node["teams"]["edges"]:
        team_node = team_edge["node"]
        team_slug = team_node["team"]["slug"]
        access_level = team_node["accessLevel"]
        team = rf"""{{ access_level = "{access_level}", slug = "{team_slug}" }}"""
        if len(teams) != 1:
            teams += ", "
        teams += team

    teams += "]"
    return teams


def gen_provider_settings(org_slug: str, pipeline_slug: str) -> str:
    pipeline = get_pipeline(org_slug, pipeline_slug)
    provider_settings = pipeline["provider"]["settings"]
    if "trigger_mode" not in provider_settings or provider_settings["trigger_mode"] == "none":
        return ""

    result = "  provider_settings {\n"
    skip_properties = {"repository", "commit_status_error", "build_pull_request_labels_changed"}
    str_properties = {
        "trigger_mode",
        "pull_request_branch_filter_configuration",
        "filter_condition",
    }
    for key, value in provider_settings.items():
        if key in str_properties:
            if value and len(value) > 0:
                value = value.replace('"', '\\"')
                result += f'    {key} = "{value}"\n'
        elif key not in skip_properties:
            if value:
                result += f"    {key} = true\n"
    result += "  }\n"
    return result


def migrate(data: Dict[str, Any], out_tf: TextIO, out_sh: TextIO) -> None:
    org = data["data"]["organization"]
    org_slug = org["slug"]
    for edge in org["pipelines"]["edges"]:
        node = edge["node"]
        id = node["id"]
        slug = node["slug"]

        print(f"Importing pipeline {org_slug}/{slug}...")

        name = node["name"]
        repository = node["repository"]["url"]
        steps = gen_steps(node)
        description = node["description"]
        default_branch = node["defaultBranch"]
        skip_intermediate_builds = "true" if node["skipIntermediateBuilds"] else "false"
        skip_intermediate_builds_branch_filter = node["skipIntermediateBuildsBranchFilter"]
        cancel_intermediate_builds = "true" if node["cancelIntermediateBuilds"] else "false"
        cancel_intermediate_builds_branch_filter = node["cancelIntermediateBuildsBranchFilter"]
        branch_configuration = node["branchConfiguration"]
        teams = gen_teams(node)
        provider_settings = gen_provider_settings(org_slug, slug)

        resource = f'resource "buildkite_pipeline" "{slug}" {{\n'
        resource += f'  name = "{name}"\n'
        resource += f'  repository = "{repository}"\n'
        resource += f"  steps = {steps}\n"
        if description:
            resource += f'  description = "{description}"\n'
        if default_branch:
            resource += f'  default_branch = "{default_branch}"\n'
        if branch_configuration:
            resource += f'  branch_configuration = "{branch_configuration}"\n'
        if skip_intermediate_builds == "true":
            resource += f"  skip_intermediate_builds = {skip_intermediate_builds}\n"
        if skip_intermediate_builds_branch_filter:
            resource += f'  skip_intermediate_builds_branch_filter = "{skip_intermediate_builds_branch_filter}"\n'
        if cancel_intermediate_builds == "true":
            resource += f"  cancel_intermediate_builds = {cancel_intermediate_builds}\n"
        if cancel_intermediate_builds_branch_filter:
            resource += f'  cancel_intermediate_builds_branch_filter = "{cancel_intermediate_builds_branch_filter}"\n'
        if teams != "[]":
            resource += f"  team = {teams}\n"

        resource += provider_settings
        resource += "}\n\n"

        out_tf.write(resource)

        imp = rf"""
terraform import buildkite_pipeline.{slug} {id}
"""
        out_sh.write(imp)


def main() -> None:
    data = load_data()
    with open("out.tf", "w+") as out_tf:
        with open("out.sh", "w+") as out_sh:
            migrate(data, out_tf, out_sh)


if __name__ == "__main__":
    main()
