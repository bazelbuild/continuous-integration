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
    r"^(?P<filename>[^:]*):(?P<line>\d*):(?:(?P<column>\d*):)? (?P<message_id>[^:]*): (?P<message>.*) \((?P<message_url>.*)\)$",
    re.MULTILINE,
)


BUILDIFIER_VERSION_PATTERN = re.compile(r"^buildifier version: ([\.\w]+)$", re.MULTILINE)


BUILDIFIER_URL = "https://github.com/bazelbuild/buildtools/tree/master/buildifier"


# https://github.com/bazelbuild/buildtools/blob/master/buildifier/buildifier.go#L333
# Buildifier error code for "needs formatting". We should fail on all other error codes > 0
# since they indicate a problem in how Buildifier is used.
BUILDIFIER_FORMAT_ERROR_CODE = 4


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


def run_buildifier(flag, files=None, version=None, what=None):
    label = "+++ :bazel: Running "
    if version:
        label += "Buildifier " + version
    else:
        label += "unreleased Buildifier"
    if what:
        label += ": " + what

    eprint(label)

    args = ["buildifier", flag]
    if files:
        args += files

    return subprocess.run(args, capture_output=True, universal_newlines=True)


def create_heading(issue_type, issue_count):
    return "##### :bazel: buildifier: found {} {} issue{} in your WORKSPACE, BUILD and *.bzl files\n".format(
        issue_count, issue_type, "s" if issue_count > 1 else ""
    )


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

    files = sorted(files)

    eprint("+++ :female-detective: Detecting Buildifier version")
    version_result = run_buildifier("--version", what="Version info")
    match = BUILDIFIER_VERSION_PATTERN.search(version_result.stdout)
    version = match.group(1) if match and match.group(1) != "redacted" else None

    # Run formatter before linter since --lint=warn implies --mode=fix,
    # thus fixing any format issues.
    formatter_result = run_buildifier(
        "--mode=check", files=files, version=version, what="Format check"
    )
    if formatter_result.returncode and formatter_result.returncode != BUILDIFIER_FORMAT_ERROR_CODE:
        output = "##### :bazel: buildifier: error while checking format:\n"
        output += "<pre><code>" + html.escape(formatter_result.stderr) + "</code></pre>"
        if "BUILDKITE_JOB_ID" in os.environ:
            output += "\n\nSee [job {job}](#{job})\n".format(job=os.environ["BUILDKITE_JOB_ID"])

        upload_output(output)
        return formatter_result.returncode

    # Format: "<file name> # reformated"
    unformatted_files = [l.partition(" ")[0] for l in formatter_result.stdout.splitlines()]
    if unformatted_files:
        eprint(
            "+++ :construction: Found {} file(s) that must be formatted".format(
                len(unformatted_files)
            )
        )

    linter_result = run_buildifier("--lint=warn", files=files, version=version, what="Lint checks")
    if linter_result.returncode == 0 and not unformatted_files:
        # If buildifier was happy, there's nothing left to do for us.
        eprint("+++ :tada: Buildifier found nothing to complain about")
        return 0

    output = ""
    if unformatted_files:
        output = create_heading("format", len(unformatted_files))
        output += (
            'Please download <a href="{}">buildifier</a> and run the following '
            "command in your workspace:<br/><code>buildifier {}</code><br/>\n".format(
                BUILDIFIER_URL, " ".join(unformatted_files)
            )
        )

    # Parse output.
    eprint("+++ :gear: Parsing buildifier output")
    findings = list(regex.finditer(linter_result.stderr))
    output += create_heading("lint", len(findings))
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
    return linter_result.returncode


if __name__ == "__main__":
    sys.exit(main())
