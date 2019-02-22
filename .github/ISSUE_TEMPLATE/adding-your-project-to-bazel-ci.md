---
name: Adding your project to Bazel CI
about: For requests to add a project to Bazel CI
title: Request to add new project [PROJECT_NAME]
labels: new-project
assignees: ''

---

- I want to test the following project on Bazel CI: [URL_TO_GIT_HUB_PROJECT]
- I confirm that the project has a `.bazelci/presubmit.yml` file.

# Instructions (you can delete this section from the issue)

Welcome to Bazel CI! We are thrilled that you want to test your project with Bazel.
Please follow these steps to make the on-boarding experience as smooth as possible:

1. Add the URL of your project's GitHub repository to the first line of this issue.
2. Add the name of your project to the issue title.
3. Please read the [introduction to Buildkite](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/README.md) to learn about the basic concepts such as pipelines.
4. Create and commit your presubmit configuration in `<YOUR REPO>/.bazelci/presubmit.yml`. The configuration format is documented [here](https://github.com/bazelbuild/continuous-integration/blob/master/buildkite/README.md#configuring-a-pipeline), and you can find several an examples [here](https://github.com/bazelbuild/rules_typescript/blob/master/.bazelci/presubmit.yml). No need to get it right on the first try - It's usually a good idea to start with a basic configuration, start a build and then iterate on the configuration.
5. The Bazel team will review this issue and create a pipeline on Buildkite.
6. The team will reach out to you and give you instructions on how to set up a GitHub webhook that triggers a CI build for incoming pull requests.
