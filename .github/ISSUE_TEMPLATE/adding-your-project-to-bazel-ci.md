---
name: Adding your project to Bazel CI
about: For requests to add a project to Bazel CI
title: Request to add new project [PROJECT_NAME]
labels: new-project
assignees: ''

---

Thank you for your interest in adding your project to Bazel CI.

At the moment we're operating at capacity and cannot add new projects except for projects maintained under the bazelbuild GitHub organization and for rules. To request a review for being added to Bazel CI, please follow the instructions below.

- [ ] My project is part of the bazelbuild GitHub organization.
- [ ] My project is a rules set of a GitHub organization other than bazelbuild.
- [ ] I want to test the following project on Bazel CI: [URL_TO_GIT_HUB_PROJECT]
- [ ] I confirm that the project has a `.bazelci/presubmit.yml` file.

# Instructions (you can delete this section from the issue)

Welcome to Bazel CI! We are thrilled that you want to test your project with Bazel.
Please follow these steps to make the on-boarding experience as smooth as possible:

1. Add the URL of your project's GitHub repository to the first line of this issue.
2. Add the name of your project to the issue title.
3. Please read the [introduction to Buildkite](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/README.md) to learn about the basic concepts such as pipelines.
4. Create and commit your presubmit configuration in `<YOUR REPO>/.bazelci/presubmit.yml`. The configuration format is documented [here](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/README.md#configuring-a-pipeline), and you can find several an example [here](https://github.com/bazelbuild/rules_typescript/blob/master/.bazelci/presubmit.yml). No need to get it right on the first try - It's usually a good idea to start with a basic configuration, wait until the pipeline is set up, trigger a build and then iterate on the configuration.
5. The Bazel team will review this issue and create a pipeline on Buildkite.
6. The team will reach out to you and give you instructions on how to set up a GitHub webhook that triggers a CI build for incoming pull requests.
