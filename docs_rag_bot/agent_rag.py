import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
os.environ["GRPC_VERBOSITY"] = "ERROR"

from google import genai
from google.genai import types
from rag_utils import search_docs

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
from tools.git_tools import fetch_code_diff, create_pull_request, get_documentation_catalog, read_file_from_repo, preview_patch
from tools.doc_tools import is_third_party_change, is_external_change, format_for_mintlify

# GENAI Client initialized once
client = genai.Client()

def get_search_docs(query: str) -> str:
    """RAG TOOL: Searches existing documentation context."""
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] 🔍 RAG Search: '{query}'")
    return search_docs(query)

def run_rag_agent(target_url):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🤖 Agent Starting: {target_url}")
    
    tool_map = {
        "get_search_docs": get_search_docs,
        "fetch_code_diff": fetch_code_diff,
        "read_file_from_repo": read_file_from_repo,
        "is_third_party_change": is_third_party_change,
        "is_external_change": is_external_change,
        "format_for_mintlify": format_for_mintlify,
        "preview_patch": preview_patch,
        "create_pull_request": create_pull_request
    }

    # STEP 1: Catalog
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] 📚 Fetching Catalog...")
    catalog_result = get_documentation_catalog(target_url)
    catalog_data = json.loads(catalog_result) if isinstance(catalog_result, str) else catalog_result
    allowed_paths = catalog_data.get('allowed_paths', [])
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] ✅ Found {len(allowed_paths)} files.")

    # STEP 2: Chat
    system_instruction = f"""
    You are a Senior Technical Writer for Bazel.
    Goal: Sync documentation with code changes.
    Knowledge Map: {json.dumps(allowed_paths)}

    Rules:
    1. Only document changes affecting public APIs, user-facing behavior, or release management.
    2. Mirroring Rule: Update BOTH .md and .mdx versions of the same file.
    3. Brevity: Keep updates to 1-2 lines.

    Pre-flight Check:
    Identify user-facing impact. If none, you MUST first explain your reasoning (e.g. "This PR only modifies internal C++ tests, so no user-facing docs are impacted."), and then output the exact string "NO_DOCS_NEEDED" at the very end of your response to stop the process.
    """

    chat = client.chats.create(
        model="gemini-pro-latest",
        config=types.GenerateContentConfig(
            tools=list(tool_map.values()),
            system_instruction=system_instruction,
            temperature=0.0
        )
    )

    # STEP 3: Run
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] 🚀 Initiating Reasoning...")
    try:
        response = chat.send_message(f"Process PR: {target_url}. 1. Fetch Diff. 2. Pre-flight. 3. Propose if needed.")
    except Exception as e:
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] ❌ Initial Call Failed: {e}")
        return

    for i in range(10): # Reduced loop for robustness
        if not response or not response.candidates: break
        
        # Kill switch
        try:
            if response.text and "NO_DOCS_NEEDED" in response.text:
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] 🛑 No docs needed.")
                break
        except: pass

        part = response.candidates[0].content.parts[0]
        
        if part.function_call:
            fn_name = part.function_call.name
            fn_args = part.function_call.args
            if 'pr_url' in fn_args: fn_args['pr_url'] = target_url
            
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] 🛠️  Tool: {fn_name}")
            try:
                result = tool_map[fn_name](**fn_args)
                response = chat.send_message(types.Part.from_function_response(name=fn_name, response={'result': result}))
            except Exception as e:
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] ❌ Tool Error ({fn_name}): {e}")
                response = chat.send_message(f"Tool {fn_name} failed: {e}")
        else:
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] 🏁 Agent Finished.")
            break

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}]  RESPONSE \n{getattr(response, 'text', 'No Text')}")

if __name__ == "__main__":
    if len(sys.argv) > 1: run_rag_agent(sys.argv[1])
