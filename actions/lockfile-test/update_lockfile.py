import os, requests, subprocess
token = os.environ["GH_TOKEN"]
# github_dir = os.environ["GITHUB_WORKSPACE"]

print("Cloning and syncing the repo...")
# print(github_dir)
# subprocess.run(['gh', 'repo', 'sync', gh_cli_repo_name, "-b", master_branch])
# subprocess.run(['gh', 'repo', 'sync', gh_cli_repo_name, "-b", release_branch_name])
subprocess.run(['git', 'clone', f"https://bazel-io:{token}@github.com/iancha1992/bazel.git"])
subprocess.run(['git', 'config', '--global', 'user.name', "bazel-io"])
subprocess.run(['git', 'config', '--global', 'user.email', "bazel-io-bot@google.com"])
os.chdir("bazel")
subprocess.run(['git', 'remote', 'add', 'origin', "git@github.com:iancha1992/bazel.git"])
subprocess.run(['git', 'remote', '-v'])

subprocess.run(["bazelisk-linux-amd64", "run", "//src/test/tools/bzlmod:update_default_lock_file"])
subprocess.run(["git", "add", ".", "Testing!"])
subprocess.run(["git", "commit", "-m", "Testing!"])
subprocess.run(["git", "push"])



# "${GITHUB_WORKSPACE}/bin/bazel" run //src/test/tools/bzlmod:update_default_lock_file
# "${GITHUB_WORKSPACE}/bin/bazel" mod deps --lockfile_mode=update
