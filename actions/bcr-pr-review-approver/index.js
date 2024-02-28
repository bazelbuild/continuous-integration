const { getInput, setFailed } = require('@actions/core');
const { context, getOctokit } = require("@actions/github");

// Keep this function in sync with the one in actions/bcr-pr-review-notifier/index.js
async function fetchAllModifiedModules(octokit, owner, repo, prNumber) {
  let page = 1;
  const perPage = 100; // GitHub's max per_page value
  let accumulate = new Set();
  let response;

  do {
    response = await octokit.rest.pulls.listFiles({
      owner,
      repo,
      pull_number: prNumber,
      per_page: perPage,
      page,
    });

    response.data.forEach(file => {
      const match = file.filename.match(/^modules\/([^\/]+)\//);
      if (match) {
        accumulate.add(match[1]);
      }
    });

    page++;
  } while (response.data.length === perPage);

  return accumulate;
}

// Keep this function in sync with the one in actions/bcr-pr-review-notifier/index.js
async function generateMaintainersMap(octokit, owner, repo, modifiedModules) {
  const maintainersMap = new Map(); // Map: maintainer GitHub username -> Set of module they maintain
  const modulesWithoutGithubMaintainers = new Set(); // Set of module names without module maintainers
  for (const moduleName of modifiedModules) {
    console.log(`Fetching metadata for module: ${moduleName}`);
    try {
      const { data: metadataContent } = await octokit.rest.repos.getContent({
        owner,
        repo,
        path: `modules/${moduleName}/metadata.json`,
        ref: 'main',
      });

      const metadata = JSON.parse(Buffer.from(metadataContent.content, 'base64').toString('utf-8'));
      let hasGithubMaintainer = false;
      metadata.maintainers.forEach(maintainer => {
        if (maintainer.github) { // Check if the github field is specified
          hasGithubMaintainer = true;
          if (!maintainersMap.has(maintainer.github)) {
            maintainersMap.set(maintainer.github, new Set());
          }
          maintainersMap.get(maintainer.github).add(moduleName);
        }
      });

      if (!hasGithubMaintainer) {
        modulesWithoutGithubMaintainers.add(moduleName);
      }
    } catch (error) {
      if (error.status === 404) {
        console.log(`Module ${moduleName} does not have a metadata.json file on the main branch.`);
        modulesWithoutGithubMaintainers.add(moduleName);
      } else {
        console.error(`Error processing module ${moduleName}: ${error}`);
        setFailed(`Failed to notify maintainers for module ${moduleName}`);
      }
    }
  }
  return [maintainersMap, modulesWithoutGithubMaintainers];
}

async function getPrApprovers(octokit, owner, repo, prNumber) {
  // Get the commits for the PR
  const commits = await octokit.rest.pulls.listCommits({
    owner,
    repo,
    pull_number: prNumber,
  });

  // Filter out the merge commits whose parents length is larger than 1
  const nonMergeCommits = commits.data.filter(commit => commit.parents.length === 1);

  // Get the latest commit submitted time
  const latestCommit = nonMergeCommits[nonMergeCommits.length - 1];
  const latestCommitTime = new Date(latestCommit.commit.author.date);
  console.log(`Latest commit: ${latestCommit.sha}`);
  console.log(`Latest commit time: ${latestCommitTime}`);

  // Get review events for the PR
  const reviewEvents = await octokit.rest.pulls.listReviews({
    owner,
    repo,
    pull_number: prNumber,
  });

  // For each reviewer, collect their latest review that are newer than the latest non-merge commit
  // Key: reviewer, Value: review
  const latestReviews = new Map();
  reviewEvents.data.forEach(review => {
    if (new Date(review.submitted_at) < latestCommitTime) {
      return;
    }

    const reviewer = review.user.login;

    if (!latestReviews.has(reviewer)) {
      latestReviews.set(reviewer, review);
      return;
    }

    existingSubmittedAt = new Date(latestReviews.get(reviewer).submitted_at);
    submittedAt = new Date(review.submitted_at);
    if (submittedAt > existingSubmittedAt) {
      latestReviews.set(reviewer, review);
    }
  });

  // Print out the latest valid reviews and collect approvers
  console.log(`Latest Reviews:`);
  const approvers = new Set();
  latestReviews.forEach(review => {
    console.log(`- Reviewer: ${review.user.login}, State: ${review.state}, Submitted At: ${review.submitted_at}`);
    if (review.state === 'APPROVED') {
      approvers.add(review.user.login);
    }
  });

  // Print out the approvers
  console.log(`Approvers: ${Array.from(approvers).join(', ')}`);

  return approvers;
}

async function checkIfAllModifiedModulesApproved(modifiedModules, maintainersMap, approvers) {
  let allModulesApproved = true;
  const modulesNotApproved = [];

  for (const module of modifiedModules) {
    let moduleApproved = false;
    for (const [maintainer, maintainedModules] of maintainersMap.entries()) {
      if (maintainedModules.has(module) && approvers.has(maintainer)) {
        moduleApproved = true;
        console.log(`Module '${module}' has maintainers' approval from '${maintainer}'.`);
        break;
      }
    }
    if (!moduleApproved) {
      allModulesApproved = false;
      modulesNotApproved.push(module);
      console.log(`Module '${module}' does not have maintainers' approval.`);
    }
  }


  if (!allModulesApproved) {
    console.log(`Cannot auto-merge this PR, the following modules do not have maintainers' approval: ${modulesNotApproved.join(', ')}`);
  } else {
    console.log('All modified modules have maintainers\' approval');
  }

  return allModulesApproved;
}

async function reviewPR(octokit, owner, repo, prNumber) {

  console.log('\n');
  console.log(`Processing PR #${prNumber}`);

  // Fetch modified modules
  const modifiedModules = await fetchAllModifiedModules(octokit, owner, repo, prNumber);
  console.log(`Modified modules: ${Array.from(modifiedModules).join(', ')}`);
  if (modifiedModules.size === 0) {
    console.log('No modules are modified in this PR');
    return;
  }

  // Figure out maintainers for each modified module
  const [ maintainersMap, modulesWithoutGithubMaintainers ] = await generateMaintainersMap(octokit, owner, repo, modifiedModules);
  console.log('Maintainers Map:');
  for (const [maintainer, maintainedModules] of maintainersMap.entries()) {
    console.log(`- Maintainer: ${maintainer}, Modules: ${Array.from(maintainedModules).join(', ')}`);
  }

  // If modulesWithoutGithubMaintainers is not empty, then return
  if (modulesWithoutGithubMaintainers.size > 0) {
    console.log(`Cannot auto-merge this PR with maintainers approval because the following modules do not have maintainers with GitHub usernames: ${Array.from(modulesWithoutGithubMaintainers).join(', ')}`);
    return;
  }

  // Get the approvers for the PR
  const approvers = await getPrApprovers(octokit, owner, repo, prNumber);

  // Verify if all modified modules have at least one maintainer's approval
  const allModulesApproved = await checkIfAllModifiedModulesApproved(modifiedModules, maintainersMap, approvers);

  const myLogin = context.actor;

  // Approve the PR if not previously approved and all modules are approved
  if (allModulesApproved) {
    if (!approvers.has(myLogin)) {
      console.log('Approving the PR');
      await octokit.rest.pulls.createReview({
        owner,
        repo,
        pull_number: prNumber,
        event: 'APPROVE',
        body: 'Hello @bazelbuild/bcr-maintainers, all modules in this PR have been approved by their maintainers. Please take a final look to merge this PR.',
      });
    }

    // TODO: Enable the following when it's safe to do so.
    // // Try to merge the PR
    // try {
    //   await octokit.rest.pulls.merge({
    //     owner,
    //     repo,
    //     pull_number: prNumber,
    //   });
    // } catch (error) {
    //   console.error('Failed to merge PR:', error.message);
    //   console.error('This PR is not mergeable probably due to failed presubmits.');
    // }
  }

  // Discard previous approvals if not all modules are approved
  if (!allModulesApproved && approvers.has(myLogin)) {
    console.log('Discarding previous approval');
    await octokit.rest.pulls.createReview({
      owner,
      repo,
      pull_number: prNumber,
      event: 'REQUEST_CHANGES',
      body: 'Require module maintainers\' approval.',
    });
  }
}

async function run() {
  const token = getInput("token");
  const octokit = getOctokit(token);
  const { owner, repo } = context.repo;

  // Get all open PRs from the repo
  const prs = await octokit.rest.pulls.list({
    owner,
    repo,
    state: 'open',
  });

  // Review each PR
  for (const pr of prs.data) {
    await reviewPR(octokit, owner, repo, pr.number);
  }
}

run().catch(err => {
  console.error(err);
  setFailed(err.message);
});
