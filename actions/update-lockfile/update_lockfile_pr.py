import os
from functions import get_release_prs, get_files_for_pr, update_lockfiles, clone_repo

lockfile_names = {"MODULE.bazel.lock", "src/test/tools/bzlmod/MODULE.bazel.lock"}
original_pr_number = os.environ["PR_NUMBER"]
original_pr_files_list = get_files_for_pr(original_pr_number)
can_proceed = False
for f in original_pr_files_list:
    if f["filename"] in lockfile_names:
        can_proceed = True
        break

if can_proceed == False:
    print("The PR does not contain any lockfile. Therefore, it does not require lockfile updates")
    raise SystemExit(0)

release_branch = os.environ["RELEASE_BRANCH"]

release_version = release_branch.split("release-")[1]

milestone_name = release_version + " release blockers"

# Get a list of the prs made to the release branch 
pr_list = get_release_prs(release_branch)

# Get all the files from each PR and find out if any of the files is a lockfile and update the lockfile if a pr contains any lockfile
requires_clone = True
for pr in pr_list:
    pr["lockfiles"] = set()
    files_list = get_files_for_pr(pr["number"])
    for file in files_list:
        if file["filename"] in lockfile_names:
            pr["lockfiles"].add(file["filename"])
    if len(pr["lockfiles"]) > 0:
        if requires_clone == True: clone_repo()
        try:
            update_lockfiles(pr["lockfiles"], pr["head"]["ref"], release_branch, lockfile_names)
        except Exception as e:
            print(f"Failed updating lockfiles: {pr['number']} in {pr['head']['ref']}")
        requires_clone = False
