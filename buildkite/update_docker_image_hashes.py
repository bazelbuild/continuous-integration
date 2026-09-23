#!/usr/bin/env python3
#
# Copyright 2026 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Updates hard-coded Docker image hashes in bazelci.py, Terraform configs, and RBE presets.
"""

import concurrent.futures
import json
from pathlib import Path
import re
import subprocess
import sys

IMAGE_KEYS = [
    "rockylinux8",
    "rockylinux8-java11",
    "rockylinux8-java11-devtoolset10",
    "debian10-java11",
    "debian11-java17",
    "debian12",
    "debian13",
    "ubuntu1604-java8",
    "ubuntu1804-java11",
    "ubuntu2004-java11",
    "ubuntu2004",
    "ubuntu2204",
    "ubuntu2404",
    "ubuntu2004-kythe",
    "ubuntu2204-kythe",
    "ubuntu2404-kythe",
    "ubuntu2204-java17",
    "fedora39-java17",
    "fedora40-java21",
    "fedora43-java25",
]


def get_image_url(image_name):
    return f"gcr.io/bazel-public/{image_name}"


def fetch_image_digests(image_name, image_url):
    cmd = ["docker", "manifest", "inspect", image_url]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Failed to inspect manifest for {image_url}: {p.stderr.strip()}")

    manifest_data = json.loads(p.stdout)
    arch_digests = {}

    # Note: The if/else branch here is needed since the `manifests` attr
    # only exists for multiplatform images. Not all images used in BazelCI
    # are multiplatform.
    if "manifests" in manifest_data:
        for m in manifest_data["manifests"]:
            arch = m.get("platform", {}).get("architecture")
            if arch in ("amd64", "arm64"):
                arch_digests[arch] = m.get("digest")
            elif arch == "unknown":
                # Docker buildx / buildkit packages SBOM and provenance attestations with architecture 'unknown'
                continue
            else:
                raise RuntimeError(f"Unsupported architecture '{arch}' found for {image_url}")
    else:
        cmd_tags = [
            "gcloud",
            "container",
            "images",
            "list-tags",
            image_url,
            "--sort-by=~timestamp",
            "--limit=1",
            "--format=json",
        ]
        p_tags = subprocess.run(cmd_tags, capture_output=True, text=True)
        if p_tags.returncode == 0 and p_tags.stdout:
            tags_data = json.loads(p_tags.stdout)
            if tags_data and "digest" in tags_data[0]:
                arch_digests["amd64"] = tags_data[0]["digest"]

    if not arch_digests:
        raise RuntimeError(f"No amd64 or arm64 digests found for {image_url}")

    return image_name, arch_digests


def fetch_all_image_digests(image_keys=None):
    if image_keys is None:
        image_keys = IMAGE_KEYS

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_key = {
            executor.submit(fetch_image_digests, key, get_image_url(key)): key for key in image_keys
        }
        for future in concurrent.futures.as_completed(future_to_key):
            key = future_to_key[future]
            try:
                img_name, digests = future.result()
                results[img_name] = digests
            except Exception as exc:
                print(f"Error fetching digests for {key}: {exc}", file=sys.stderr)
                raise

    return {k: results[k] for k in image_keys}


def format_image_hashes_dict(image_hashes):
    lines = ["IMAGE_HASHES = {"]
    for image_name, arch_dict in image_hashes.items():
        lines.append(f'    "{image_name}": {{')
        for arch in ("amd64", "arm64"):
            if arch in arch_dict:
                lines.append(f'        "{arch}": "{arch_dict[arch]}",')
        lines.append("    },")
    lines.append("}")
    return "\n".join(lines)


SENTINEL_START = "# DO_NOT_MODIFY_IMAGE_HASHES_SENTINEL_START"
SENTINEL_END = "# DO_NOT_MODIFY_IMAGE_HASHES_SENTINEL_END"


def update_bazelci_file(bazelci_path, new_image_hashes_str):
    output_lines = []
    in_sentinel_block = False
    found_start = False
    found_end = False

    with open(bazelci_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith(SENTINEL_START):
                output_lines.append(line)
                output_lines.append(f"{new_image_hashes_str}\n")
                in_sentinel_block = True
                found_start = True
            elif line.startswith(SENTINEL_END):
                in_sentinel_block = False
                output_lines.append(line)
                found_end = True
            elif not in_sentinel_block:
                output_lines.append(line)

    if not found_start:
        raise ValueError(f"Could not find start sentinel '{SENTINEL_START}' in {bazelci_path}")
    if not found_end:
        raise ValueError(f"Could not find end sentinel '{SENTINEL_END}' in {bazelci_path}")

    with open(bazelci_path, "w", encoding="utf-8") as f:
        f.writelines(output_lines)


def update_pinned_hashes(files, image_hashes):
    pattern = re.compile(r"gcr\.io/bazel-public/([a-zA-Z0-9_\-]+)@sha256:[a-f0-9]+")

    updated_files = []
    for fpath in sorted(files):
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        def replacer(match):
            img_name = match.group(1)
            if img_name in image_hashes and "amd64" in image_hashes[img_name]:
                digest = image_hashes[img_name]["amd64"]
                return f"gcr.io/bazel-public/{img_name}@{digest}"
            return match.group(0)

        updated_content = pattern.sub(replacer, content)
        if updated_content != content:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(updated_content)
            updated_files.append(fpath)

    return updated_files


def update_terraform_configs(terraform_dir, image_hashes):
    tf_files = list(terraform_dir.glob("**/*.tf")) + list(terraform_dir.glob("**/*.tpl"))
    return update_pinned_hashes(tf_files, image_hashes)


def update_rbe_presets(rbe_file, image_hashes):
    return update_pinned_hashes([rbe_file], image_hashes)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    bazelci_path = repo_root / "buildkite" / "bazelci.py"
    terraform_dir = repo_root / "buildkite" / "terraform"
    rbe_presets_file = repo_root / "rules" / "rbe_presets.json"

    if not bazelci_path.exists():
        print(f"Error: {bazelci_path} not found.", file=sys.stderr)
        sys.exit(1)

    if not terraform_dir.exists():
        print(f"Error: {terraform_dir} not found.", file=sys.stderr)
        sys.exit(1)

    if not rbe_presets_file.exists():
        print(f"Error: {rbe_presets_file} not found.", file=sys.stderr)
        sys.exit(1)

    print("Fetching latest image manifests...")

    digests = fetch_all_image_digests(IMAGE_KEYS)

    new_dict_str = format_image_hashes_dict(digests)
    update_bazelci_file(bazelci_path, new_dict_str)
    print(f"Successfully updated IMAGE_HASHES in {bazelci_path}!")

    updated_tf = update_terraform_configs(terraform_dir, digests)
    print(f"Successfully updated {len(updated_tf)} terraform configuration files:")
    for tf_path in updated_tf:
        print(f"  - {tf_path}")

    updated_rbe = update_rbe_presets(rbe_presets_file, digests)
    if updated_rbe:
        print(f"Successfully updated RBE presets in {rbe_presets_file}!")


if __name__ == "__main__":
    main()
