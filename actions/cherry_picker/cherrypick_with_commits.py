import os, re
from vars import input_data, upstream_repo, cherrypick_with_commits_infos
from functions import cherry_pick, create_pr, issue_comment, get_pr_body, PushCpException, push_to_branch, get_middle_text

milestone_title = os.environ["INPUT_MILESTONE_TITLE"]
milestoned_issue_number = os.environ["INPUT_MILESTONED_ISSUE_NUMBER"]
issue_title = os.environ['INPUT_ISSUE_TITLE']
issue_body = os.environ["INPUT_ISSUE_BODY"]
commits_text = cherrypick_with_commits_infos["commits"]
team_labels_text = cherrypick_with_commits_infos["team_labels"]
reviewers_text = cherrypick_with_commits_infos["reviewers"]
issue_body_dict = {}
issue_body_dict["commits"] = get_middle_text(issue_body, commits_text["left"], commits_text["right"]).replace(" ", "").split(",")

for commit_index in range(len(issue_body_dict["commits"])):
    issue_body_dict["commits"][commit_index] = re.sub(r'https://.*/commit/', "", issue_body_dict["commits"][commit_index])

issue_body_dict["labels"] = get_middle_text(issue_body, team_labels_text["left"], team_labels_text["right"]).replace(" ", "").replace("@", "").split(",")
issue_body_dict["reviewers"] = get_middle_text(issue_body, reviewers_text["left"], reviewers_text["right"]).replace(" ", "").replace("@", "").split(",")

release_number = milestone_title.split(" release blockers")[0]
release_branch_name = f"{input_data['release_branch_name_initials']}{release_number}"
target_branch_name = f"cp_ondemand_{milestoned_issue_number}-{release_number}"
head_branch_name = f"{input_data['user_name']}:{target_branch_name}"
reviewers = issue_body_dict["reviewers"]
labels = issue_body_dict["labels"]
requires_clone = True
requires_checkout = True
successful_commits = []
failed_commits = []

for idx, commit_id in enumerate(issue_body_dict["commits"]):
    try:
        cherry_pick(commit_id, release_branch_name, target_branch_name, requires_clone, requires_checkout, input_data)
        msg_body = get_pr_body(commit_id, input_data["api_repo_name"])
        success_msg = {"commit_id": commit_id, "msg": msg_body}
        successful_commits.append(success_msg)
    except PushCpException as pe:
        issue_comment(milestoned_issue_number, str(pe), input_data["api_repo_name"], input_data["is_prod"])
        raise SystemExit(0)
    except Exception as e:
        failed_commits.append(commit_id)
    requires_clone = False
    requires_checkout = False

try:
    push_to_branch(target_branch_name)
except Exception as e:
    issue_comment(milestoned_issue_number, str(e), input_data["api_repo_name"], input_data["is_prod"])
    raise SystemExit(0)

issue_comment_body = ""
if len(successful_commits):
    if len(successful_commits) >= 2:
        pr_body = f"This PR contains {len(successful_commits)} commit(s).\n\n"
        for idx, commit in enumerate(successful_commits):
            pr_body += str((idx + 1)) + ")" + commit["msg"] + "\n\n"
    elif len(successful_commits) == 1:
        pr_body = f"{successful_commits[0]['msg']}"
    if "awaiting-review" not in labels: labels.append("awaiting-review")
    cherry_picked_pr_number = create_pr(reviewers, release_number, labels, issue_title, pr_body, release_branch_name, target_branch_name, input_data['user_name'])
    issue_comment_body = f"The following commits were cherry-picked in https://github.com/{upstream_repo}/pull/{cherry_picked_pr_number}: "
    for success_commit in successful_commits:
        issue_comment_body += f"https://github.com/{input_data['api_repo_name']}/commit/{success_commit['commit_id']}, "
    issue_comment_body = issue_comment_body[::-1].replace(" ,", ".", 1)[::-1]

    if len(failed_commits):
        failure_commits_str = f"\nFailed commits (likely due to merge conflicts): "
        for fail_commit in failed_commits:
            failure_commits_str += f"https://github.com/{input_data['api_repo_name']}/commit/{fail_commit}, "
        failure_commits_str = failure_commits_str[::-1].replace(" ,", "", 1)[::-1]
        failure_commits_str += "\n\nThe failed commits are NOT included in the PR. Please resolve manually.\ncc: @bazelbuild/triage"
        issue_comment_body += failure_commits_str
elif len(failed_commits):
    issue_comment_body = "Failed commmits (likely due to merge conflicts): "
    for fail_commit in failed_commits:
        issue_comment_body += f"https://github.com/{input_data['api_repo_name']}/commit/{fail_commit}, "
    issue_comment_body = issue_comment_body[::-1].replace(" ,", ".", 1)[::-1] + "\nPlease resolve manually.\ncc: @bazelbuild/triage"
issue_comment(milestoned_issue_number, issue_comment_body, input_data["api_repo_name"], input_data["is_prod"])
