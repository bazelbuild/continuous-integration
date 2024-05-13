import os

headers = {
    'X-GitHub-Api-Version': '2022-11-28'
}

token = os.environ["GH_TOKEN"]


if "INPUT_IS_PROD" not in os.environ or os.environ["INPUT_IS_PROD"] == "false":
    input_data = {
        "is_prod": False,
        "api_repo_name": "iancha1992/bazel",
        "user_name": "iancha1992",
        "email": "heec@google.com",
    }

elif os.environ["INPUT_IS_PROD"] == "true":
    input_data = {
        "is_prod": True,
        "api_repo_name": "bazelbuild/bazel",
        "user_name": "bazel-io",
        "email": "bazel-io-bot@google.com",
    }

gh_cli_repo_name = f"{input_data['user_name']}/bazel"
gh_cli_repo_url = f"git@github.com:{gh_cli_repo_name}.git"
