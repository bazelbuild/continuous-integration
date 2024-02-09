import os, subprocess

# subprocess.run(["git", "cherry-pick", "777868b3dd"])
# check_unmerged_files = str(subprocess.Popen(["git", "diff", "--name-only", "--diff-filter=U"], stdout=subprocess.PIPE).communicate()[0].decode())
# print(check_unmerged_files)

# if "actions/cherry_picker/action.yml" in check_unmerged_files:
#     print("yes")

# if "src/test/tools/bzlmod/MODULE.bazel.lock" in check_unmerged_files:
#     update_lockfile_status = subprocess.run(["../bazelisk-linux-amd64", "run", "//src/test/tools/bzlmod:update_default_lock_file"])
# elif "MODULE.bazel.lock" in check_unmerged_files:
#     update_lockfile_status = subprocess.run(["../bazelisk-linux-amd64", "mod", "deps", "--lockfile_mode=update"])
# else:
#     return
# if update_lockfile_status.returncode != 0: raise Exception("Error updating the lockfile...")
# git_add_status = subprocess.run(["git", "diff", "--exit-code"])
# if git_add_status.returncode == 0: raise Exception("There is nothing to add although 'bazel mod deps --lockfile_mode=update' was run...")
# subprocess.run(["git", "add", "."])
# subprocess.run(["git", "commit", "-m", "'Updated the MODULE.bazel.lock'"])

# subprocess.run(["echo", "7.0.2", ">", ".bazelversion"], shell=True, capture_output=True, text=True)

# subprocess.call("echo 7.0.2 > .bazelversion", shell=True)

# unmerged_files = str(subprocess.Popen(["git", "diff", "--name-only", "--diff-filter=U"], stdout=subprocess.PIPE).communicate()[0].decode())

# unmerged_files = str(subprocess.Popen(["git", "diff", "--name-only", "--diff-filter=U"], stdout=subprocess.PIPE).communicate()[0].decode())


lockfile_names = ["actions/cherry_picker/functions.py"]
# unmerged_all_files = str(subprocess.Popen(["git", "diff", "--name-only", "--diff-filter=U"], stdout=subprocess.PIPE).communicate()[0].decode()).split("\n")
unmerged_all_files = ["actions/cherry_picker/functions.py", "actions/sandbox.py", "zzz"]
unmerged_rest = [j for i,j in enumerate(unmerged_all_files) if j not in lockfile_names]



print("Hey")
print(unmerged_all_files)
print("bye")
print(unmerged_rest)




