import os
import hmac
import hashlib
import json
import requests
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from dotenv import load_dotenv
from agent_rag import run_rag_agent, client
from rag_utils import upsert_merged_doc, upsert_style_lesson

# Load local environment variables (.env)
load_dotenv()

app = FastAPI()

#  CONFIGURATION 
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET")
TARGET_LABEL = "bot:docs-needed"

#  SECURITY WHITELIST 
ALLOWED_REPOS = ["bazelbuild/bazel", "deepalak56/bazel_deepa"]

#  DEDUPLICATION CACHE 
# Stores PR URLs currently being processed to prevent double-comments on webhook retries
processing_cache = set()

def verify_signature(payload_body: bytes, signature_header: str):
    """Verifies that the payload was sent by GitHub using the shared secret."""
    if not signature_header or not WEBHOOK_SECRET:
        return False
    hash_object = hmac.new(WEBHOOK_SECRET.encode(), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)

@app.get("/")
def home():
    return {"message": "Docs RAG Bot is running."}

def generate_style_lesson(original_patch, final_content, filename):
    """Uses Gemini to synthesize what the human changed from the bot's suggestion."""
    prompt = f"""
    You are a Technical Writing Mentor. 
    
    ORIGINAL BOT SUGGESTION FOR {filename}:
    {original_patch}
    
    FINAL HUMAN-APPROVED VERSION:
    {final_content}
    
    Compare the two. If the human changed the bot's suggestion (moved lines, deleted flags, changed tone), 
    write a 2-line "Style Lesson" for the bot to follow in the future.
    Example: "When adding archive flags, place them in the Starlark Reference table, not the conceptual examples."
    If there are no changes, return "NO_CHANGE".
    """
    try:
        response = client.models.generate_content(model="gemini-3.1-flash-lite", contents=prompt)
        return response.text.strip()
    except:
        return "NO_CHANGE"

def run_and_clear_cache(pr_url):
    """Wraps the agent run to ensure the PR is removed from cache when finished."""
    try:
        run_rag_agent(pr_url)
    finally:
        if pr_url in processing_cache:
            processing_cache.remove(pr_url)

@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    signature = request.headers.get("X-Hub-Signature-256")
    body = await request.body()
    
    # 1. Verify Security
    if WEBHOOK_SECRET and not verify_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(body)
    event_type = request.headers.get("X-GitHub-Event")
    
    # 0. REPOSITORY WHITELIST CHECK
    repo_name = payload.get("repository", {}).get("full_name")
    if repo_name not in ALLOWED_REPOS:
        print(f"🚫 Ignoring webhook from unauthorized repository: {repo_name}")
        return {"status": "unauthorized_repo"}

    # 1. TRIGGER: Label added ('bot:docs-needed')
    if event_type == "pull_request":
        action = payload.get("action")
        if action == "labeled":
            label_name = payload.get("label", {}).get("name")
            if label_name == TARGET_LABEL:
                pr_url = payload["pull_request"]["html_url"]
                
                # --- DEDUPLICATION CHECK ---
                if pr_url in processing_cache:
                    print(f"⚠️ Ignoring duplicate webhook for {pr_url} (already processing).")
                    return {"status": "ignored_duplicate"}
                
                print(f"🏷️ Detected label '{label_name}'. Summoning RAG Bot...")
                processing_cache.add(pr_url)
                background_tasks.add_task(run_and_clear_cache, pr_url)
        
        # 3. TRIGGER: PR Merged (Learning from final human edits)
        elif action == "closed" and payload.get("pull_request", {}).get("merged"):
            pr_number = payload["pull_request"]["number"]
            repo = payload["repository"]["full_name"]
            print(f"🎓 PR #{pr_number} merged in {repo}. Analyzing for style lessons...")
            
            # Get list of changed files
            files_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            r = requests.get(files_url, headers=headers)
            
            if r.status_code == 200:
                for file in r.json():
                    filename = file["filename"]
                    if filename.endswith((".md", ".mdx")):
                        raw_url = file["raw_url"]
                        content_resp = requests.get(raw_url)
                        if content_resp.status_code == 200:
                            final_text = content_resp.text
                            background_tasks.add_task(upsert_merged_doc, filename, final_text, payload["pull_request"]["html_url"])
                            lesson = generate_style_lesson("Placeholder for bot's previous patch", final_text, filename)
                            if lesson != "NO_CHANGE":
                                background_tasks.add_task(upsert_style_lesson, filename, lesson)

    return {"status": "event_received"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
