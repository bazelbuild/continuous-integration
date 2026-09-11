import re
import os

def is_third_party_change(diff: str) -> bool:
    """
    Checks if the diff contains changes to third-party or vendor directories.
    """
    patterns = [r"third_party/", r"vendor/", r"WORKSPACE", r"go\.mod", r"requirements\.txt"]
    return any(re.search(p, diff) for p in patterns)

def is_external_change(diff: str) -> bool:
    """
    Placeholder function to determine if a change is external (user-facing).
    For now, it always returns True to allow the agent to proceed.
    This function should be implemented with actual logic to analyze the diff
    and determine if it impacts user-facing features, APIs, or command-line flags.
    """
    # TODO: Implement actual logic to determine if the change is external.
    # For now, we return True to allow the agent to proceed.
    return True

def format_for_mintlify(text: str) -> str:
    """
    Prepares text for Mintlify (.mdx).
    Escapes bare braces {} which would otherwise break the React-based MDX parser.
    """
    # Escape { and }
    text = text.replace("{", "\\{").replace("}", "\\}")
    
    # Heuristic: Convert standard Markdown notes to Mintlify components
    text = re.sub(r"^Note:\s*(.*)", r"<Info>\1</Info>", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^Warning:\s*(.*)", r"<Warning>\1</Warning>", text, flags=re.MULTILINE | re.IGNORECASE)
    
    return text

def write_docs_to_disk(devsite_content: str, mintlify_content: str, base_filename: str) -> str:
    """
    Writes the generated content to the docs/ directory.
    """
    os.makedirs("docs/devsite", exist_ok=True)
    os.makedirs("docs/mintlify", exist_ok=True)
    
    devsite_path = f"docs/devsite/{base_filename}.md"
    mintlify_path = f"docs/mintlify/{base_filename}.mdx"
    
    with open(devsite_path, "w") as f:
        f.write(devsite_content)
    with open(mintlify_path, "w") as f:
        f.write(mintlify_content)
        
    return f"Files created: {devsite_path} and {mintlify_path}"
