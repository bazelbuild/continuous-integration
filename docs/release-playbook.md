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

## Preparing a new release

1.  [Create a release blockers milestone](https://github.com/bazelbuild/bazel/milestones/new) named "X.Y.Z release blockers" (case-sensitive), where we keep track of issues that must be resolved before the release goes out.
1.  [Create a release tracking issue](https://github.com/bazelbuild/bazel/issues/new?assignees=&labels=release%2Cteam-OSS%2CP1%2Ctype%3A+process&template=release.md&title=Release+X.Y+-+%24MONTH+%24YEAR) to keep the community updated about the progress of the release
1.  Create the branch for the release. The branch should always be named `release-X.Y.Z` (the `.Z` part is important). Cherry-pick PRs will be sent against this branch.
    *   The actual creation of the branch can be done via the GitHub UI or via the command line. How we choose the base commit of the branch depends on the type of the release:
    *   For patch releases (`X.Y.Z` where `Z>0`), the base commit should simply be `X.Y.(Z-1)`.
    *   For minor releases (`X.Y.0` where `Y>0`), the base commit should typically be `X.(Y-1).<current max Z>`.
    *   For major releases (`X.0.0`), the base commit is some "healthy" commit on the main branch.
        *   This means that there's an extra step involved in preparing the release -- "cutting" the release branch, so to speak. For this, check the [Bazel@HEAD+Downstream pipeline](https://buildkite.com/bazel/bazel-with-downstream-projects-bazel). The branch cut should happen on a green commit there; if the pipeline is persistently red, work with the Green Team to resolve it first and delay the branch cut as needed.
        *   A first release candidate should immediately be created after the release branch is created. See [create a release candidate](#create-a-release-candidate) below.
1.  After creating the branch, edit the CODEOWNERS file on that branch, replace the entire contents of the file with the line `* @your-github-username` and submit it directly.
    *   This makes sure that all PRs sent against that branch have you as a reviewer.
1.  (For minor release only) Send an email to both bazel-dev@googlegroups.com and bazel-discuss@googlegroups.com announcing the next release.
    *   It should contain the text: `The Bazel X.Y.Z release branch (release-X.Y.Z [link]) is open for business. Please send cherry-pick PRs against this branch if you'd like your change to be in X.Y.Z. Please follow the release tracking issue [link] for updates.`
1.  Meanwhile, begin the [internal approval process](http://go/bazel-internal-launch-checklist), too.
    *   Note that certain steps in the internal approval process require at least preliminary release notes, so those steps should usually wait until the first release candidate is pushed and the release notes have taken vague shape.
    *   Please make sure the Eng. team review status is explicit in release notes/bazel release announcement doc(s), and ensure the Eng. team should approve the release note before creating the launch review issue.
## Maintaining the release

While the release is active, you should make sure to do the following:

*   Monitor [the "potential release blocker" label](https://github.com/bazelbuild/bazel/issues?q=label%3A%22potential+release+blocker%22).
    *   These are issues or PRs that community members have proposed to be fixed/included in the next release. Check each of these and decide whether they should be release blockers; if so, add a comment with the text `@bazel-io fork X.Y.Z` and a copy of the issue will be added to the "X.Y.Z release blockers" milestone; if not, explain why in a comment, and remove the "potential release blocker" label.
*   For cherry-picks,
    *   If a Bazel team member has proposed the fixes, then proceed with the cherry-pick and merge it.
    *   If a Bazel team member authors a commit and a community member asks to cherry-pick, then confirm with the author before cherry-picking the PR to make sure this change is safe to merge.
    *   If a community member author a commit and asks to cherry-pick, then confirm with the reviewer before cherry-picking the PR to make sure that the change is safe to merge.
*   Review any PRs sent to the release branch and merge them as necessary.
    *   Make sure to close any related release blocker issues after merging the PRs; merging PRs into non-main branches does *not* automatically close related issues (see [GitHub docs](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue)).
*   When enough PRs have been cherry-picked and the release is nearing a ready state, create a release candidate (see [below](#create-a-release-candidate)).
    *   When a few days pass and no more release blockers show up, push the candidate as the release. Otherwise, rinse and repeat the steps above.
*   Keep the task list in the release tracking issue updated and check boxes as you follow the release process.
    *   In particular, try and keep the estimated release date updated.

## Create a release candidate

1.  Create a branch (via the GitHub UI or via the command line) named `release-X.Y.ZrcN` at the appropriate commit.
    *   This branch is essentially used as a tag (i.e. no further commits should happen on this branch). All cherry-pick commits should continue to go into the release branch (i.e. `release-X.Y.Z`, without the `rcN` part).

1.  Check BuildKite results at https://buildkite.com/bazel-trusted/bazel-release. You should
    see the `release-X.Y.ZrcN` branch here and a new build running for
    your release. Building Patch Release for old bazel version, create a new build and in 'Option' choose Environment Variable as USE_BAZEL_VERSION=X.Y.(Z-1) i.e previous version.
    See example:
    *   Go to https://buildkite.com/bazel-trusted/bazel-release
    *   Click "New Build", then fill in the fields like this:
        *   Message: Release-4.2.3rc1 (Or any message you like)
        *   Commit: HEAD
        *   Branch: release-4.2.3rc1
        *   Option: USE_BAZEL_VERSION=4.2.2 
1.  Check the postsubmit test run for the release branch to ensure that all
    tests on all platforms pass with the version you're about to release.

    *   Go to https://buildkite.com/bazel/bazel-bazel and find the
        `release-X.Y.ZrcN` branch in the list. A build should
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
    the GitHub issue. Note that there should be a new Bazel Release Announcement document for every major release.
1.  Copy & paste the generated text from the "Generate Announcement" step.
1.  Reorganize the notes per category (C++, Java, etc.).
2.  Assign a comment to "+[pcloudy@google.com](mailto:pcloudy@google.com)" and "+[wyv@google.com](mailto:wyv@google.com)" for initial review. 
3.  Once approved, for each category, add a comment and assign it to the corresponding
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
    1.  there are no more release blocking issues.

## Push a release

1.  **Push the final release (do not cancel midway)** by running the following commands in a Bazel git repo on a Linux machine:

    ```bash
    git fetch origin release-X.Y.ZrcN
    git checkout release-X.Y.ZrcN
    scripts/release/release.sh release
    ```

    **Warning**: If this process is interrupted for any reason, please check the following before running:
      * Both `release-X.Y.ZrcN` and `master` branch are restored to the previous clean state (without addtional release commits).
      * Release tag is deleted locally (`git tag -d X.Y.Z`), otherwise rerun will cause an error that complains the tag already exists.

1.  A CI job is uploading the release artifacts to GitHub. Look for the release
    workflow on https://buildkite.com/bazel-trusted/bazel-release/. Unblock the steps by clicking "Deploy release artifacts". Subsequently you should
    see the updated version in Github.

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
1.  Publish versioned documentation (For major and minor releases only)
    1.  Fetch the git tag for the release: `git fetch --tags`
    1.  Do a checkout to that tag: `git checkout X.Y.Z`
        1. You should see this message:

        ```
        $ git checkout X.Y.Z
        Note: checking out 'X.Y.Z'.

        You are in 'detached HEAD' state. You can look around, make experimental
        changes and commit them, and you can discard any commits you make in this
        state without impacting any branches by performing another checkout.

        If you want to create a new branch to retain commits you create, you may
        do so (now or later) by using -b with the checkout command again. Example:

        git checkout -b <new-branch-name>

        HEAD is now at defd737761 Release X.Y.Z (yyyy-mm-dd)
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
    1.  Ping @fweikert to update the documentation site.

1.  Merge the blog post pull request. (For major and minor releases only)
    1.  Make sure you update the date in your post (and the path) to reflect when
    it is actually published.
    1.  **Note:** The blog sometimes takes time to update the homepage, so use
    the full path to your post to check that it is live.
1.  For major and minor releases, update the release page to replace the generated notes with a link to the blog post. For patch release, update the           release notes without a blog post link - see example: https://github.com/bazelbuild/bazel/releases/tag/5.3.1
1.  Close the release-tracking bug.

### Updating Google's internal mirror

Please ping @meteorcloudy to copy the release binary to their internal mirror.

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

### Push new docker image

Follow the [instructions](../bazel/oci/README.md) to push new docker image for the new release, ping [@meteorcloudy](https://github.com/meteorcloudy) for help.
