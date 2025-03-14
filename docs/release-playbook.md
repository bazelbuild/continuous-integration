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

## One-time setup

These steps only have to be performed once, ever.

*   Make sure you are a member of the Bazel [Release Managers](https://github.com/orgs/bazelbuild/teams/release-managers/members) team on GitHub.
*   Make sure you are a member of the Bazel [release-managers](https://buildkite.com/organizations/bazel-trusted/teams/release-managers/members)
    group on BuildKite.  If that link does not work for you, ask one of the Buildkite org admins to add you to
    the group.
*   Set up github ssh key if you haven't already.
    *    https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/
*   Generate a new identifier for Google's internal Git mirror: https://bazel.googlesource.com/new-password (and paste the code in your shell).
*   Log in to the Gerrit UI to create an account: https://bazel-review.git.corp.google.com/ (without this step, you will see errors such as `error_type: PERMISSION_DENIED_BY_GERRIT_ACL` and `"\'git push\' requires a Gerrit user account."` when running the release script.

## Preparing a new release

1.  [Create a release blockers milestone](https://github.com/bazelbuild/bazel/milestones/new) named "X.Y.Z release blockers" (case-sensitive), where we keep track of issues that must be resolved before the release goes out.
    *   Set the (tentative) release date.
    *   Add this description: `Issues that need to be resolved before the X.Y.Z release.`.
    *   Refer to [this example](https://github.com/bazelbuild/bazel/milestone/38)
1.  [Create a release tracking issue](https://github.com/bazelbuild/bazel/issues/new?assignees=&labels=release%2Cteam-OSS%2CP1%2Ctype%3A+process&template=release.md&title=Release+X.Y+-+%24MONTH+%24YEAR) to keep the community updated about the progress of the release. [See example](https://github.com/bazelbuild/bazel/issues/16159). Pin this issue.
1.  Create the branch for the release. The branch should always be named `release-X.Y.Z` (the `.Z` part is important). Cherry-pick PRs will be sent against this branch.
    *   The actual creation of the branch can be done via the GitHub UI or via the command line. For minor and patch releases, create the branch from the previous release tag, if possible. How we choose the base commit of the branch depends on the type of the release:
    *   For patch releases (`X.Y.Z` where `Z>0`), the base commit should simply be `X.Y.(Z-1)`.
    *   For minor releases (`X.Y.0` where `Y>0`), the base commit should typically be `X.(Y-1).<current max Z>`.
    *   For major releases (`X.0.0`), the base commit is some "healthy" commit on the main branch.
        *   This means that there's an extra step involved in preparing the release -- "cutting" the release branch, so to speak. For this, check the [Bazel@HEAD+Downstream pipeline](https://buildkite.com/bazel/bazel-with-downstream-projects-bazel). The branch cut should happen on a green commit there; if the pipeline is persistently red, work with the Green Team to resolve it first and delay the branch cut as needed.
        *   A first release candidate should immediately be created after the release branch is created. See [create a release candidate](#create-a-release-candidate) below.
1.  After creating the branch, edit the CODEOWNERS file on that branch, replace the entire contents of the file with the line `* @your-github-username` and submit it directly.
    *   This makes sure that all PRs sent against that branch have you as a reviewer.
1.  Update the MODULE.bazel file in the new branch. Change the version in the module to the version of the new release branch. For example, if the new release branch is `release-8.1.0`, then change the version to `8.1.0` like below.
    * ```
        module(
            name = "bazel",
            version = "8.1.0",
            repo_name = "io_bazel",
        )
      ```
1.  Update the branch name in the scheduled build for release branches by editing the "build branch" field [here](https://buildkite.com/bazel/bazel-at-head-plus-downstream/settings/schedules/b63d6589-2658-4850-a9b9-b588b9ea5c99/edit). Set it to `release-X.Y.Z` so that downstream tests run against this branch.
1.  Ping [@meteorcloudy](https://github.com/meteorcloudy) to configure a [GitHub merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue#about-merge-queues) for this new branch.
1.  (For minor release only) Send an email to bazel-discuss@googlegroups.com announcing the next release.
    *   It should contain the text: `The Bazel X.Y.Z release branch (release-X.Y.Z [link]) is open for business. Please send cherry-pick PRs against this branch if you'd like your change to be in X.Y.Z. Please follow the release tracking issue [link] for updates.`
1.  Meanwhile, begin the [internal approval process](http://go/bazel-internal-launch-checklist), too.
    *   Note that certain steps in the internal approval process require at least preliminary release notes, so those steps should usually wait until the first release candidate is pushed and the release notes have taken vague shape.
    *   Please make sure that the Eng team review status is explicit in the release announcement doc. The release notes should be approved before starting the internal review process.

## Maintaining the release

While the release is active, you should make sure to do the following:

*   Monitor [the "potential release blocker" label](https://github.com/bazelbuild/bazel/issues?q=label%3A%22potential+release+blocker%22).
    *   These are issues or PRs that community members have proposed to be fixed/included in the next release. Check each of these and decide whether they should be release blockers; if so, add a comment with the text `@bazel-io fork X.Y.Z` and a copy of the issue will be added to the "X.Y.Z release blockers" milestone; if not, explain why in a comment, and remove the "potential release blocker" label.
*   For cherry-picks,
    *   If a Bazel team member has proposed the fixes, then proceed with the cherry-pick and merge it.
    *   If a Bazel team member authors a commit and a community member asks to cherry-pick, then confirm with the author before cherry-picking the PR to make sure this change is safe to merge.
    *   If a community member author a commit and asks to cherry-pick, then confirm with the reviewer before cherry-picking the PR to make sure that the change is safe to merge.
    *   **Notes:**
        *   All cherry-pick PRs sent to a release branch should be reviewed and approved by a Bazel team member (usually the reviewer of the original PR)
        *   Before merging a change into the release branch, confirm that the original change is already merged at Bazel@HEAD. One simple way to do this is to make sure all cherry-picked commits contain `PiperOrigin-RevId: <CL number>` in the commit message. For some exceptions, if it's really specific to the release branch, include a good reason in the PR description and make sure it's signed-off by a Bazel team member.
        *   If a requested cherry-pick has merge conflicts that cannot be resolved without cherry-picking additional commits, ask the author of the original commit to submit a PR directly against the release branch.
        *   After RC1, cherry-picks are limited to critical fixes only. If a cherry-pick is needed, ask the requester to answer the following questions: Why is this change critical, and what benefits does it provide? What is the likelihood of this change introducing a regression?
*   Review any PRs sent to the release branch and merge them as necessary.
    *   Make sure to close any related release blocker issues after merging the PRs; merging PRs into non-main branches does *not* automatically close related issues (see [GitHub docs](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue)).
    *   Before closing a release blocker issue, add a comment indicating how the issue was resolved, for better tracking (e.g. `cherry-picked in #XYZ` - see [this example](https://github.com/bazelbuild/bazel/issues/16629#issuecomment-1302743541))
*   Periodically check downstream tests that are run against the release branch to catch any breakages early on in the process. If you see any failures that don't appear at HEAD, reach out to the Bazel team, open an issue if needed, and add the issue to the release blockers list.
*   When enough PRs have been cherry-picked and the release is nearing a ready state, create a release candidate (see [below](#create-a-release-candidate)).
    *   One week before pushing the final release candidate, go through all the remaining issues on the milestone to triage and add the "soft-release-blocker" label.
    *   Make sure all issues without the "soft-release-blocker" label are addressed before the final release.
*   Keep the task list in the release tracking issue updated and check boxes as you follow the release process.
    *   In particular, try and keep the estimated release date updated.
*   If there is a request to backport a fix to a previous minor release, then add the "potential N.x cherry-picks" label (for example, if we just released 7.2.0 release, but there is a request to make some changes to fix 6.4.0, then we should put the label, "potential 6.x cherry-picks" label). If there are about five or more issues/PRs with the label, then we should start a discussion to release a new minor release for the previous LTS track.
    *   Note: Create and monitor this label when once we start working on a major release; we'll always have another minor release in the previous LTS track.

## Create a release candidate

1.  Create a branch (via the GitHub UI or via the command line) named `release-X.Y.ZrcN` at the appropriate commit.
    *   This branch is essentially used as a tag (i.e. no further commits should happen on this branch). All cherry-pick commits should continue to go into the release branch (i.e. `release-X.Y.Z`, without the `rcN` part).

1.  Check BuildKite results at https://buildkite.com/bazel-trusted/bazel-release. You should
    see the `release-X.Y.ZrcN` branch here and a new build running for
    your release. When building a patch release for a previous LTS version, make sure to set USE_BAZEL_VERSION=X.Y.(Z-1).
    For example:
    *   Go to https://buildkite.com/bazel-trusted/bazel-release
    *   Click on "New Build" and set the following:
        *   Message: Release-4.2.3rc1 (Or any message you like)
        *   Commit: HEAD
        *   Branch: release-4.2.3rc1
        *   Option: USE_BAZEL_VERSION=4.2.2
    *   If the previous version requires changes to the pipeline, create a new branch in the continuous-integration repository with the required changes (see release-4.2.4 [example](https://github.com/bazelbuild/continuous-integration/tree/release-4.2.4)) and explicitly set the buildkite script path. Refer to [this example](https://buildkite.com/bazel-trusted/bazel-release/builds/1076#01879e91-7694-420d-bc1a-4be9f84c0c51).
1.  Check the postsubmit test run for the release branch to ensure that all
    tests on all platforms pass with the version you're about to release.

    *   Go to https://buildkite.com/bazel/bazel-bazel and find the
        `release-X.Y.ZrcN` branch in the list. A build should
        automatically run. Make sure that it passes.

1.  When it all looks good, go back to the job in the
    [release pipeline](https://buildkite.com/bazel-trusted/bazel-release/builds),
    click "Deploy release artifacts" for the deployment step.

    *   This will upload the release candidate binaries to GitHub and our
        apt-get repository. The link is probably of the form:
        https://releases.bazel.build/3.6.0/rc1/index.html

1.  If that worked, click on the "Generate release notes" step to unblock it. If this is the first release candidate, copy and paste the generated text into the release announcements doc. For rcX where X>2, compare the generated notes with the release announcements working doc and add only the new/missing notes. Refer to the "Release announcement" section below for more details.

1. Confirm that the RC published to GitHub looks good. If it's the first RC, add a note stating that the release notes are still being reviewed.

1.  Send out an email to `bazel-discuss@googlegroups.com` about the new release candidate. E.g.:
    *   Subject: Bazel 7.0.1 release candidate 1 is available for testing
    *   Body:
    ```
    Bazel 7.0.1rc1 is now available for those that want to try it out.

    You can download it from here: https://github.com/bazelbuild/bazel/releases/tag/7.0.1rc1

    If you're using Bazelisk, you can point to this RC by setting USE_BAZEL_VERSION=7.0.1rc1.

    Please test it out and report any issues [here](https://github.com/bazelbuild/bazel/issues) as soon as possible.
    A draft of the release notes can be found [here](https://docs.google.com/document/d/1pu2ARPweOCTxPsRR8snoDtkC9R51XWRyBXeiC6Ql5so/edit?usp=sharing).
    ```

1.  Add a comment to the release GitHub issue announcing that a new RC is out. See [example](https://github.com/bazelbuild/bazel/issues/20470#issuecomment-1889975586).

1.  Post on the #general channel on the [Bazel Slack](https://bazelbuild.slack.com/) announcing that a new RC is out. See [example](https://bazelbuild.slack.com/archives/CA31HN1T3/p1705095377557259).

1. Post a comment on all internal chats announcing that a new RC is out.

1.  Post a comment on all issues / PRs addressed in this RC to ask users to test (this is a manual step for now but will eventually be automated).

    Issues:
      ```
      A fix for this issue has been included in [Bazel 7.0.2 RC1](https://github.com/bazelbuild/bazel/releases/tag/7.0.2rc1). Please test out the release candidate and report any issues as soon as possible.
    If you're using Bazelisk, you can point to the latest RC by setting USE_BAZEL_VERSION=7.0.2rc1. Thanks!
      ```
    PRs:
      ```
      The changes in this PR have been included in [Bazel 6.5.0 RC2](https://github.com/bazelbuild/bazel/releases/tag/6.5.0rc2). Please test out the release candidate and report any issues as soon as possible.
    If you're using Bazelisk, you can point to the latest RC by setting USE_BAZEL_VERSION=6.5.0rc2. Thanks!
      ```

1.  Trigger a new pipeline in BuildKite to test the release candidate with all the downstream projects.
    *   Go to https://buildkite.com/bazel/bazel-with-downstream-projects-bazel
    *   Click "New Build", then fill in the fields like this:
        *   Message: Test Release-3.0.0rc2 (Or any message you like)
        *   Commit: HEAD
        *   Branch: release-3.0.0rc2
    *   **Note:** Make sure that downstream builds for the release candidate don't have any extra breakages compared to Bazel@HEAD so that Bazel postsubmits won’t be broken after the release.

1. Trigger a new pipeline in BuildKite to test the release candidate with top BCR modules.
    *   Go to https://buildkite.com/bazel/bcr-bazel-compatibility-test
    *   Click "New Build", then fill in the fields like this:
        *   Message: Test Bazel 8.0.0rc2 with top BCR modules (Or any message you like)
        *   Environment Variables:
            - USE_BAZEL_VERSION=8.0.0rc2
            - SELECT_TOP_BCR_MODULES=100
            - SKIP_WAIT_FOR_APPROVAL=1
    * For a major release, BCR modules might be broken due to incompatible changes. In this case, file or update an issue in the BCR repository to report those breakages.
      For example, [#3056](https://github.com/bazelbuild/bazel-central-registry/issues/3056).
    * For a minor release, BCR modules should be passing if there is no previous known breakages reported during the major release test. If there are new breakages, that means there is probably a regression in the release candidate. In this case, file an issue in the Bazel repo and ask the Bazel team to investigate.

1.  Once issues are fixed, create a new candidate with the relevant cherry-picks.

## Release announcement

The release manager is responsible for the [draft release
announcement](https://docs.google.com/document/d/1pu2ARPweOCTxPsRR8snoDtkC9R51XWRyBXeiC6Ql5so/edit).

Once the first candidate is available:

1.  Open the doc, create a new section with your release number, add a link to
    the GitHub issue. Note that there should be a new Bazel Release Announcement document for every major release. For minor and patch releases, use the latest open doc.
1.  Copy & paste the generated text from the "Generate release notes" step.
1.  Reorganize the notes per category (C++, Java, etc.).
1.  Assign a comment to "+[pcloudy@google.com](mailto:pcloudy@google.com)" and "+[wyv@google.com](mailto:wyv@google.com)" for initial review.
1.  Once approved, for each category, add a comment and assign it to the corresponding
    [team contact](https://bazel.build/contribute/maintainers-guide?hl=en#team-labels):
    "+person for review (see guidelines at the top of the doc)".

For each subsequent release candidate:

1. Ensure that new commits are documented in the release announcement doc.
2. Assign a comment to "+[pcloudy@google.com](mailto:pcloudy@google.com)" and "+[wyv@google.com](mailto:wyv@google.com)" for another review, if the changes are significant.
3. If needed, assign relevant sections to the corresponding TLs for additional edits and review.

After a few days of iteration:

1.  Make sure all comments have been resolved, and the text follows the
    guidelines (see "How to review the notes?" in the document).
1.  [For major releases only] Ping "+[radvani@google.com](mailto:radvani@google.com)" to coordinate on publishing a blog post. Send a pull request to [bazel-blog](https://github.com/bazelbuild/bazel-blog/) with release notes if needed.

## Release requirements

1.  The release announcement must be ready and approved.
1.  The internal approval process is complete with all approvals granted.
1.  Verify that the [conditions outlined in our policy](https://bazel.build/release#release-procedure-policies) **all apply**. As of
    July 2023 those were the following, but _double check_ that they have not changed since then.
    1.  there are no more release blocking issues
    2.  at least **2 business days passed since you pushed the last RC**
    3.  [for major and minor releases only] at least **1 week passed since you pushed RC1**
    4.  the next day is a business day (i.e. no releases on Fridays or weekends)

Note: the above policies are for final releases only. RCs can be created without waiting for days in between each.

## Push a release

1.  **Push the final release (do not cancel midway)** by running the following commands in a Bazel git repo on a Linux machine. But first make sure that:
      * the master branch is up to date to avoid overwriting parts of the CHANGELOG file
      * the final `release-X.Y.ZrcN` branch is identical to the `release-X.Y.Z` branch to avoid missing any commits

    ```bash
    git fetch origin release-X.Y.ZrcN
    git checkout release-X.Y.ZrcN
    scripts/release/release.sh release
    ```

    **Warning**: If this process is interrupted for any reason, please check the following before running:
      * Both `release-X.Y.ZrcN` and `master` branch are restored to the previous clean state (without addtional release commits). Without this step, you may see errors and/or multiple commits pushed.
      * Release tag is deleted locally (`git tag -d X.Y.Z`), otherwise rerun will cause an error that complains the tag already exists.

1.  A CI job is uploading the release artifacts to GitHub. Look for the release
    workflow on https://buildkite.com/bazel-trusted/bazel-release/. When building a patch release for a previous LTS version, follow the same steps above as you did when creating a release candidate (set `USE_BAZEL_VERSION`, etc.).
    * Once all the steps are complete, click on "Deploy release artifacts" to unblock it. Subsequently you should see the updated version in Github.
        * Ensure all binaries were uploaded to GitHub properly.
            * **Why?** Sometimes binaries are uploaded incorrectly.
            * **How?** Go to the [GH releases page](https://github.com/bazelbuild/bazel/releases),
                click "Edit", see if there's a red warning sign next to any binary. You
                need to manually upload those; get them from
                `https://storage.googleapis.com/bazel/$RELEASE_NUMBER/release/index.html`.
    * Once the binaries are uploaded and the GitHub release page looks correct, click on "Build and Publish" to unblock this step.
    * Verify that the Chocolatey package has been successfully uploaded here: `https://community.chocolatey.org/packages/bazel/<version>`, e.g. [6.2.0](https://community.chocolatey.org/packages/bazel/6.2.0), [6.2.0-rc2](https://community.chocolatey.org/packages/bazel/6.2.0-rc2).
    * Verify that the docker container has been successfully build, pushed, and tagged as `latest` if needed, by checking the container registry. If there are any issues, follow the [instructions](../bazel/oci/README.md) to manually perform these steps. Ping [@meteorcloudy](https://github.com/meteorcloudy) for help.

1.  Update the release bug:
    1.  State the fact that you pushed the release
    2.  Add links to the GitHub and release pages
    3.  Ask the package maintainers to update the package definitions:
        [@vbatts](https://github.com/vbatts) [@excitoon](https://github.com/excitoon)
    1.  Example: [https://github.com/bazelbuild/bazel/issues/17695#issuecomment-1540757336]
1.  Publish versioned documentation by following [go/bazel-release-docs](http://go/bazel-release-docs) (for major and minor releases only)
    1.  Make sure  the documentation is built and ready to be published after the final RC has been created, in order to avoid any delays.
1.  [For major releases only] Coordinate with "+[radvani@google.com](mailto:radvani@google.com)" and merge the blog post pull request as needed.
    1.  Make sure you update the date in your post (and the path) to reflect when
    it is actually published.
    1.  **Note:** The blog sometimes takes time to update the homepage, so use
    the full path to your post to check that it is live.
1.  For major releases, update the release page to replace the generated notes with the structured releases notes from the release announcement doc and link to the blog post (see [example](https://github.com/bazelbuild/bazel/releases/tag/6.0.0)). For minor and patch release, update the release notes without a blog post link - see [example](https://github.com/bazelbuild/bazel/releases/tag/6.1.0).
1.  Send out an email to `bazel-discuss@googlegroups.com` about the new release. E.g.:
    *   Subject: Bazel 6.2.0 is released
    *   Body:
    ```
    Bazel 6.2.0 is now available: https://github.com/bazelbuild/bazel/releases/tag/6.2.0
    ```
1.  Post on the #general channel on the [Bazel Slack](https://bazelbuild.slack.com/) about the new release (same content as above).
1.  Post on all internal chats about the new release.
1.  Move all issues with the "soft-release-blocker" label to the next release milestone.

### Updating .bazelversion and the release documentation page

Submit an internal CL for the following:
1. If this is the newest version of the most recent Bazel LTS release, update https://github.com/bazelbuild/bazel/blob/master/.bazelversion.
    *   Make sure that the CI isn't skipped (no `SKIP_CI` tag) so that we don't miss any errors
2. Update the [support matrix](https://bazel.build/release/index.html#support-matrix) on bazel.build to reflect the latest version (for all LTS releases).

### Updating Google's internal mirror

Follow the instructions [here](http://go/bazel-internal-launch-checklist#updating-googles-internal-mirror) to update the internal mirror.

### Updating the Homebrew recipe

[Homebrew](http://brew.sh/index.html) is a package manager for OS X. This
section assumes that you are on a Mac OS machine with homebrew installed.

To update the `bazel` recipe on Homebrew, you can send a pull request to
https://github.com/Homebrew/homebrew-core/blob/master/Formula/bazel.rb.

Example: https://github.com/Homebrew/homebrew-core/pull/57966

However, usually the Homebrew community takes care of this reasonably
quickly, so feel free to skip this step, if you aren't familiar with it.


### Updating the Chocolatey package

This is done as part of our release pipeline. If there are any issues or questions, reach out to [@petemounce](https://github.com/petemounce), an external contributor.

### Updating the Scoop pakage

As of February 2019, this is done by an external contributor,
[@excitoon](https://github.com/excitoon) on GitHub. [Ping him](http://telegram.me/excitoon) when there's a
new release coming out.


### Updating the Fedora package

This is done by an external contributor, [@vbatts](https://github.com/vbatts) on
GitHub. Ping him when there's a new release coming out.

## Clean up

1. Close and unpin the release tracking issue
1. Close the release blockers milestone
1. Ensure that internal trackers are closed

