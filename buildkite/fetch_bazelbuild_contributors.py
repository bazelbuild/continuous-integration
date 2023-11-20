#!/usr/bin/env python3
#
# Copyright 2023 The Bazel Authors. All rights reserved.
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

import requests
import json
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_github_api_response(url, headers):
    logging.info(f"Fetching data from {url}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logging.error(f"Failed to fetch data: {response.text}")
        return []

    data = response.json()

    if isinstance(data, dict):  # In case the response is an error message or a single object
        logging.error(f"Unexpected response format: {data}")
        return []

    if 'next' in response.links.keys():
        data.extend(get_github_api_response(response.links['next']['url'], headers))

    return data

def get_repositories(org, headers):
    url = f"https://api.github.com/orgs/{org}/repos?type=all&per_page=100"
    repos = get_github_api_response(url, headers)
    return [repo['name'] for repo in repos]

def get_contributors(org, repo, headers):
    url = f"https://api.github.com/repos/{org}/{repo}/contributors?per_page=100"
    contributors = get_github_api_response(url, headers)
    return [contributor['login'] for contributor in contributors]

def save_to_json(data, filename):
    sorted_data = {repo: sorted(data[repo]) for repo in sorted(data)}
    logging.info(f"Saving data to {filename}")
    with open(filename, 'w') as file:
        json.dump(sorted_data, file, indent=4)

def main():
    org = "bazelbuild"
    token = os.getenv('GITHUB_TOKEN')

    if not token:
        logging.error("GitHub token not found in environment variables. Please set GITHUB_TOKEN.")
        return

    headers = {'Authorization': f'token {token}'}

    logging.info(f"Retrieving repositories for organization: {org}")
    repositories = get_repositories(org, headers)
    all_contributors = {}

    for repo in repositories:
        logging.info(f"Processing repository: {repo}")
        contributors = get_contributors(org, repo, headers)
        all_contributors[repo] = contributors

    save_to_json(all_contributors, 'contributors.json')
    logging.info("Script completed successfully")

if __name__ == "__main__":
    main()
