#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import fnmatch
import html
import json
import locale
import os
import os.path
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import closing
from distutils.version import LooseVersion
from urllib.request import urlopen

BUILDIFIER_VERSION_PATTERN = re.compile(
    r"^buildifier version: ([\.\w]+)$", re.MULTILINE
)

# https://github.com/bazelbuild/buildtools/blob/master/buildifier/buildifier.go#L333
# Buildifier error code for "needs formatting". We should fail on all other error codes > 0
# since they indicate a problem in how Buildifier is used.
BUILDIFIER_FORMAT_ERROR_CODE = 4

VERSION_ENV_VAR = "BUILDIFIER_VERSION"

WARNINGS_ENV_VAR = "BUILDIFIER_WARNINGS"

BUILDIFIER_RELEASES_URL = "https://api.github.com/repos/bazelbuild/buildtools/releases"

BUILDIFIER_DEFAULT_DISPLAY_URL = (
    "https://github.com/bazelbuild/buildtools/tree/master/buildifier"
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
        [
            "buildkite-agent",
            "annotate",
            "--style",
            "warning",
            "--context",
            "buildifier",
        ],
        input=output.encode(locale.getpreferredencoding(False)),
    )
    if result.returncode != 0:
        eprint(
            ":rotating_light: 'buildkite-agent annotate' failed with exit code {}".format(
                result.returncode
            )
        )


def print_error(failing_task, message):
    output = "##### :bazel: buildifier: error while {}:\n".format(failing_task)
    output += "<pre><code>{}</code></pre>".format(html.escape(message))
    if "BUILDKITE_JOB_ID" in os.environ:
        output += "\n\nSee [job {job}](#{job})\n".format(
            job=os.environ["BUILDKITE_JOB_ID"]
        )

    upload_output(output)


def get_file_url(filename, line):
    commit = os.environ.get("BUILDKITE_COMMIT")
    repo = os.environ.get(
        "BUILDKITE_PULL_REQUEST_REPO", os.environ.get("BUILDKITE_REPO", None)
    )
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


def run_buildifier(binary, flags, version=None, what=None):
    label = "+++ :bazel: Running "
    if version:
        label += "Buildifier " + version
    else:
        label += "unreleased Buildifier"
    if what:
        label += ": " + what

    eprint(label)

    return subprocess.run(
        [binary] + flags, capture_output=True, universal_newlines=True
    )


def create_heading(issue_type, issue_count):
    return "##### :bazel: buildifier: found {} {} issue{} in your WORKSPACE, BUILD and *.bzl files\n".format(
        issue_count, issue_type, "s" if issue_count > 1 else ""
    )


def get_buildifier_info(version):
    all_releases = get_releases()
    if not all_releases:
        raise Exception("Could not get Buildifier releases from GitHub")

    resolved_version = version
    if version == "latest":
        resolved_version = str(max(LooseVersion(r) for r in all_releases))

    if resolved_version not in all_releases:
        raise Exception("Unknown Buildifier version '{}'".format(version))

    display_url, download_url = all_releases.get(resolved_version)
    return resolved_version, display_url, download_url


def get_releases():
    with closing(urlopen(BUILDIFIER_RELEASES_URL)) as res:
        body = res.read()
        content = body.decode(res.info().get_content_charset("iso-8859-1"))

    return {
        r["tag_name"]: get_release_urls(r)
        for r in json.loads(content)
        if not r["prerelease"]
    }


def get_release_urls(release):
    for asset in release["assets"]:
        if asset["name"] == "buildifier-linux-amd64":
            return release["html_url"], asset["browser_download_url"]
    raise Exception(
        "There is no Buildifier binary for release {}".format(release["tag_name"])
    )


def download_buildifier(url):
    path = os.path.join(tempfile.mkdtemp(), "buildifier")
    with closing(urlopen(url)) as response:
        with open(path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
    os.chmod(path, 0o755)
    return path


def format_lint_warning(filename, warning):
    line_number = warning["start"]["line"]
    link_start, link_end, column_text = "", "", ""

    file_url = get_file_url(filename, line_number)
    if file_url:
        link_start = '<a href="{}">'.format(file_url)
        link_end = "</a>"

    column = warning["start"].get("column")
    if column:
        column_text = ":{}".format(column)

    return '{link_start}{filename}:{line}{column}{link_end}: <a href="{help_url}">{category}</a>: {message}'.format(
        link_start=link_start,
        filename=filename,
        line=line_number,
        column=column_text,
        link_end=link_end,
        help_url=warning["url"],
        category=warning["category"],
        message=warning["message"],
    )


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    buildifier_binary = "buildifier"
    display_url = BUILDIFIER_DEFAULT_DISPLAY_URL
    version = os.environ.get(VERSION_ENV_VAR, "latest")
    eprint("+++ :github: Downloading Buildifier version '{}'".format(version))
    try:
        version, display_url, download_url = get_buildifier_info(version)
        eprint("Downloading Buildifier {} from {}".format(version, download_url))
        buildifier_binary = download_buildifier(download_url)
    except Exception as ex:
        print_error("downloading Buildifier", str(ex))
        return 1

    flags = ["--mode=check", "--lint=warn"]
    warnings = os.getenv(WARNINGS_ENV_VAR)
    if warnings:
        eprint("Running Buildifier with the following warnings: {}".format(warnings))
        flags.append("--warnings={}".format(warnings))

    result = run_buildifier(
        buildifier_binary,
        flags + ["--format=json", "-r", "."],
        version=version,
        what="Format & lint checks",
    )

    if result.returncode and result.returncode != BUILDIFIER_FORMAT_ERROR_CODE:
        print_error("Buildifier failed", result.stderr)
        return result.returncode

    data = json.loads(result.stdout)
    if data["success"]:
        # If buildifier was happy, there's nothing left to do for us.
        eprint("+++ :tada: Buildifier found nothing to complain about")
        return 0

    unformatted_files = []
    lint_findings = []
    for file in data["files"]:
        filename = file["filename"]

        if not file["formatted"]:
            unformatted_files.append(filename)

        for warning in file["warnings"]:
            lint_findings.append(format_lint_warning(filename, warning))

    output = ""
    if unformatted_files:
        eprint(
            "+++ :construction: Found {} file(s) that must be formatted".format(
                len(unformatted_files)
            )
        )
        output = create_heading("format", len(unformatted_files))
        display_version = " {}".format(version) if version else ""
        output += (
            'If this repo uses a pre-commit hook, then you should install it. '
            'Otherwise, please download <a href="{}">buildifier{}</a> and run the following '
            "command in your workspace:<br/><pre><code>buildifier {}</code></pre>"
            "\n".format(display_url, display_version, " ".join(unformatted_files))
        )

    if lint_findings:
        eprint("+++ :gear: Rendering lint warnings")
        output += create_heading("lint", len(lint_findings))
        output += "<pre><code>"
        output += "\n".join(lint_findings)
        output = output.strip() + "</pre></code>"

    upload_output(output)

    # Preserve buildifier's exit code.
    return BUILDIFIER_FORMAT_ERROR_CODE


if __name__ == "__main__":
    sys.exit(main())
