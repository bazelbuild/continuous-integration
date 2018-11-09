# Bazel Release Playbook

Authors: lpino@, pcloudy@, laurentlb@

Status: Work in progress

Last Updated: 2018-11-09

Link to this document: go/bazel-release-playbook

Congratulations, you're the new release manager!

Each release has a tracking bug (see the list on http://go/bazel-release). The bug
includes a "Target RC date". On that day, create a new release candidate.

## Creating a new release candidate

### Setup

Do these steps once per release.

*   Set up github ssh key if you haven't already.
    *    https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/
*   Find baseline commit and cherrypicks
    *    Check Bazel nightly build at
         https://buildkite.com/bazel/bazel-with-downstream-projects-bazel. If
         many downstream jobs are failing then this isnot a good baseline
         commit. If only a few downstream jobs are failing and the issues are
         known then this is a good baseline commit. Fixes for the known issues
         should be cherry-picked, any remaining issues should become release
         blockers.

### Create a Candidate

Create candidates with the release.sh script.

*   If it's the first candidate for this version, run:

    ```
    RELEASE_NUMBER=<CURRENT RELEASE NUMBER x.yy.z>
    BASELINE_COMMIT=01234567890abcdef # From the Setup phase
    git clone https://github.com/bazelbuild/bazel.git ~/bazel-release-$RELEASE_NUMBER
    cd ~/bazel-release-$RELEASE_NUMBER
    scripts/release/release.sh create $RELEASE_NUMBER $BASELINE_COMMIT [CHERRY_PICKS...]
    ```

    Note that the three-digit version is important: "0.19.0". not "0.19".

*   For cherry-picks, you need `--force_rc=N` where `N` is the number of the
    release candidate of `$RELEASE_NUMBER`. For example, the first time you do a
    cherry-pick (after the initial candidate), N will be 2.

    ```
    scripts/release/release.sh create --force_rc=2 $RELEASE_NUMBER $BASELINE_COMMIT [CHERRY_PICKS...]
    ```

*   If you already did some cherry-picks and you want to add more, use "git log"
    to find the latest commit (this corresponds to the last cherry-pick commit).
    Use that as the new baseline and list the new cherry-picks to add on top. Or
    simply re-use the same baseline and cherrypicks from the previous candidate,
    and add the new cherrypicks.

    ```
    scripts/release/release.sh create --force_rc=3 $RELEASE_NUMBER NEW_BASELINE_COMMIT [NEW_CHERRY_PICKS...]
    ```

*   Resolve conflicts if there are any, type `exit` when you are done, then the script will continue.
    *   WARNING: `release.sh create` handles conflicts in a subshell (which is why you need to type `exit`).

*   Check/edit release notes.

*   Run `release.sh push`. This uploads the candidate and starts the release
    process on BuildKite.

    ```
    scripts/release/release.sh push
    ```

*   Update GitHub issue with the command that was run and the new candidate name
    (ie, 0.19.1rc3).

*   Check BuildKite results at https://buildkite.com/bazel/release. You should
    see the `release-$RELEASE_NUMBER` branch here and a new build running for
    your release.

    *   If the build fails with "Build creator not allowed", simply start a new
        one by clicking on the "New build" button in the top right corner
        ([Issue
        #281](https://github.com/bazelbuild/continuous-integration/issues/281)).

*   Check the postsubmit test run for the release branch to ensure that all
    tests on all platforms pass with the version you're about to release.

    *   Go to https://buildkite.com/bazel/bazel-bazel and find the
        `release-$RELEASE_NUMBER` branch in the list. A build should
        automatically run. Make sure that it passes.

*   When it all looks good, go back to the job in the release pipeline, click
    "Unblock step" for the deployment step. This will upload the release
    candidate binaries to GitHub, https://releases.bazel.build and our apt-get
    repository.

    *   If you don't have the permission, ask one of the Buildkite org
        admins to add you to the
        [bazel-sheriffs](https://buildkite.com/bazel?team=bazel-sheriffs)
        group.

    *   If that worked, click "Unblock step" for the "Generate Announcement" step.

*   Prepare the release announcement on http://go/bazel-newsletters.
    *   Create a new section for the release. Populate using the generated text
        (from the "generate announcement" step).
    *   Reorganize the notes per category (C++, Java, etc.)
    *   Add a comment with "+[spomorski@google.com](mailto:spomorski@google.com)" so that he takes a look.
    *   Send an email to [blaze-devel](mailto:blaze-devel@google.com) asking for reviewers.

*   Copy & paste the generated text into a new e-mail and send it.
    *   The first line is the recipient address.
    *   The second line is the subject.
    *   The rest is the body of the message.

*   Trigger a new pipeline in BuildKite to test the release candidate with all the downstream projects.
    *   Go to https://buildkite.com/bazel/bazel-with-downstream-projects-bazel
    *   Click "New Build", then fill in the fields like this:
        *   Message: Test Release-0.14.0rc1 (Or any message you like)
        *   Commit: HEAD
        *   Branch: release-0.14.0

*   Look for failing projects in red.
    *   Compare the results with the latest Bazel release:
        *   Jobs built with the latest Bazel:
            https://buildkite.com/bazel?team=bazel
        *   Jobs built with release candidate: e.g.
            https://buildkite.com/bazel/bazel-with-downstream-projects-bazel/builds/287

        If a project is failing with release candidate but not with the latest
        Bazel release, then there's probably a regression in the candidate. Ask
        the Bazel sheriff if the problem is already noticed. If not, find out
        the culprit, file an issue at
        https://github.com/bazelbuild/bazel/issues and mark it as release
        blocker.


        If a project is failing with both release candidate and the latest Bazel
        release, it could be a breakage from the project itself. Go through the
        build history (eg.
        [TensorFlow_serving](https://buildkite.com/bazel/tensorflow-serving/builds?page=2))
        to confirm this, then file an issue to their owners.

    *   File bugs (**TODO: how to find the owner/project link?**)

*   Once issues are fixed, create a new candidate with the relevant cherry-picks.

## Push a release

1.  Verify that the following conditions **all apply**:
    1.  at least **2 weeks passed since you pushed RC1**, and
    1.  at least **2 business days passed since you pushed the last RC**, and
    1.  there are **no open [release-critical Blaze bugs](https://b.corp.google.com/hotlists/14305)** in Buganizer, and
    1.  there are **no open ["Release blocking" Bazel bugs](https://github.com/bazelbuild/bazel/labels/Release%20blocker)** on GitHub.
1.  Generate a new identifier: https://bazel.googlesource.com/new-password (and paste the code in your shell).
    This is only necessary the first time you handle a release.
1.  **Push the final release (do not cancel midway)**:

    ```
    scripts/release/release.sh release
    ```

1.  A CI job is uploading the release artifacts to GitHub. Look for the release
    workflow on https://buildkite.com/bazel/release/. Unblock the steps.

1.  Ensure all binaries were uploaded to GitHub properly.
    1.  **Why?** Sometimes binaries are uploaded incorrectly.
    1.  **How?** Go to the [GH releases
        page](https://github.com/bazelbuild/bazel/releases), click "Edit", see
        if there's a red warning sign next to any binary. You need to manually
        upload those; get them from Jenkins
        ([example](https://github.com/bazelbuild/bazel/issues/2158#issuecomment-265538453)).
1.  Update the release bug:
    1.  State the fact that you pushed the release
    1.  Ask the package maintainers to update the package definitions: @vbatts @petemounce
    1.  Example: [https://github.com/bazelbuild/bazel/issues/3773#issuecomment-352692144]
1.  Publish blog post (http://go/bazel-newsletters).


### Updating the Homebrew recipe

[Homebrew](http://brew.sh/index.html) is a package manager for OS X. This
section assumes that you are on a Mac OS machine with homebrew installed.

To update the `bazel` recipe on Homebrew, you must send a pull request to
https://github.com/bazelbuild/homebrew-tap


### Updating the Chocolatey package

As of November 2016, this is done by an external contributor,
[@petemounce](https://github.com/petemounce) on GitHub. Ping him when there's a
new release coming out.


### Updating the Fedora package

This is done by an external contributor, [@vbatts](https://github.com/vbatts) on
GitHub. Ping him when there's a new release coming out.

