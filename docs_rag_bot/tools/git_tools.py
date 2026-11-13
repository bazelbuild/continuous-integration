import os
import json
import urllib.request
import urllib.parse
import urllib.error
import base64
import time

def _get_github_headers(accept_header="application/vnd.github.v3+json"):
    token = os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": accept_header, 
        "User-Agent": "DocSync-Agent-v15",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    return headers

def _make_api_request(url, accept_header="application/vnd.github.v3+json", method="GET", data=None):
    headers = _get_github_headers(accept_header)
    req = urllib.request.Request(url, headers=headers, method=method)
    if data:
        req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req) as response:
            return response.read(), response.getcode()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else "No body"
        raise Exception(f"GitHub API Error {e.code}: {e.reason} - {error_body}")
    except Exception as e:
        raise Exception(f"Network Error: {str(e)}")

def fetch_code_diff(pr_url: str) -> str:
    """Fetches PR metadata and code diff."""
    max_chars = 25000
    try:
        parts = pr_url.strip().split("/")
        pr_number = parts[-1]
        owner, repo = parts[-4], parts[-3]
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        meta_content, _ = _make_api_request(url, "application/vnd.github.v3+json")
        meta_data = json.loads(meta_content.decode('utf-8'))
        requested_reviewers = [r['login'] for r in meta_data.get('requested_reviewers', [])]
        reviews_url = f"{url}/reviews"
        reviews_content, _ = _make_api_request(reviews_url)
        reviews_data = json.loads(reviews_content.decode('utf-8'))
        past_reviewers = list(set([r['user']['login'] for r in reviews_data]))
        all_reviewers = list(set(requested_reviewers + past_reviewers))
        diff_content, _ = _make_api_request(url, "application/vnd.github.v3.diff")
        diff_text = diff_content.decode('utf-8')
        combined = (
            f"--- PR TITLE ---\n{meta_data.get('title')}\n\n"
            f"--- PR BODY ---\n{meta_data.get('body')}\n\n"
            f"--- REVIEWERS ---\n{', '.join(all_reviewers)}\n\n"
            f"--- DIFF ---\n{diff_text}"
        )
        return combined[:max_chars]
    except Exception as e:
        return f"Error: {str(e)}"

def get_documentation_catalog(pr_url: str) -> dict:
    try:
        parts = pr_url.strip().split("/")
        owner, repo = parts[-4], parts[-3]
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1"
        try:
            content, _ = _make_api_request(url)
        except:
            url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
            content, _ = _make_api_request(url)
        tree = json.loads(content.decode('utf-8')).get('tree', [])
        
        # Dynamically fetch the two most recent Bazel releases
        try:
            rel_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
            rel_content, _ = _make_api_request(rel_url)
            releases = json.loads(rel_content.decode('utf-8'))
            RECENT_ALLOWED = [r['tag_name'] for r in releases if not r['prerelease']][:2]
        except:
            RECENT_ALLOWED = ["9.0.0", "9.1.0"] # Fallback

        def is_allowed(path):
            if not (path.endswith('.md') or path.endswith('.mdx')): return False
            if '/versions/' in path:
                return any(f"/versions/{v}/" in path for v in RECENT_ALLOWED)
            return (path.startswith('site/en/') or path.startswith('docs/'))
        catalog = [item['path'] for item in tree if is_allowed(item['path'])]
        return {"total_files": len(catalog), "allowed_paths": catalog}
    except Exception as e:
        return {"error": str(e)}

def read_file_from_repo(pr_url: str, file_path: str, start_line: int = 1, end_line: int = -1) -> str:
    try:
        parts = pr_url.strip().split("/")
        owner, repo = parts[-4], parts[-3]
        clean_path = file_path.lstrip('/')
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{urllib.parse.quote(clean_path, safe='/')}"
        content_raw, _ = _make_api_request(url)
        data = json.loads(content_raw.decode('utf-8'))
        content = base64.b64decode(data.get('content', '').replace('\n', '')).decode('utf-8')
        lines = content.splitlines(keepends=True)
        if not lines: return ""
        try:
            start = max(1, int(start_line))
            if end_line == -1 or int(end_line) > len(lines): end = len(lines)
            else: end = int(end_line)
        except: start, end = 1, len(lines)
        return "".join(lines[start-1:end])
    except Exception as e:
        return f"Error reading file '{file_path}': {str(e)}"

def preview_patch(pr_url: str, path: str, old_text: str, new_text: str) -> str:
    try:
        original = read_file_from_repo(pr_url, path)
        if original.startswith("Error"): return f"Preview Error: {original}"
        if old_text not in original: return f"Preview Error: The exact 'old_text' was not found in the file."
        updated = original.replace(old_text, new_text)
        lines = updated.splitlines()
        first_line_of_new_text = new_text.splitlines()[0] if new_text else ""
        start_idx = 0
        for i, line in enumerate(lines):
            if first_line_of_new_text in line:
                start_idx = max(0, i - 5)
                break
        end_idx = min(len(lines), start_idx + 15)
        context = "\n".join(lines[start_idx:end_idx])
        return f"Patch successfully applied in memory!\n\n...\n{context}\n...\n"
    except Exception as e:
        return f"Preview Error: {str(e)}"

def create_pull_request(pr_url: str, pr_title: str, pr_body: str, updates_json: str, reviewers: str = "") -> str:
    """
    Creates a Stacked PR and NOTIFIES the author on their existing parent PR.
    """
    try:
        updates = json.loads(updates_json)
        parts = pr_url.strip().split("/")
        pr_number = parts[-1]
        upstream_owner, upstream_repo = parts[-4], parts[-3]
        fork_owner = os.environ.get("FORK_OWNER", "deepalak56")
        fork_repo = os.environ.get("FORK_REPO", "bazel_deepa")
        
        # 1. Get Target PR details
        pr_api_url = f"https://api.github.com/repos/{upstream_owner}/{upstream_repo}/pulls/{pr_number}"
        pr_content, _ = _make_api_request(pr_api_url)
        pr_data = json.loads(pr_content.decode('utf-8'))
        
        target_repo_owner = pr_data['head']['repo']['owner']['login']
        target_repo_name = pr_data['head']['repo']['name']
        target_branch = pr_data['head']['ref']
        
        # 2. Get Head SHA of contributor's branch
        ref_url = f"https://api.github.com/repos/{target_repo_owner}/{target_repo_name}/git/ref/heads/{target_branch}"
        content, _ = _make_api_request(ref_url)
        base_commit_sha = json.loads(content.decode('utf-8'))['object']['sha']
        
        commit_url = f"https://api.github.com/repos/{target_repo_owner}/{target_repo_name}/git/commits/{base_commit_sha}"
        commit_content, _ = _make_api_request(commit_url)
        base_tree_sha = json.loads(commit_content.decode('utf-8'))['tree']['sha']

        # 3. Create a branch on OUR fork
        branch_name = f"docs-bot/update-{pr_number}-{int(time.time())}"
        create_ref_url = f"https://api.github.com/repos/{fork_owner}/{fork_repo}/git/refs"
        _make_api_request(create_ref_url, method="POST", data={"ref": f"refs/heads/{branch_name}", "sha": base_commit_sha})

        # 4. Apply Patches
        tree_elements = []
        
        # --- SECURITY GUARDRAIL ---
        forbidden_patterns = ['/versions/']
        for item in updates:
            path = item.get('path', '').lstrip('/')
            for pattern in forbidden_patterns:
                if pattern in path:
                    return f"SECURITY ERROR: You are forbidden from modifying '{path}'. Do not attempt to edit versioned documentation."
        # --------------------------

        for item in updates:
            path = item.get('path', '').lstrip('/')
            old_text = item.get('old_text', '')
            new_text = item.get('new_text', '')
            
            file_url = f"https://api.github.com/repos/{target_repo_owner}/{target_repo_name}/contents/{urllib.parse.quote(path, safe='/')}?ref={target_branch}"
            file_raw, _ = _make_api_request(file_url)
            file_data = json.loads(file_raw.decode('utf-8'))
            original = base64.b64decode(file_data.get('content', '').replace('\n', '')).decode('utf-8')
            
            if old_text not in original:
                return f"Error applying patch to {path}: The exact 'old_text' was not found. Please ensure your snippet matches exactly, including indentation."
            
            updated = original.replace(old_text, new_text)
            
            # Create a blob for the updated content
            blob_url = f"https://api.github.com/repos/{fork_owner}/{fork_repo}/git/blobs"
            blob_resp, _ = _make_api_request(blob_url, method="POST", data={"content": updated, "encoding": "utf-8"})
            tree_elements.append({"path": path, "mode": "100644", "type": "blob", "sha": json.loads(blob_resp.decode('utf-8'))['sha']})

        # 5. Finalize Commit
        tree_url = f"https://api.github.com/repos/{fork_owner}/{fork_repo}/git/trees"
        tree_resp, _ = _make_api_request(tree_url, method="POST", data={"base_tree": base_tree_sha, "tree": tree_elements})
        commit_resp, _ = _make_api_request(f"https://api.github.com/repos/{fork_owner}/{fork_repo}/git/commits", method="POST", data={"message": f"{pr_title}\n\n{pr_body}", "tree": json.loads(tree_resp.decode('utf-8'))['sha'], "parents": [base_commit_sha]})
        new_commit_sha = json.loads(commit_resp.decode('utf-8'))['sha']
        _make_api_request(f"https://api.github.com/repos/{fork_owner}/{fork_repo}/git/refs/heads/{branch_name}", method="PATCH", data={"sha": new_commit_sha, "force": True})

        # 6. Create Stacked PR targeting the author's branch
        pr_url_api = f"https://api.github.com/repos/{target_repo_owner}/{target_repo_name}/pulls"
        pr_resp, _ = _make_api_request(pr_url_api, method="POST", data={
            "title": pr_title, 
            "body": pr_body, 
            "head": f"{fork_owner}:{branch_name}", 
            "base": target_branch 
        })
        stacked_pr_url = json.loads(pr_resp.decode('utf-8')).get('html_url')

        # 7. POST A POPUP COMMENT ON THE PARENT PR
        comment_url = f"https://api.github.com/repos/{upstream_owner}/{upstream_repo}/issues/{pr_number}/comments"
        comment_body = (
            f"### 🤖 Documentation Ready for Review\n\n"
            f"Hi @{target_repo_owner}, I have prepared the documentation updates for your changes.\n\n"
            f"Please review and merge my proposal here: **[Documentation Patch]({stacked_pr_url})**\n\n"
            f"Once you merge this small PR, your original PR will be updated automatically with the documentation."
        )
        _make_api_request(comment_url, method="POST", data={"body": comment_body})

        return f"✅ Success! Stacked PR created: {stacked_pr_url}. Notification posted on parent PR #{pr_number}."
    except Exception as e:
        return f"Error: {str(e)}"
