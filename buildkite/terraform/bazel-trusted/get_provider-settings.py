import re
import requests
import sys
import os

# Configuration
API_TOKEN = "bkua_b53978e5f05c755074e9359d26bef470dd1511c1"
ORG_SLUG = "bazel-trusted"
TF_FILE = "main.tf"

HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

def get_pipeline_settings(pipeline_slug):
    url = f"https://api.buildkite.com/v2/organizations/{ORG_SLUG}/pipelines/{pipeline_slug}"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json().get("provider", {}).get("settings", {})
        print(f"  [!] API Error for {pipeline_slug}: {response.status_code}")
    except Exception as e:
        print(f"  [!] Connection error: {e}")
    return None

def format_provider_settings(settings):
    mapping = {
    # Core behavior (Triggering)
    "trigger_mode": "trigger_mode",
    "build_branches": "build_branches",
    "build_pull_requests": "build_pull_requests",
    "build_tags": "build_tags",

    # GitHub PR & Fork Customizations
    "build_pull_request_forks": "build_pull_request_forks",
    "build_pull_request_ready_for_review": "build_pull_request_ready_for_review",
    "build_pull_request_labels_changed": "build_pull_request_labels_changed",
    "build_pull_request_base_branch_changed": "build_pull_request_base_branch_changed",
    "prefix_pull_request_fork_branch_names": "prefix_pull_request_fork_branch_names",

    # Filtering Logic (The "Brain" of your pipeline)
    "filter_enabled": "filter_enabled",
    "filter_condition": "filter_condition",
    "pull_request_branch_filter_enabled": "pull_request_branch_filter_enabled",
    "pull_request_branch_filter_configuration": "pull_request_branch_filter_configuration",

    # GitHub Status & Feedback
    "publish_commit_status": "publish_commit_status",
    "publish_commit_status_per_step": "publish_commit_status_per_step",
    "separate_pull_request_statuses": "separate_pull_request_statuses",
    "publish_blocked_as_pending": "publish_blocked_as_pending",

    # Resource Management & Build Logic
    "cancel_deleted_branch_builds": "cancel_deleted_branch_builds",
    "skip_builds_for_existing_commits": "skip_builds_for_existing_commits",
    "skip_pull_request_builds_for_existing_commits": "skip_pull_request_builds_for_existing_commits",

    # Advanced 
    "ignore_default_branch_pull_requests": "ignore_default_branch_pull_requests",
    "build_merge_group_checks_requested": "build_merge_group_checks_requested",
    "cancel_when_merge_group_destroyed": "cancel_when_merge_group_destroyed",
    "use_merge_group_base_commit_for_git_diff_base": "use_merge_group_base_commit_for_git_diff_base"
}
    
    lines = ["  provider_settings = {"]
    for api_key, tf_key in mapping.items():
        val = settings.get(api_key)
        if val is None: continue
        
        # Format HCL values
        if isinstance(val, bool):
            v = str(val).lower()
        elif isinstance(val, str):
            v = '"' + val.replace('"', '\\"') + '"'
        else:
            v = val
        lines.append(f"    {tf_key.ljust(45)} = {v}")
    lines.append("  }")
    return "\n".join(lines)

def update_tf_file():
    if not os.path.exists(TF_FILE):
        print(f"File {TF_FILE} not found!")
        return

    with open(TF_FILE, "r") as f:
        lines = f.readlines()

    new_lines = []
    current_block = []
    in_pipeline_resource = False
    current_slug = None

    for line in lines:
        # Detect start of a pipeline resource
        res_match = re.match(r'^resource\s+"buildkite_pipeline"\s+"(?P<id>[^"]+)"', line)
        if res_match:
            in_pipeline_resource = True
            current_block = [line]
            current_slug = res_match.group('id')
            continue

        if in_pipeline_resource:
            current_block.append(line)

            # Detect end of resource block by checking for an unindented closing brace
            if line.rstrip() == "}":
                print(f"[*] Found pipeline: {current_slug}")
                
                settings = get_pipeline_settings(current_slug)
                if settings:
                    # Remove existing provider_settings (either = null or block)
                    block_str = "".join(current_block)
                    block_str = re.sub(r'\n\s+provider_settings\s*=\s*null', '', block_str)
                    block_str = re.sub(r'\n\s+provider_settings\s*(?:=\s*)?\{.*?\n\s+\}', '', block_str, flags=re.DOTALL)
                    
                    # Inject new settings before the final brace
                    settings_hcl = format_provider_settings(settings)
                    updated_block = block_str.rstrip().rsplit('}', 1)[0] + settings_hcl + "\n}\n"
                    new_lines.append(updated_block)
                else:
                    new_lines.append("".join(current_block))
                
                in_pipeline_resource = False
                current_block = []
                current_slug = None
        else:
            new_lines.append(line)

    with open(TF_FILE, "w") as f:
        f.writelines(new_lines)
    print("\n[Done] Process complete.")

if __name__ == "__main__":
    update_tf_file()