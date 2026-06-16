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

"""Custom Bazel rule to create minimal Python zipapps.

This module defines the `lightweight_py_binary_zipapp` rule, which collects all
transitive sources and dependencies of a `py_binary` (including pip dependencies)
and bundles them into a single executable `.pyz` file using Python's built-in
`zipapp` module.
"""

ZipappSourcesInfo = provider(
    doc = "Provider to collect transitive sources for zipapp packaging.",
    fields = {
        "sources": "depset of transitive sources (files)",
    }
)

def _collect_sources_aspect_impl(target, ctx):
    """Aspect implementation that traverses the dependency graph.

    It collects all files from `srcs` and `data` attributes, and propagates
    transitively through `deps` and `data` attributes.
    """
    transitive_sources = []
    
    # Collect direct files from srcs and data
    for attr in ["srcs", "data"]:
        if hasattr(ctx.rule.attr, attr):
            transitive_sources.extend([t.files for t in getattr(ctx.rule.attr, attr)])

    # Propagate transitive sources from deps and data
    for attr in ["deps", "data"]:
        if hasattr(ctx.rule.attr, attr):
            transitive_sources.extend([
                dep[ZipappSourcesInfo].sources
                for dep in getattr(ctx.rule.attr, attr)
                if ZipappSourcesInfo in dep
            ])

    return [ZipappSourcesInfo(
        sources = depset(transitive = transitive_sources)
    )]

collect_sources_aspect = aspect(
    implementation = _collect_sources_aspect_impl,
    attr_aspects = ["deps", "data"],
    doc = "Aspect to collect all transitive sources and data files.",
)

def _get_dest_path(f):
    """Computes the destination path of a file inside the zipapp."""
    if f.owner.workspace_name == "":
        return f.short_path
    else:
        parts = f.short_path.split("/")
        if len(parts) > 2 and parts[0] == "..":
            path_in_repo = "/".join(parts[2:])
        else:
            path_in_repo = f.short_path
            
        if path_in_repo.startswith("site-packages/"):
            return path_in_repo[len("site-packages/"):]
        return path_in_repo

def _format_manifest_entry(f):
    """Formats a single file entry for the manifest.

    Filters out compiled extension files (.so, .pyd, .dll, .dylib) because
    they cannot be loaded from a zip archive by standard Python zipimport.
    
    As specified in PEP 273 (https://peps.python.org/pep-0273/) and the
    official Python zipimport documentation (https://docs.python.org/3/library/zipimport.html),
    zip import of dynamic modules is disallowed due to OS-level limitations
    (loaders like dlopen/LoadLibrary require a real physical filesystem path).
    
    Returning None tells Args.add_all to ignore this file.
    """
    if f.extension in ["so", "pyd", "dll", "dylib"]:
        return None
    dest = _get_dest_path(f)
    return "%s:%s" % (f.path, dest)

def _py_zipapp_impl(ctx):
    binary = ctx.attr.binary
    if ZipappSourcesInfo not in binary:
        fail("Binary target does not have ZipappSourcesInfo. Ensure the aspect is applied.")
        
    sources = binary[ZipappSourcesInfo].sources
    
    # Create a manifest of files to copy.
    args = ctx.actions.args()
    args.add_all(sources, map_each = _format_manifest_entry)
    
    manifest_file = ctx.actions.declare_file(ctx.attr.name + "_manifest.txt")
    ctx.actions.write(manifest_file, args)
    
    output = ctx.actions.declare_file(ctx.attr.name + ".pyz")
    
    # Helper python script to perform the copy and zipapp creation.
    builder_script_content = """
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

def main():
    parser = argparse.ArgumentParser(description="Builder script for lightweight_py_binary_zipapp.")
    parser.add_argument("--manifest", required=True, help="Path to the manifest file.")
    parser.add_argument("--output", required=True, help="Path to the output .pyz file.")
    parser.add_argument("--main", help="The entry point for the zipapp, in the format pkg.module:func.")
    parser.add_argument("--compress", action="store_true", help="Whether to compress the zipapp.")
    
    args = parser.parse_args()

    # Read text manifest (src:dest)
    manifest = []
    with open(args.manifest, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(':', 1)
            if len(parts) == 2:
                manifest.append({'src': parts[0], 'dest': parts[1]})

    # Use a temporary directory to stage the zipapp contents
    with tempfile.TemporaryDirectory() as tmpdir:
        for entry in manifest:
            src = entry['src']
            dest = os.path.join(tmpdir, entry['dest'])
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)

        # Run python -m zipapp
        python_exe = sys.executable if sys.executable else 'python3'
        cmd = [python_exe, '-m', 'zipapp', tmpdir, '-o', args.output]
        if args.main:
            cmd.extend(['-m', args.main])
        if args.compress:
            cmd.append('-c')
            
        print("Running:", " ".join(cmd))
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print("zipapp failed:")
            print("stdout:", res.stdout)
            print("stderr:", res.stderr)
            sys.exit(res.returncode)

if __name__ == '__main__':
    main()
"""
    
    builder_script = ctx.actions.declare_file(ctx.attr.name + "_builder.py")
    ctx.actions.write(builder_script, builder_script_content)
    
    # Build the inputs depset
    inputs = depset(
        direct = [manifest_file, builder_script],
        transitive = [sources],
    )
    
    # Prepare arguments for the builder script using argparse style
    arguments = []
    arguments.append("--manifest=%s" % manifest_file.path)
    arguments.append("--output=%s" % output.path)
    if ctx.attr.main:
        arguments.append("--main=%s" % ctx.attr.main)
    if ctx.attr.compress:
        arguments.append("--compress")
        
    # Run the builder script using system python
    ctx.actions.run_shell(
        outputs = [output],
        inputs = inputs,
        arguments = arguments,
        command = "python3 " + builder_script.path + " \"$@\"",
    )
    
    return [DefaultInfo(files = depset([output]))]

lightweight_py_binary_zipapp = rule(
    implementation = _py_zipapp_impl,
    attrs = {
        "binary": attr.label(
            mandatory = True,
            aspects = [collect_sources_aspect],
            doc = "The py_binary target to package.",
        ),
        "main": attr.string(
            mandatory = False,
            doc = "The entry point for the zipapp (passed as -m to zipapp, e.g. 'pkg.mod:func').",
        ),
        "compress": attr.bool(
            default = True,
            doc = "Whether to compress the zipapp (requires Python 3.7+).",
        ),
    },
    doc = "Rule to package a py_binary and its transitive dependencies into a minimal .pyz zipapp.",
)
