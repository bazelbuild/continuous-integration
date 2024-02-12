import os, subprocess, requests, re
from vars import headers, token, upstream_repo, upstream_url

class PushCpException(Exception):
    pass

class UpdateLockfileException(Exception):
    pass

def get_commit_id(pr_number, actor_name, action_event, api_repo_name):
    params = {"per_page": 100}
    response = requests.get(f'https://api.github.com/repos/{api_repo_name}/issues/{pr_number}/events', headers=headers, params=params)
    commit_id = None
    for event in response.json():
        if (event["actor"]["login"] in actor_name) and (event["commit_id"] != None) and (commit_id == None) and (event["event"] == action_event):
            commit_id = event["commit_id"]
        elif (event["actor"]["login"] in actor_name) and (event["commit_id"] != None) and (commit_id != None) and (event["event"] == action_event):
            print(f'PR#{pr_number} has multiple commits made by {actor_name}')
            raise SystemExit(0)
    if commit_id == None:
        print(f'PR#{pr_number} has NO commit made by {actor_name}')
        raise SystemExit(0)
    # return
    return commit_id

def get_reviewers(pr_number, api_repo_name, issues_data):
    if "pull_request" not in issues_data: return []
    r = requests.get(f'https://api.github.com/repos/{api_repo_name}/pulls/{pr_number}/reviews', headers=headers)
    if len(r.json()) == 0:
        print(f"PR#{pr_number} has no approver at all.")
        raise SystemExit(0)
    approvers_list = []
    for review in r.json():
        if review["state"] == "APPROVED": approvers_list.append(review["user"]["login"])
    if len(approvers_list) == 0:
        print(f"PR#{pr_number} has no approval from the approver(s).")
        raise SystemExit(0)
    return approvers_list

def extract_release_numbers_data(pr_number, api_repo_name):

    def get_milestoned_issues(milestones, pr_number):
        results= {}
        for milestone in milestones:
            params = {
                "milestone": milestone["number"]
            }
            r = requests.get(f'https://api.github.com/repos/{api_repo_name}/issues', headers=headers, params=params)
            for issue in r.json():
                if issue["body"] == f'Forked from #{pr_number}' and issue["state"] == "open":
                    results[milestone["title"]] = issue["number"]
                    break
        return results

    response_milestones = requests.get(f'https://api.github.com/repos/{api_repo_name}/milestones', headers=headers)
    all_milestones = list(map(lambda n: {"title": n["title"].split("release blockers")[0].replace(" ", ""), "number": n["number"]}, response_milestones.json()))
    milestoned_issues = get_milestoned_issues(all_milestones, pr_number)
    return milestoned_issues

def issue_comment(issue_number, body_content, api_repo_name, is_prod):
    if is_prod == True:
        subprocess.run(['git', 'remote', 'add', 'upstream', upstream_url])
        subprocess.run(['gh', 'repo', 'set-default', upstream_repo])
        subprocess.run(['gh', 'issue', 'comment', str(issue_number), '--body', body_content])
        subprocess.run(['git', 'remote', 'rm', 'upstream'])
        subprocess.run(['gh', 'repo', 'set-default', api_repo_name])
    else:
        subprocess.run(['gh', 'issue', 'comment', str(issue_number), '--body', body_content])

def update_lockfile(changed_files, has_conflicts):
    std_out_bazel_version = subprocess.Popen(["../bazelisk-linux-amd64", "--version"], stdout=subprocess.PIPE)
    bazel_version_std_out = std_out_bazel_version.communicate()[0].decode()
    major_version_digit = int(re.findall(r"\d.\d.\d", bazel_version_std_out)[0].split(".")[0])
    if major_version_digit < 7:
        print("Warning: The .bazelversion is less than 7. Therefore, the lockfiles may not be updated...")
        raise Exception(f"The bazel major version is {bazel_version_std_out}. We cannot use bazel to update the lockfiles.")
    
    if has_conflicts == True:
        subprocess.run(["git", "checkout", "--theirs", "MODULE.bazel.lock", "src/test/tools/bzlmod/MODULE.bazel.lock"])
        subprocess.run(["git", "add", "."])

    if "src/test/tools/bzlmod/MODULE.bazel.lock" in changed_files:
        print("src/test/tools/bzlmod/MODULE.bazel.lock needs to be updated. This may take awhile... Please be patient.")
        subprocess.run(["../bazelisk-linux-amd64", "run", "//src/test/tools/bzlmod:update_default_lock_file"])
        subprocess.run(["git", "add", "."])

    print("Updating the lockfile(s)...")
    subprocess.run(["../bazelisk-linux-amd64", "mod", "deps", "--lockfile_mode=update"])
    subprocess.run(["git", "add", "."])

    # If there was a conflict, then run this
    if has_conflicts == True:
        subprocess.run(["git", "-c", "core.editor=true", "cherry-pick", "--continue"])

def cherry_pick(commit_id, release_branch_name, target_branch_name, requires_clone, requires_checkout, input_data):
    gh_cli_repo_name = f"{input_data['user_name']}/bazel"
    gh_cli_repo_url = f"git@github.com:{gh_cli_repo_name}.git"
    master_branch = input_data["master_branch"]
    user_name = input_data["user_name"]
    user_email = input_data["email"]

    def clone_and_sync_repo(gh_cli_repo_name, master_branch, release_branch_name, user_name, gh_cli_repo_url, user_email):
        print("Cloning and syncing the repo...")
        subprocess.run(['gh', 'repo', 'sync', gh_cli_repo_name, "-b", master_branch])
        subprocess.run(['gh', 'repo', 'sync', gh_cli_repo_name, "-b", release_branch_name])
        subprocess.run(['git', 'clone', f"https://{user_name}:{token}@github.com/{gh_cli_repo_name}.git"])
        subprocess.run(['git', 'config', '--global', 'user.name', user_name])
        subprocess.run(['git', 'config', '--global', 'user.email', user_email])
        os.chdir("bazel")
        print("pwd")
        subprocess.run(['pwd'])
        print("ls")
        subprocess.run(['ls'])
        print("ls ..")
        subprocess.run(['ls', '..'])
        print("cat .bazelversion")
        subprocess.run(['cat', '.bazelversion'])
        subprocess.run(['git', 'remote', 'add', 'origin', gh_cli_repo_url])
        subprocess.run(['git', 'remote', '-v'])

    def checkout_release_number(release_branch_name, target_branch_name):
        subprocess.run(['git', 'fetch', '--all'])
        status_checkout_release = subprocess.run(['git', 'checkout', release_branch_name])
        
        # Create the new release branch from the upstream if not exists already.
        if status_checkout_release.returncode != 0:
            print(f"There is NO branch called {release_branch_name}...")
            print(f"Creating the {release_branch_name} from upstream, {upstream_url}")
            subprocess.run(['git', 'remote', 'add', 'upstream', upstream_url])
            subprocess.run(['git', 'remote', '-v'])
            subprocess.run(['git', 'fetch', 'upstream'])
            subprocess.run(['git', 'branch', release_branch_name, f"upstream/{release_branch_name}"])
            release_push_status = subprocess.run(['git', 'push', '--set-upstream', 'origin', release_branch_name])
            if release_push_status.returncode != 0:
                raise Exception(f"The branch, {release_branch_name}, may not exist. Please retry the cherry-pick after the branch is created.")
            subprocess.run(['git', 'remote', 'rm', 'upstream'])
            subprocess.run(['git', 'checkout', release_branch_name])
        status_checkout_target = subprocess.run(['git', 'checkout', '-b', target_branch_name])
        if status_checkout_target.returncode != 0: raise Exception(f"Cherry-pick was being attempted. But, it failed due to already existent branch called {target_branch_name}\ncc: @bazelbuild/triage")

    def run_cherry_pick(is_prod, commit_id, target_branch_name):
        print(f"Cherry-picking the commit id {commit_id} in CP branch: {target_branch_name}")
        if is_prod == True:
            cherrypick_status = subprocess.run(['git', 'cherry-pick', commit_id])
        else:
            cherrypick_status = subprocess.run(['git', 'cherry-pick', '-m', '1', commit_id])
        lockfile_names = ["src/test/tools/bzlmod/MODULE.bazel.lock", "MODULE.bazel.lock", ""]
        unmerged_all_files = str(subprocess.Popen(["git", "diff", "--name-only", "--diff-filter=U"], stdout=subprocess.PIPE).communicate()[0].decode()).split("\n")
        unmerged_rest = [j for i,j in enumerate(unmerged_all_files) if j not in lockfile_names]
        changed_files = str(subprocess.Popen(["git", "diff", "--name-only"], stdout=subprocess.PIPE).communicate()[0].decode()).split("\n")
        print("This is the changed files")
        print(changed_files)

        if cherrypick_status.returncode != 0 and "src/test/tools/bzlmod/MODULE.bazel.lock" not in changed_files and "MODULE.bazel.lock" not in changed_files:
            subprocess.run(['git', 'cherry-pick', '--skip'])
            raise Exception("Cherry-pick was attempted, but there may be merge conflict(s). Please resolve manually.\ncc: @bazelbuild/triage")
        elif (cherrypick_status.returncode != 0 and len(unmerged_rest) == 0):
            update_lockfile(changed_files, True)
        elif cherrypick_status.returncode == 0 and ("src/test/tools/bzlmod/MODULE.bazel.lock" in changed_files or "MODULE.bazel.lock" in changed_files):
            update_lockfile(changed_files, False)
        #     update_lockfile(changed_files)
        
    if requires_clone == True: clone_and_sync_repo(gh_cli_repo_name, master_branch, release_branch_name, user_name, gh_cli_repo_url, user_email)
    if requires_checkout == True: checkout_release_number(release_branch_name, target_branch_name)
    run_cherry_pick(input_data["is_prod"], commit_id, target_branch_name)

def push_to_branch(target_branch_name):
    print(f"Pushing it to branch: {target_branch_name}")
    push_status = subprocess.run(['git', 'push', '--set-upstream', 'origin', target_branch_name])
    if push_status.returncode != 0: raise PushCpException(f"Cherry-pick was attempted, but failed to push. Please check if the branch, {target_branch_name}, already exists\ncc: @bazelbuild/triage")

def get_cherry_picked_pr_number(head_branch, release_branch):
    params = {
        "head": head_branch,
        "base": release_branch,
        "state": "open"
    }
    r = requests.get(f'https://api.github.com/repos/{upstream_repo}/pulls', headers=headers, params=params).json()
    if len(r) == 1: return r[0]["number"]
    else: raise Exception(f"Could not find the cherry-picked PR number \ncc: @bazelbuild/triage")

def create_pr(reviewers, release_number, labels, pr_title, pr_body, release_branch_name, target_branch_name, user_name):
    head_branch = f"{user_name}:{target_branch_name}"
    reviewers_str = ",".join(reviewers)
    labels_str = ",".join(labels)
    modified_pr_title = f"[{release_number}] {pr_title}" if f"[{release_number}]" not in pr_title else pr_title
    status_create_pr = subprocess.run(['gh', 'pr', 'create', "--repo", upstream_repo, "--title", modified_pr_title, "--body", pr_body, "--head", head_branch, "--base", release_branch_name,  '--label', labels_str, '--reviewer', reviewers_str])
    if status_create_pr.returncode == 0:
        cherry_picked_pr_number = get_cherry_picked_pr_number(head_branch, release_branch_name)
        return cherry_picked_pr_number
    else: raise Exception("PR failed to be created.")

def get_labels(pr_number, api_repo_name):
    r = requests.get(f'https://api.github.com/repos/{api_repo_name}/issues/{pr_number}/labels', headers=headers)
    labels_list = list(filter(lambda label: "area" in label or "team" in label, list(map(lambda x: x["name"], r.json()))))
    if "awaiting-review" not in labels_list: labels_list.append("awaiting-review")
    return labels_list

def get_pr_title_body(commit_id, api_repo_name):
    response_commit = requests.get(f"https://api.github.com/repos/{api_repo_name}/commits/{commit_id}")
    original_msg = response_commit.json()["commit"]["message"]
    pr_title = original_msg[:original_msg.index("\n\n")] if "\n\n" in original_msg else original_msg
    pr_body = original_msg[original_msg.index("\n\n") + 2:] if "\n\n" in original_msg else original_msg
    commit_str_body = f"Commit https://github.com/{api_repo_name}/commit/{commit_id}"
    if "PiperOrigin-RevId" in pr_body:
        piper_index = pr_body.index("PiperOrigin-RevId")
        pr_body = pr_body[:piper_index] + f"{commit_str_body}\n\n" + pr_body[piper_index:]
    else:
        pr_body += f"\n\n{commit_str_body}"
    return {"title": pr_title, "body": pr_body}

def get_middle_text(all_str, left_str, right_str):
    left_index = all_str.index(left_str) + len(left_str)
    if right_str == None:
        right_index = len(all_str)
    else:
        right_index = all_str.index(right_str)
    return all_str[left_index:right_index]