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

regex = re.compile(
    r"^(?P<filename>[^:]*):(?P<line>\d*):(?:(?P<column>\d*):)? (?P<message_id>[^:]*): (?P<message>.*?) \((?P<message_url>.*?)\)$",
    re.MULTILINE | re.DOTALL
)

BUILDIFIER_VERSION_PATTERN = re.compile(r"^buildifier version: ([\.\w]+)$", re.MULTILINE)

# https://github.com/bazelbuild/buildtools/blob/master/buildifier/buildifier.go#L333
# Buildifier error code for "needs formatting". We should fail on all other error codes > 0
# since they indicate a problem in how Buildifier is used.
BUILDIFIER_FORMAT_ERROR_CODE = 4

VERSION_ENV_VAR = "BUILDIFIER_VERSION"

WARNINGS_ENV_VAR = "BUILDIFIER_WARNINGS"

BUILDIFIER_RELEASES_URL = "https://api.github.com/repos/bazelbuild/buildtools/releases"

BUILDIFIER_DEFAULT_DISPLAY_URL = "https://github.com/bazelbuild/buildtools/tree/master/buildifier"


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


def print_error(failing_task, message):
    output = "##### :bazel: buildifier: error while {}:\n".format(failing_task)
    output += "<pre><code>{}</code></pre>".format(html.escape(message))
    if "BUILDKITE_JOB_ID" in os.environ:
        output += "\n\nSee [job {job}](#{job})\n".format(job=os.environ["BUILDKITE_JOB_ID"])

    upload_output(output)


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


def run_buildifier(binary, flags, files=None, version=None, what=None):
    label = "+++ :bazel: Running "
    if version:
        label += "Buildifier " + version
    else:
        label += "unreleased Buildifier"
    if what:
        label += ": " + what

    eprint(label)

    args = [binary] + flags
    if files:
        args += files

    return subprocess.run(args, capture_output=True, universal_newlines=True)


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

    return {r["tag_name"]: get_release_urls(r) for r in json.loads(content) if not r["prerelease"]}


def get_release_urls(release):
    buildifier_assets = [
        a for a in release["assets"] if a["name"] in ("buildifier", "buildifier.linux")
    ]
    if not buildifier_assets:
        raise Exception("There is no Buildifier binary for release {}".format(release["tag_name"]))

    return release["html_url"], buildifier_assets[0]["browser_download_url"]


def download_buildifier(url):
    path = os.path.join(tempfile.mkdtemp(), "buildifier")
    with closing(urlopen(url)) as response:
        with open(path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
    os.chmod(path, 0o755)
    return path


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    buildifier_binary = "buildifier"
    display_url = BUILDIFIER_DEFAULT_DISPLAY_URL
    version = os.environ.get(VERSION_ENV_VAR)
    if version:
        eprint("+++ :github: Downloading Buildifier version '{}'".format(version))
        try:
            version, display_url, download_url = get_buildifier_info(version)
            eprint("Downloading Buildifier {} from {}".format(version, download_url))
            buildifier_binary = download_buildifier(download_url)
        except Exception as ex:
            print_error("downloading Buildifier", str(ex))
            return 1

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

    # Determine Buildifier version if the user did not request a specific version.
    if not version:
        eprint("+++ :female-detective: Detecting Buildifier version")
        version_result = run_buildifier(buildifier_binary, ["--version"], what="Version info")
        match = BUILDIFIER_VERSION_PATTERN.search(version_result.stdout)
        version = match.group(1) if match and match.group(1) != "redacted" else None

    # Run formatter before linter since --lint=warn implies --mode=fix,
    # thus fixing any format issues.
    formatter_result = run_buildifier(
        buildifier_binary, ["--mode=check"], files=files, version=version, what="Format check"
    )
    if formatter_result.returncode and formatter_result.returncode != BUILDIFIER_FORMAT_ERROR_CODE:
        print_error("checking format", formatter_result.stderr)
        return formatter_result.returncode

    # Format: "<file name> # reformated"
    unformatted_files = [l.partition(" ")[0] for l in formatter_result.stdout.splitlines()]
    if unformatted_files:
        eprint(
            "+++ :construction: Found {} file(s) that must be formatted".format(
                len(unformatted_files)
            )
        )

    lint_flags = ["--lint=warn"]
    warnings = os.getenv(WARNINGS_ENV_VAR)
    if warnings:
        eprint("Running Buildifier with the following warnings: {}".format(warnings))
        lint_flags.append("--warnings={}".format(warnings))

    linter_result = run_buildifier(
        buildifier_binary, lint_flags, files=files, version=version, what="Lint checks"
    )
    if linter_result.returncode == 0 and not unformatted_files:
        # If buildifier was happy, there's nothing left to do for us.
        eprint("+++ :tada: Buildifier found nothing to complain about")
        return 0

    output = ""
    if unformatted_files:
        output = create_heading("format", len(unformatted_files))
        display_version = " {}".format(version) if version else ""
        output += (
            "Please download <a href=\"{}\">buildifier{}</a> and run the following "
            "command in your workspace:<br/><pre><code>buildifier {}</code></pre>"
            "\n".format(display_url, display_version, " ".join(unformatted_files))
        )

    # Parse output.
    if linter_result.returncode:
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
    return max(linter_result.returncode, formatter_result.returncode)


if __name__ == "__main__":
    sys.exit(main())
