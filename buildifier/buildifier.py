#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import fnmatch
import html
import locale
import os.path
import re
import subprocess
import sys

regex = re.compile(
    r"(?P<filename>[^:]*):(?P<line>\d*):(?:(?P<column>\d*):)? (?P<message_id>[^:]*): (?P<message>.*) \((?P<message_url>.*)\)"
)


def eprint(*args, **kwargs):
    """
    Print to stderr and flush (just in case).
    """
    print(*args, flush=True, file=sys.stderr, **kwargs)


def upload_output(output):
    # Generate output usable by Buildkite's annotations.
    eprint("--- :hammer_and_wrench: Printing raw output for debugging")
    eprint(output)

    eprint("+++ :buildkite: Uploading output via 'buildkite annotate'")
    result = subprocess.run(
        ["buildkite-agent", "annotate", "--style", "warning", "--context", "buildifier"],
        input=output.encode(locale.getpreferredencoding(False)),
    )
    if result.returncode != 0:
        eprint(
            ":rotating_light: 'buildkite-agent annotate' failed with exit code {}".format(
                result.returncode
            )
        )


def get_file_url(filename, line):
    commit = os.environ.get("BUILDKITE_COMMIT")
    repo = os.environ.get("BUILDKITE_PULL_REQUEST_REPO", os.environ.get("BUILDKITE_REPO", None))
    if not commit or not repo:
        return None

    # Example 1: https://github.com/bazelbuild/bazel.git
    # Example 2: git://github.com/philwo/bazel.git
    # Example 3: git@github.com:bazelbuild/bazel.git
    match = re.match(r"(?:(?:git|https?)://|git@)(github.com[:/].*)\.git", repo)
    if match:
        return "https://{}/blob/{}/{}#L{}".format(
            match[1].replace(":", "/"), commit, filename, line
        )

    return None


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    # Gather all files to process.
    eprint("+++ :female-detective: Looking for WORKSPACE, BUILD, BUILD.bazel and *.bzl files")
    files = []
    build_bazel_found = False
    for root, _, filenames in os.walk("."):
        for filename in filenames:
            if fnmatch.fnmatch(filename, "BUILD.bazel"):
                build_bazel_found = True
            for pattern in ("WORKSPACE", "BUILD", "BUILD.bazel", "*.bzl"):
                if fnmatch.fnmatch(filename, pattern):
                    files.append(os.path.relpath(os.path.join(root, filename)))
    if build_bazel_found:
        eprint(
            "Found BUILD.bazel files in the workspace, thus ignoring BUILD files without suffix."
        )
        files = [fname for fname in files if not fnmatch.fnmatch(os.path.basename(fname), "BUILD")]
    if not files:
        eprint("No files found, exiting.")
        return 0

    # Run buildifier.
    eprint("+++ :bazel: Running buildifier")
    result = subprocess.run(
        ["buildifier", "--lint=warn"] + sorted(files), capture_output=True, universal_newlines=True
    )

    # If buildifier was happy, there's nothing left to do for us.
    if result.returncode == 0:
        eprint("+++ :tada: Buildifier found nothing to complain about")
        return result.returncode

    # Parse output.
    eprint("+++ :gear: Parsing buildifier output")
    findings = []
    for line in result.stderr.splitlines():
        # Skip empty lines.
        line = line.strip()
        if not line:
            continue

        # Try to parse as structured data.
        match = regex.match(line)
        if match:
            findings.append(match)
        else:
            output = "##### :bazel: buildifier: error while parsing output\n"
            output += "<pre><code>" + html.escape(result.stderr) + "</code></pre>"
            if "BUILDKITE_JOB_ID" in os.environ:
                output += "\n\nSee [job {job}](#{job})\n".format(job=os.environ["BUILDKITE_JOB_ID"])
            upload_output(output)
            return result.returncode

    output = "##### :bazel: buildifier: found {} problems in your WORKSPACE, BUILD and *.bzl files\n".format(
        len(findings)
    )
    output += "<pre><code>"
    for finding in findings:
        file_url = get_file_url(finding["filename"], finding["line"])
        if file_url:
            output += '<a href="{}">{}:{}</a>:'.format(
                file_url, finding["filename"], finding["line"]
            )
        else:
            output += "{}:{}:".format(finding["filename"], finding["line"])
        if finding["column"]:
            output += "{}:".format(finding["column"])
        output += ' <a href="{}">{}</a>: {}\n'.format(
            finding["message_url"], finding["message_id"], finding["message"]
        )
    output = output.strip() + "</pre></code>"
    upload_output(output)

    # Preserve buildifier's exit code.
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
