#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import fnmatch
import locale
import os.path
import re
import subprocess
import sys

regex = re.compile(
    r"^(?P<filename>[^:]*):(?P<line>\d*):(?:(?P<column>\d*):)? (?P<message_id>[^:]*): (?P<message>.*) \((?P<message_url>.*)\)$",
    re.MULTILINE,
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


def run_buildifier(flag, files, what):
    eprint("+++ :bazel: Running buildifier ({})".format(what))
    result = subprocess.run(
        ["buildifier", flag] + files, capture_output=True, universal_newlines=True
    )
    return result.returncode, result.stderr


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

    # No need to check the exit code since buildifier -d returns 0 even when it finds unformatted files.
    # It prints the names of all offending files, but appends a colon to every single one.
    _, formatter_output = run_buildifier("-d", files, "format check")
    unformatted_files = [l.rstrip(":") for l in formatter_output.splitlines()]

    linter_return_code, linter_output = run_buildifier("--lint=warn", files, "lint checks")

    if unformatted_files:
        eprint(
            "+++ :construction: Found {} file(s) that must be formatted".format(
                len(unformatted_files)
            )
        )
    elif linter_return_code == 0:
        # If buildifier was happy, there's nothing left to do for us.
        eprint("+++ :tada: Buildifier found nothing to complain about")
        return linter_return_code

    # Parse output.
    eprint("+++ :gear: Parsing buildifier output")
    findings = list(regex.finditer(linter_output))
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

    if unformatted_files:
        output += (
            "<p/>There are also {} unformatted file(s) in the repository. "
            "Please run the following command in your workspace:"
            "<br/><code>buildifier {}</code>".format(
                len(unformatted_files), " ".join(unformatted_files)
            )
        )

    upload_output(output)

    # Preserve buildifier's exit code.
    return linter_return_code


if __name__ == "__main__":
    sys.exit(main())
