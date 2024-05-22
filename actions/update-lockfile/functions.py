import requests, subprocess, os, re, pprint
from vars import headers, token, gh_cli_repo_name, input_data, gh_cli_repo_url

def get_release_prs(release_branch):
    page_param = 1
    params = {
        "state": "open",
        "base": release_branch,
        "per_page": 100,
        "page": page_param
    }
    pr_list = []
    response_pr = requests.get(f"https://api.github.com/repos/{gh_cli_repo_name}/pulls", headers=headers, params=params).json()
    pr_list.extend(response_pr)
    while len(response_pr) == 100:
        page_param += 1
        response_pr = requests.get(f"https://api.github.com/repos/{gh_cli_repo_name}/pulls", headers=headers, params=params).json()
        pr_list.extend(response_pr)
    return list(filter(lambda n: n["user"]["login"] == input_data["user_name"], pr_list))

def get_files_for_pr(pr_number):
    page_param = 1
    params = {
        "per_page": 100,
        "page": page_param,
    }
    files_list = []
    response_pr_files = requests.get(f"https://api.github.com/repos/{gh_cli_repo_name}/pulls/{pr_number}/files", headers=headers, params=params).json()
    files_list.extend(response_pr_files)
    while len(response_pr_files) == 100:
        page_param += 1
        response_pr_files = requests.get(f"https://api.github.com/repos/{gh_cli_repo_name}/pulls/{pr_number}/files", headers=headers, params=params).json()
        files_list.extend(response_pr_files)
    return files_list

def clone_repo():
    subprocess.run(['git', 'clone', f"https://{input_data['user_name']}:{token}@github.com/{gh_cli_repo_name}.git"])
    subprocess.run(['git', 'config', '--global', 'user.name', input_data["user_name"]])
    subprocess.run(['git', 'config', '--global', 'user.email', input_data["email"]])
    os.chdir("bazel")
    subprocess.run(['git', 'remote', 'add', 'origin', gh_cli_repo_url])
    subprocess.run(['git', 'remote', '-v'])

def checkout_branch(head_branch, release_branch):
    subprocess.run(['git', 'fetch', '--all'])
    subprocess.run(['git', 'checkout', release_branch])
    subprocess.run(['git', 'pull'])

    status_checkout_release = subprocess.run(['git', 'checkout', head_branch])
    return status_checkout_release

def push_to_branch():
    push_status = subprocess.run(['git', 'push', '-f'])
    if push_status.returncode != 0: raise Exception(f"Cherry-pick was attempted, but failed to push.\ncc: @bazelbuild/triage")

def update_lockfiles(lockfiles, head_branch, release_branch, lockfile_names):
    if checkout_branch(head_branch, release_branch).returncode != 0:
        print(f"{input_data['user_name']} does not have the branch: {head_branch}...")
        return
    std_out_bazel_version = subprocess.Popen(["../bazelisk-linux-amd64", "--version"], stdout=subprocess.PIPE)
    bazel_version_std_out = std_out_bazel_version.communicate()[0].decode()
    major_version_digit = int(re.findall(r"\d.\d.\d", bazel_version_std_out)[0].split(".")[0])

    if major_version_digit < 7:
        print("Warning: The .bazelversion is less than 7. Therefore, the lockfiles will not be updated...")
        return
    
    rebase_status = subprocess.run(["git", "rebase", f"origin/{release_branch}"])
    if rebase_status.returncode != 0:
        unmerged_all_files = str(subprocess.Popen(["git", "diff", "--name-only", "--diff-filter=U"], stdout=subprocess.PIPE).communicate()[0].decode()).split("\n")
        unmerged_rest = [j for i, j in enumerate(unmerged_all_files) if j not in lockfile_names and j != ""]
        if len(unmerged_rest) != 0:
            print("Could not rebase because of conflicts with files other than the lockfiles")
        else:
            print("There was conflicts with lockfiles only...")
            allowed_rebase_continue_attempts = 2
            while allowed_rebase_continue_attempts > 0:
                for f in lockfile_names:
                    subprocess.run(["git", "checkout", "--ours", f])
                subprocess.run(["git", "add", "."])
                rebase_continue_status = subprocess.run(["git", "-c", "core.editor=true", "rebase", "--continue"])
                if rebase_continue_status.returncode == 0:
                    if "src/test/tools/bzlmod/MODULE.bazel.lock" in lockfiles:
                        subprocess.run(["../bazelisk-linux-amd64", "run", "//src/test/tools/bzlmod:update_default_lock_file"])
                    subprocess.run(["../bazelisk-linux-amd64", "mod", "deps", "--lockfile_mode=update"])
                    subprocess.run(["git", "add", "."])
                    subprocess.run(["git", "commit", "-m", "Update lockfile(s)"])
                    push_to_branch()
                    return
                allowed_rebase_continue_attempts -= 1
        subprocess.run(['git', 'rebase', '--abort'])
    else:
        if "src/test/tools/bzlmod/MODULE.bazel.lock" in lockfiles:
            subprocess.run(["../bazelisk-linux-amd64", "run", "//src/test/tools/bzlmod:update_default_lock_file"])
        subprocess.run(["../bazelisk-linux-amd64", "mod", "deps", "--lockfile_mode=update"])
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", "Update lockfile(s)"])
        push_to_branch()
