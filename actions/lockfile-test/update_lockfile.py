import os, requests, subprocess
token = os.environ["GH_TOKEN"]
pr_number = os.environ["PR_NUMBER"]

# print("Cloning and syncing the repo...")
# subprocess.run(['git', 'clone', f"https://bazel-io:{token}@github.com/iancha1992/bazel.git"])
# subprocess.run(['git', 'config', '--global', 'user.name', "bazel-io"])
# subprocess.run(['git', 'config', '--global', 'user.email', "bazel-io-bot@google.com"])
# os.chdir("bazel")
# subprocess.run(['git', 'remote', 'add', 'origin', "git@github.com:iancha1992/bazel.git"])
# subprocess.run(['git', 'remote', '-v'])

# print("checking branches")
# subprocess.run(['git', 'branch'])

# # subprocess.run(["../bazelisk-linux-amd64", "run", "//src/test/tools/bzlmod:update_default_lock_file"])
# print("Create hiword.txt")
# subprocess.run(["touch", "hiword.txt"])
# subprocess.run(["git", "add", "."])
# subprocess.run(["git", "commit", "-m", "Testing!"])
# subprocess.run(["git", "push"])




print("This is the pr number", pr_number)


# New code here
headers = {
    'X-GitHub-Api-Version': '2022-11-28'
}
r = requests.get(f'https://api.github.com/repos/bazelbuild/bazel/pulls/{pr_number}', headers=headers).json()


print("Cloning and syncing the repo...")
subprocess.run(['git', 'clone', f"https://bazel-io:{token}@github.com/bazelbuild/bazel.git"])
subprocess.run(['git', 'config', '--global', 'user.name', "bazel-io"])
subprocess.run(['git', 'config', '--global', 'user.email', "bazel-io-bot@google.com"])
os.chdir("bazel")
# subprocess.run(['git', 'remote', 'add', 'origin', "git@github.com:iancha1992/bazel.git"])
subprocess.run(['git', 'remote', '-v'])

print("checking branches")
subprocess.run(['git', 'branch'])

# subprocess.run(["../bazelisk-linux-amd64", "run", "//src/test/tools/bzlmod:update_default_lock_file"])
print("Create hiword.txt")
subprocess.run(["touch", "hiword.txt"])
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Testing!"])
subprocess.run(["git", "push"])
