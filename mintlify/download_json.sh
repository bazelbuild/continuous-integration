#!/bin/bash

# Function to download and recursively process JSON files
# Usage: download_json <URL> [rel_path]
download_json() {
    local url="$1"
    local rel_path="${2:-$(basename "$url")}"

    # Create directory structure if needed
    local dir_name
    dir_name=$(dirname "$rel_path")
    if [[ "$dir_name" != "." ]]; then
        mkdir -p "$dir_name"
    fi

    echo "Downloading: $url -> $rel_path"

    # Download the file
    if ! curl -sSL "$url" -o "$rel_path"; then
        echo "Error: Failed to download $url"
        return 1
    fi

    # Check if the file is valid JSON and has $ref entries
    # We use jq to find all values of keys named "$ref" recursively
    local refs
    refs=$(jq -r '.. | .["$ref"]? | select(. != null)' "$rel_path" 2>/dev/null)

    if [[ -z "$refs" ]]; then
        return 0
    fi

    # Get the base URL (strip the filename from the current URL)
    local base_url
    base_url=$(dirname "$url")

    # Process each reference
    while IFS= read -r ref; do
        # Ignore external/absolute URLs for this specific logic (if they start with http)
        if [[ "$ref" =~ ^http ]]; then
            echo "Skipping absolute URL: $ref"
            continue
        fi

        # Clean up the relative path (remove leading ./)
        local clean_ref="${ref#./}"

        # Construct the new URL and the new local path
        local new_url="$base_url/$clean_ref"

        # The new local path should be relative to the directory of the current file
        # or simply relative to the root if the refs are structured that way.
        # Based on the example: navigation.json -> navigation/9.0.en.json
        local new_rel_path
        if [[ "$dir_name" == "." ]]; then
            new_rel_path="$clean_ref"
        else
            new_rel_path="$dir_name/$clean_ref"
        fi

        # Recursive call
        download_json "$new_url" "$new_rel_path"
    done <<< "$refs"
}