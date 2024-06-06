#!/usr/bin/env python3

import subprocess
import requests
import json
import os
import sys

# Get the Buildkite API token from environment variable
BUILDKITE_API_TOKEN = os.getenv('BUILDKITE_API_TOKEN')

if BUILDKITE_API_TOKEN is None:
    raise EnvironmentError('The environment variable BUILDKITE_API_TOKEN is not set.')

# Define constants
PIPELINE_SLUG = 'publish-bazel-binaries-platform'
ORGANIZATION_SLUG = 'bazel-trusted'
BRANCH = 'master'  # Adjust branch as necessary

# Get all commits since the specified commit
def get_commits(start_commit, end_commit):
    result = subprocess.run(
        ['git', 'log', '--format=%H', f'{start_commit}..{end_commit}'],
        stdout=subprocess.PIPE,
        text=True
    )
    commits = result.stdout.strip().split('\n')
    return commits

# Trigger the Buildkite pipeline for a specific commit
def trigger_build(commit):
    url = f'https://api.buildkite.com/v2/organizations/{ORGANIZATION_SLUG}/pipelines/{PIPELINE_SLUG}/builds'
    headers = {
        'Authorization': f'Bearer {BUILDKITE_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'commit': commit,
        'branch': BRANCH,
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        print(f'Successfully triggered build for commit: {commit}')
    else:
        print(f'Failed to trigger build for commit: {commit}, status code: {response.status_code}, response: {response.text}')

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <start_commit> <end_commit>")
        sys.exit(1)
    
    start_commit = sys.argv[1]
    end_commit = sys.argv[2]
    
    commits = get_commits(start_commit, end_commit)
    for commit in commits:
        trigger_build(commit)

if __name__ == '__main__':
    main()

