import os, requests, subprocess
token = os.environ["GH_TOKEN"]

print("Cloning and syncing the repo...")
subprocess.run(['git', 'clone', f"https://bazel-io:{token}@github.com/iancha1992/bazel.git"])
subprocess.run(['git', 'config', '--global', 'user.name', "bazel-io"])
subprocess.run(['git', 'config', '--global', 'user.email', "bazel-io-bot@google.com"])
os.chdir("bazel")
subprocess.run(['git', 'remote', 'add', 'origin', "git@github.com:iancha1992/bazel.git"])
subprocess.run(['git', 'remote', '-v'])

# subprocess.run(["../bazelisk-linux-amd64", "run", "//src/test/tools/bzlmod:update_default_lock_file"])
print("Create hiword.txt")
subprocess.run(["touch", "hiword.txt"])
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Testing!"])
subprocess.run(["git", "push"])

