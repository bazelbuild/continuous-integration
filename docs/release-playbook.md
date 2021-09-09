# Bazel Release Playbook

This is the guide to conducting a Bazel release. This is especially relevant for
release managers, but will be of interest to anyone who is curious about the
release process.

## Preface 

> For future reference and release managers - the release manager playbook should
> be treated like an IKEA manual. That means: Do not try to be smart, optimize /
> skip / reorder steps, otherwise chaos will ensue. Just follow it and the end
> result will be.. well, a usable piece of furniture, or a Bazel release
> (depending on the manual).
> 
> Like aviation and workplace safety regulations, the playbook is written in the
> tears and blood of broken Bazelisks, pipelines, releases and Git branches.
> Assume that every step is exactly there for a reason, even if it might not be
> obvious. If you follow them to the letter, they are not error prone. Errors
> have only happened in the past, when a release manager thought it's ok to
> follow them by spirit instead. ;)
> 
> -- @philwo

## Setup

Do this once.

*   Make sure you are a member of the Bazel [release-managers](https://buildkite.com/organizations/bazel-trusted/teams/release-managers/members)
    group.  If that link does not work for you, ask one of the Buildkite org admins to add you to
    the group.
*   Set up github ssh key if you haven't already.
    *    https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/
        
Do these steps once per release.

*   Find baseline commit and cherrypicks
    *    Check Bazel nightly build at
         https://buildkite.com/bazel/bazel-with-downstream-projects-bazel. If
         many downstream jobs are failing then this is not a good baseline
         commit. If only a few downstream jobs are failing and the issues are
         known then this is a good baseline commit. Fixes for the known issues
         should be cherry-picked, any remaining issues should become release
         blockers.
*   Begin the [internal release process](http://go/bazel-internal-launch-checklist), too.

## Release issue

Each release has a tracking bug (see the
[list](https://github.com/bazelbuild/bazel/issues?utf8=%E2%9C%93&q=label%3Arelease+)).
The last and the next releases should be pinned. The bug includes a "Target RC
date". On that day, create a new release candidate.

The release manager adds a comment to the issue with the following content:

```
# Status of Bazel X.Y

- Target baseline: [date]
- Expected release date: [date]
- [List of release blockers](https://github.com/bazelbuild/bazel/labels/Release%20blocker)

To report a release-blocking bug, please file a bug using the `Release blocker` label, and cc me.

Task list:

- [ ] Update GitHub issues for incompatible changes
- [ ] Pick release baseline:
- [ ] Create release candidate:
- [ ] Check downstream projects:
- [ ] [Create draft release announcement](https://docs.google.com/document/d/1wDvulLlj4NAlPZamdlEVFORks3YXJonCjyuQMUQEmB0/edit)
- [ ] Send for review the release announcement PR:
- [ ] Push the release, notify package maintainers:
- [ ] Update the documentation
- [ ] Push the blog post
- [ ] Update the [release page](https://github.com/bazelbuild/bazel/releases/)
```

Keep the task list updated and check boxes as you follow the release process. [Example](https://github.com/bazelbuild/bazel/issues/7816#issuecomment-497037232).


## Update the status of GitHub issues for incompatible changes

**This section is a place where you have to mechanically follow the entire process to the letter from beginning to end, even though it might seem unnecessary at times.**

In the below, _X.Y_ is a release you are cutting.

### Start new migration windows

1. Search for all [open "incompatible-change" issues that have "migration-ready" labels](https://github.com/bazelbuild/bazel/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+label%3Aincompatible-change+label%3Amigration-ready)
1. For each such issue:
     1. Add a "migration-_X.Y_" label.
     2. Add a "breaking-change-_X.Y+w_" label where _w_ is the length of migration window for that particular issue
     2. Remove "migration-ready" label

### Review breaking changes

(skip this section if you're not creating a major release)

1. Search for issues with label "breaking-change-_X.Y_".
2. For all such issues that are **closed**, verify that the flag is flipped and release notes mention the breaking change.
   1. If the flag is not flipped, you probably need to reopen the issue and follow the steps as if the issue was open. Ping the author as well.
   1. If the release notes do not mention the breaking change, manually add the flag to the release notes (under "Prepare the Release Announcement" section). 
2. For all such issues that are still **open**:
   1. remove the label "breaking-change-_X.Y_".
   1. add a label "migration-_X.Y_" and "breaking-change-_X.Y+1_" (this prolongs the migration window by 1 release).
   1. Reach out to the issue owner.

### Prolong ongoing migration windows

1. Search for issues with labels "migration-_X.Y-1_" that are not "migration-_X.Y_" and not "breaking-change-_X.Y_"
2. For all such issues, apply "migration-_X.Y_" label. Do **not** remove any previous "migration-_X.Y-1_" labels.

## Create a Candidate

Create candidates with the `release.sh` script. See above how to pick a good baseline commit.

*  If it's the first candidate for this version, run:

    ```bash
    RELEASE_NUMBER=<CURRENT RELEASE NUMBER x.yy.z>
    BASELINE_COMMIT=01234567890abcdef # From the Setup phase
    git clone https://github.com/bazelbuild/bazel.git ~/bazel-release-$RELEASE_NUMBER
    cd ~/bazel-release-$RELEASE_NUMBER
    scripts/release/release.sh create $RELEASE_NUMBER $BASELINE_COMMIT [CHERRY_PICKS...]
    ```

    Note that the three-digit version is important: "0.19.0". not "0.19".

*  For cherry-picks, you need `--force_rc=N` where `N` is the number of the
    release candidate of `$RELEASE_NUMBER`. For example, the first time you do a
    cherry-pick (after the initial candidate), N will be 2.

    ```bash
    scripts/release/release.sh create --force_rc=2 $RELEASE_NUMBER $BASELINE_COMMIT [CHERRY_PICKS...]
    ```

*  If you already did some cherry-picks and you want to add more, use "git log"
    to find the latest commit (this corresponds to the last cherry-pick commit).
    Use that as the new baseline and list the new cherry-picks to add on top. Or
    simply re-use the same baseline and cherrypicks from the previous candidate,
    and add the new cherrypicks.

    ```bash
    scripts/release/release.sh create --force_rc=3 $RELEASE_NUMBER NEW_BASELINE_COMMIT [NEW_CHERRY_PICKS...]
    ```

Resolve conflicts if there are any, type `exit` when you are done, then the script will continue.
WARNING: `release.sh create` handles conflicts in a subshell (which is why you need to type `exit`).

Editing the release notes is not needed (it will be done later).

## Push the candidate

1.  Run `release.sh push`. This uploads the candidate and starts the release
    process on BuildKite.

    ```bash
    scripts/release/release.sh push
    ```

1.  Update GitHub issue with the command that was run and the new candidate name
    (ie, 0.19.1rc3). Update the issue with the estimated release date, assuming no
    regression is found.

1.  Check BuildKite results at https://buildkite.com/bazel-trusted/bazel-release. You should
    see the `release-$RELEASE_NUMBER` branch here and a new build running for
    your release.

1.  Check the postsubmit test run for the release branch to ensure that all
    tests on all platforms pass with the version you're about to release.

    *   Go to https://buildkite.com/bazel/bazel-bazel and find the
        `release-$RELEASE_NUMBER` branch in the list. A build should
        automatically run. Make sure that it passes.

1.  When it all looks good, go back to the job in the
    [release pipeline](https://buildkite.com/bazel-trusted/bazel-release/builds),
    click "Deploy release artifacts" for the deployment step.

    *   This will upload the release candidate binaries to GitHub and our 
        apt-get repository. The github link is probably of the form:
        https://releases.bazel.build/3.6.0/rc1/index.html

1.  If that worked, click on the "Generate announcement mail text" step to unblock it.
    If it's the first release candidate, prepare the release announcement (see
    next section).

1.  Copy & paste the generated text into a new e-mail and send it. If you're
    creating a new release candidate, reply to the previous e-mail to keep all
    the information in one thread.
    *   The first line is the recipient address.
    *   The second line is the subject.
    *   The rest is the body of the message.
    *   Replace the generated notes with a link to the release announcement draft.
       `https://docs.google.com/document/d/1wDvulLlj4NAlPZamdlEVFORks3YXJonCjyuQMUQEmB0/view`

1.  Trigger a new pipeline in BuildKite to test the release candidate with all the downstream projects.
    *   Go to https://buildkite.com/bazel/bazel-with-downstream-projects-bazel
    *   Click "New Build", then fill in the fields like this:
        *   Message: Test Release-3.0.0rc2 (Or any message you like)
        *   Commit: HEAD
        *   Branch: release-3.0.0rc2

1.  Look for failing projects in red.
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

1.  Once issues are fixed, create a new candidate with the relevant cherry-picks.

## Release announcement

The release manager is responsible for the [draft release
announcement](https://docs.google.com/document/d/1wDvulLlj4NAlPZamdlEVFORks3YXJonCjyuQMUQEmB0/edit).

Once the first candidate is available:

1.  Open the doc, create a new section with your release number, add a link to
    the GitHub issue.
1.  Copy & paste the generated text from the "Generate Announcement" step.
1.  Reorganize the notes per category (C++, Java, etc.).
1.  For each category, add a comment and assign it to the corresponding
    [team contact](https://www.bazel.build/maintainers-guide.html#team-labels):
    "+person for review (see guidelines at the top of the doc)".
1.  Send an email to [bazel-dev](https://groups.google.com/forum/#!forum/bazel-dev) for
    additional reviews.
1.  Assign a comment to "+[aiuto@google.com](mailto:aiuto@google.com)"
    and "+[daroberts@google.com](mailto:daroberts@google.com)"
    for a global review.

After a few days of iteration:

1.  Make sure all comments have been resolved, and the text follows the
    guidelines (see "How to review the notes?" in the document).
1.  Send a pull request to [bazel-blog](https://github.com/bazelbuild/bazel-blog/).

## Release requirements

1.  The release announcement must be ready (the pull request has been reviewed).
1.  Verify that the [conditions outlined in our policy](https://bazel.build/support.html#policy) **all apply**. As of
    May 2019 those were the following, but _double check_ that they have not changed since then.
    1.  at least **1 week passed since you pushed RC1**, and
    1.  at least **2 business days passed since you pushed the last RC**, and
    1.  there are **no open ["Release blocking" Bazel bugs](https://github.com/bazelbuild/bazel/labels/Release%20blocker)** on GitHub.

## Push a release

1.  Generate a new identifier: https://bazel.googlesource.com/new-password (and paste the code in your shell).
    This is only necessary the first time you handle a release.
1.  **Push the final release (do not cancel midway)**:

    ```bash
    scripts/release/release.sh release
    ```

1.  A CI job is uploading the release artifacts to GitHub. Look for the release
    workflow on https://buildkite.com/bazel-trusted/bazel-release/. Unblock the steps.

1.  Ensure all binaries were uploaded to GitHub properly.
    1.  **Why?** Sometimes binaries are uploaded incorrectly.
    1.  **How?** Go to the [GH releases page](https://github.com/bazelbuild/bazel/releases),
        click "Edit", see if there's a red warning sign next to any binary. You
        need to manually upload those; get them from
        `https://storage.googleapis.com/bazel/$RELEASE_NUMBER/release/index.html`.
1.  Update the release bug:
    1.  State the fact that you pushed the release
    1.  Ask the package maintainers to update the package definitions:
        [@vbatts](https://github.com/vbatts) [@petemounce](https://github.com/petemounce) [@excitoon](https://github.com/excitoon)
    1.  Example: [https://github.com/bazelbuild/bazel/issues/3773#issuecomment-352692144]
1.  Publish versioned documentation
    1.  Fetch the git tag for the release: `git fetch --tags`
    1.  Do a checkout to that tag: `git checkout $RELEASE_NUMBER`
        1. You should see this message (e.g. for 0.21.0):

        ```
        $ git checkout 0.21.0
        Note: checking out '0.21.0'.

        You are in 'detached HEAD' state. You can look around, make experimental
        changes and commit them, and you can discard any commits you make in this
        state without impacting any branches by performing another checkout.

        If you want to create a new branch to retain commits you create, you may
        do so (now or later) by using -b with the checkout command again. Example:

        git checkout -b <new-branch-name>

        HEAD is now at defd737761 Release 0.21.0 (2018-12-19)
        ```
    1.  [Install `gsutil`](https://cloud.google.com/storage/docs/gsutil_install)
        and ensure you have access to the `bazel-public` GCP project.
    1.  Run `scripts/docs/generate_versioned_docs.sh`. If you get interrupted,
        it is safe to re-run the script. This script will build the web assets
        for the documentation, generate a tarball from them, and push the
        tarball to Google Cloud Storage.
        * The script will fail to run if you're not in a git checkout of a
          release.
        * If the tarball has already been pushed to GCS, this script will not
          overwrite the existing tarball.
    1.  Update `site/_config.yml` and `scripts/docs/doc_versions.bzl` with `$RELEASE_NUMBER`.
         1. `site/_config.yml`: set `version:` to `$RELEASE_NUMBER` and add `$RELEASE_NUMBER` to `doc_versions:`.
         1. `scripts/docs/doc_versions.bzl`: add the following list item to `DOC_VERSIONS`
            <pre>
            {
               "version": "<i>$RELEASE_NUMBER</i>",
               "sha256": "<i>result of `sha256sum bazel-bin/site/jekyll-tree.tar`</i>",
            },
            </pre>
         1. After the changes are submitted, it will take 30 mins-1 hour for them to show up on bazel.build.

1.  Merge the blog post pull request.
    1.  Make sure you update the date in your post (and the path) to reflect when
    it is actually published.
    1.  **Note:** The blog sometimes takes time to update the homepage, so use
    the full path to your post to check that it is live.
1.  Update the [release page](https://github.com/bazelbuild/bazel/releases/) to
    replace the generated notes with a link to the blog post.
1.  Close the release-tracking bug. If you need to do a patch release, create a
    new tracking bug.

### Updating Google's internal mirror

Please ping @philwo and @meteorcloudy to copy the release binary to their
internal mirror.


### Updating the Homebrew recipe

[Homebrew](http://brew.sh/index.html) is a package manager for OS X. This
section assumes that you are on a Mac OS machine with homebrew installed.

To update the `bazel` recipe on Homebrew, you can send a pull request to
https://github.com/Homebrew/homebrew-core/blob/master/Formula/bazel.rb.

Example: https://github.com/Homebrew/homebrew-core/pull/57966

However, usually the Homebrew community takes care of this reasonably
quickly, so feel free to skip this step, if you aren't familiar with it.


### Updating the Chocolatey package

As of November 2016, this is done by an external contributor,
[@petemounce](https://github.com/petemounce) on GitHub. Ping him when there's a
new release coming out.


### Updating the Scoop pakage

As of February 2019, this is done by an external contributor,
[@excitoon](https://github.com/excitoon) on GitHub. [Ping him](http://telegram.me/excitoon) when there's a
new release coming out.


### Updating the Fedora package

This is done by an external contributor, [@vbatts](https://github.com/vbatts) on
GitHub. Ping him when there's a new release coming out.
