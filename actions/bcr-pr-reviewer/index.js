const { getInput, setFailed } = require('@actions/core');
const { context, getOctokit } = require("@actions/github");

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

async function notifyMaintainers(octokit, owner, repo, prNumber, maintainersMap) {
  // For the list of maintainers who maintain the same set of modules, we want to group them together
  const moduleListToMaintainers = new Map(); // Map: Serialized Module List -> Maintainers

  // Populate moduleListToMaintainers based on maintainersMap
  for (const [maintainer, modules] of maintainersMap.entries()) {
    const modulesList = Array.from(modules).sort().join(', '); // Serialize module list
    if (!moduleListToMaintainers.has(modulesList)) {
      moduleListToMaintainers.set(modulesList, new Set());
    }
    moduleListToMaintainers.get(modulesList).add(`@${maintainer}`);
  }

  // Notify maintainers based on grouped module lists
  const prAuthor = context.payload.pull_request.user.login;
  for (const [modulesList, maintainers] of moduleListToMaintainers.entries()) {
    // Skip notifying the PR author if they are one of the module maintainers
    const maintainersCopy = new Set(maintainers);
    if (maintainersCopy.has(`@${prAuthor}`)) {
      console.log(`Skipping notifying PR author ${prAuthor} from the maintainers list for modules: ${modulesList}`);
      maintainersCopy.delete(`@${prAuthor}`);
    }
    if (maintainersCopy.size === 0) {
      continue;
    }
    const maintainersList = Array.from(maintainersCopy).join(', ');
    console.log(`Notifying ${maintainersList} for modules: ${modulesList}`);
    const commentBody = `Hello ${maintainersList}, modules you maintain (${modulesList}) have been updated in this PR. Please review the changes.`;
    await postComment(octokit, owner, repo, prNumber, commentBody);
  }
}

async function postComment(octokit, owner, repo, prNumber, body) {
  // Check if the same comment already exists for the PR in the past two weeks
  const existingComments = await octokit.rest.issues.listComments({
    owner,
    repo,
    issue_number: prNumber,
    since: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(), // Two weeks ago
  });

  const commentExists = existingComments.data.some(comment => comment.body === body);
  if (commentExists) {
    console.log('Skipping comment as it\'s already posted for the PR within the past two weeks.');
    return;
  }

  const comment = {
    owner,
    repo,
    issue_number: prNumber,
    body,
  };
  await octokit.rest.issues.createComment(comment).catch(error => {
    console.error(`Failed to post comment: ${error}`);
    setFailed(`Failed to notify maintainers: ${error}`);
  });
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

async function runNotifier(octokit) {
  const prNumber = context.issue.number;
  if (!prNumber) {
    console.log('Could not get pull request number from context, exiting');
    return;
  }
  console.log(`Processing PR #${prNumber}`);

  const { owner, repo } = context.repo;

  // Fetch modified modules
  const modifiedModules = await fetchAllModifiedModules(octokit, owner, repo, prNumber);
  console.log(`Modified modules: ${Array.from(modifiedModules).join(', ')}`);

  // Figure out maintainers for each modified module
  const [ maintainersMap, modulesWithoutGithubMaintainers ] = await generateMaintainersMap(octokit, owner, repo, modifiedModules);

  // Notify maintainers for modules with module maintainers
  await notifyMaintainers(octokit, owner, repo, prNumber, maintainersMap);

  // Notify BCR maintainers for modules without module maintainers
  if (modulesWithoutGithubMaintainers.size > 0) {
    const modulesList = Array.from(modulesWithoutGithubMaintainers).join(', ');
    console.log(`Notifying @bazelbuild/bcr-maintainers for modules: ${modulesList}`);
    await postComment(octokit, owner, repo, prNumber, `Hello @bazelbuild/bcr-maintainers, modules without existing maintainers (${modulesList}) have been updated in this PR. Please review the changes.`);
  }
}

async function waitForDismissApprovalsWorkflow(octokit, owner, repo) {
  // List all workflow of this repository
  const workflows = await octokit.rest.actions.listRepoWorkflows({
    owner,
    repo,
  });

  // Find the workflow file for .github/workflows/dismiss_approvals.yml
  const dismissApprovalsWorkflow = workflows.data.workflows.find(workflow => workflow.path === '.github/workflows/dismiss_approvals.yml');
  if (!dismissApprovalsWorkflow) {
    setFailed('The dismiss_approvals workflow is not found');
    return false;
  }
  console.log(`Found dismiss_approvals workflow: ${dismissApprovalsWorkflow.id}`);

  // Wait until all runs of the dismiss_approvals workflow are completed
  // https://docs.github.com/en/rest/actions/workflow-runs?apiVersion=2022-11-28#list-workflow-runs-for-a-repository
  shouldWaitStatues = ['queued', 'in_progress', 'requested', 'pending', 'waiting'];
  let response;
  while (true) {
    total_count = 0;
    for (const status of shouldWaitStatues) {
      response = await octokit.rest.actions.listWorkflowRuns({
        owner,
        repo,
        workflow_id: dismissApprovalsWorkflow.id,
        status: status,
      });

      for (const run of response.data.workflow_runs) {
        console.log(`Dismiss approvals workflow run #${run.run_number} is ${run.status}`);
      }

      total_count += response.data.total_count;
    }

    if (total_count > 0) {
      console.log('Waiting 5s for dismiss approvals workflow runs to complete');
      await new Promise(resolve => setTimeout(resolve, 5000));
    } else {
      console.log('All dismiss approvals workflow runs are completed');
      break;
    }
  }
  return true;
}

async function runPrReviewer(octokit) {
  const { owner, repo } = context.repo;

  // Wait until all runs of the dismiss_approvals workflow are completed
  if (!await waitForDismissApprovalsWorkflow(octokit, owner, repo)) {
    return;
  }

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

async function runDismissApproval(octokit) {
  const prNumber = context.issue.number;
  if (!prNumber) {
    console.log('Could not get pull request number from context, exiting');
    return;
  }
  console.log(`Processing PR #${prNumber}`);

  const reviews = await octokit.rest.pulls.listReviews({
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: prNumber,
  });

  for (const review of reviews.data) {
    if (review.state === 'APPROVED') {
      console.log(`Dismiss approval from ${review.user.login}`);
      await octokit.rest.pulls.dismissReview({
        owner: context.repo.owner,
        repo: context.repo.repo,
        pull_number: prNumber,
        review_id: review.id,
        message: 'Require module maintainers\' approval for newly pushed changes.',
      });
    }
  }
}

async function run() {
  const action_type = getInput("action-type");
  const token = getInput("token");
  const octokit = getOctokit(token);

  if (action_type === "notify_maintainers") {
    await runNotifier(octokit);
  } else if (action_type === "review_prs") {
    await runPrReviewer(octokit);
  } else if (action_type === "dismiss_approvals") {
    await runDismissApproval(octokit);
  } else {
    console.log(`Unknown action type: ${action_type}`);
  }
}

run().catch(err => {
  console.error(err);
  setFailed(err.message);
});
