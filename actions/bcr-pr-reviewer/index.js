const { getInput, setFailed } = require('@actions/core');
const { context, getOctokit } = require("@actions/github");

async function fetchAllModifiedModuleVersions(octokit, owner, repo, prNumber) {
  // Fetch the PR information to get the head SHA
  const prInfo = await octokit.rest.pulls.get({
    owner,
    repo,
    pull_number: prNumber,
  });
  const initialHeadSha = prInfo.data.head.sha;

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

    // Re-fetch PR information to check if new commits were pushed during pagination
    const latestPrInfoForShaCheck = await octokit.rest.pulls.get({
      owner,
      repo,
      pull_number: prNumber,
    });
    if (initialHeadSha !== latestPrInfoForShaCheck.data.head.sha) {
      console.error(`PR #${prNumber} has been updated during file listing. Initial SHA: ${initialHeadSha}, Current SHA: ${latestPrInfoForShaCheck.data.head.sha}. Aborting as the file list may be stale.`);
      return null;
    }

    response.data.forEach(file => {
      const match = file.filename.match(/^modules\/([^\/]+)\/([^\/]+)\//);
      if (match) {
        accumulate.add(`${match[1]}@${match[2]}`);
      }
    });

    page++;
  } while (response.data.length === perPage);

  return accumulate;
}

async function fetchAllModulesWithMetadataChange(octokit, owner, repo, prNumber) {
  // Fetch the PR information to get the head SHA
  const prInfo = await octokit.rest.pulls.get({
    owner,
    repo,
    pull_number: prNumber,
  });
  const initialHeadSha = prInfo.data.head.sha;

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

    // Re-fetch PR information to check if new commits were pushed during pagination
    const latestPrInfoForShaCheck = await octokit.rest.pulls.get({
      owner,
      repo,
      pull_number: prNumber,
    });
    if (initialHeadSha !== latestPrInfoForShaCheck.data.head.sha) {
      console.error(`PR #${prNumber} has been updated during file listing. Initial SHA: ${initialHeadSha}, Current SHA: ${latestPrInfoForShaCheck.data.head.sha}. Aborting as the file list may be stale.`);
      return null;
    }

    response.data.forEach(file => {
      const match = file.filename.match(/^modules\/([^\/]+)\/metadata\.json/);
      if (match) {
        accumulate.add(match[1]);
      }
    });

    page++;
  } while (response.data.length === perPage);

  return accumulate;
}

async function generateMaintainersMap(octokit, owner, repo, modifiedModules, toNotifyOnly) {
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
      for (const maintainer of metadata.maintainers) {
        // Only add maintainers with a github handle set. When `toNotifyOnly`, also exclude those who have set "do_not_notify"
        if (maintainer.github && !(toNotifyOnly && maintainer["do_not_notify"])) {
          hasGithubMaintainer = true;
          if (!maintainersMap.has(maintainer.github)) {
            try {
              // Verify maintainer.github matches maintainer.github_user_id via GitHub API
              const { data: user } = await octokit.rest.users.getByUsername({
                username: maintainer.github,
              });

              if (!user || user.id !== maintainer.github_user_id) {
                console.error(`Maintainer ${maintainer.github} does not match the user ID ${maintainer.github_user_id} or user not found`);
                setFailed(`Maintainer ${maintainer.github} does not match the user ID ${maintainer.github_user_id} or user not found`);
                return;
              }
              maintainersMap.set(maintainer.github, new Set());
            } catch (error) {
              console.error(`Failed to fetch user ID for GitHub username ${maintainer.github}: ${error.message}`);
              setFailed(`Failed to fetch user ID for GitHub username ${maintainer.github}: ${error.message}`);
              return;
            }
          }
          maintainersMap.get(maintainer.github).add(moduleName);
        }
      }

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

  // If there are too many maintainers, it's likely to be an accidental change that will spam too many people.
  if (moduleListToMaintainers.size > 10) {
    console.log(`Skipping notifying maintainers as there are too many maintainers: ${moduleListToMaintainers.size}`);
    // Notify the PR author that too many modules are modified
    const commentBody = `Hello @${prAuthor}, too many modules have been updated in this PR. If this is intended, please consider breaking it down into multiple PRs.`;
    await postComment(octokit, owner, repo, prNumber, commentBody);
    return;
  }

  for (const [modulesList, maintainers] of moduleListToMaintainers.entries()) {
    // Skip notifying the PR author if they are one of the module maintainers
    const maintainersCopy = new Set(maintainers);
    if (maintainersCopy.has(`@${prAuthor}`)) {
      console.log(`Skipping notifying PR author ${prAuthor} from the maintainers list for modules: ${modulesList}`);
      maintainersCopy.delete(`@${prAuthor}`);
    }
    if (maintainersCopy.size === 0) {
      // If all maintainers are skipped, we should notify the BCR maintainers
      await postComment(octokit, owner, repo, prNumber,
        `Hello @bazelbuild/bcr-maintainers, modules (${modulesList}) have been updated in this PR.
        Please review the changes. You can view a diff against the previous version in the "Generate module diff" check.`);
      continue;
    }
    const maintainersList = Array.from(maintainersCopy).join(', ');
    console.log(`Notifying ${maintainersList} for modules: ${modulesList}`);
    const commentBody = `Hello ${maintainersList}, modules you maintain (${modulesList}) have been updated in this PR.
      Please review the changes. You can view a diff against the previous version in the "Generate module diff" check.`;
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

async function checkIfAllModifiedModulesApproved(modifiedModules, maintainersMap, approvers, prAuthor) {
  let allModulesApproved = true;
  const modulesNotApproved = [];

  for (const module of modifiedModules) {
    let moduleApproved = false;
    for (const [maintainer, maintainedModules] of maintainersMap.entries()) {
      if (maintainedModules.has(module)) {
        if (approvers.has(maintainer)) {
          moduleApproved = true;
          console.log(`Module '${module}' has maintainers' approval from '${maintainer}'.`);
          break;
        }
        if (prAuthor === maintainer) {
          moduleApproved = true;
          console.log(`Module '${module}' has maintainers' approval from the PR author '${prAuthor}'.`);
          break;
        }
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

  // Skip if the PR is a draft
  const prInfo = await octokit.rest.pulls.get({
    owner,
    repo,
    pull_number: prNumber,
  });

  if (prInfo.data.draft) {
    console.log('Skipping draft PR');
    return;
  }

  // Fetch modified modules
  const modifiedModuleVersions = await fetchAllModifiedModuleVersions(octokit, owner, repo, prNumber);
  const modifiedModules = new Set(Array.from(modifiedModuleVersions).map(module => module.split('@')[0]));
  console.log(`Modified modules: ${Array.from(modifiedModules).join(', ')}`);
  if (modifiedModules.size === 0) {
    console.log('No modules are modified in this PR');
    return;
  }

  // Figure out maintainers for each modified module
  const [ maintainersMap, modulesWithoutGithubMaintainers ] = await generateMaintainersMap(octokit, owner, repo, modifiedModules, /* toNotifyOnly= */ false);
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
  const prAuthor = prInfo.data.user.login;
  const allModulesApproved = await checkIfAllModifiedModulesApproved(modifiedModules, maintainersMap, approvers, prAuthor);

  // Re-fetch PR information to check if new commits were pushed since analysis started
  const initialHeadSha = prInfo.data.head.sha;
  const latestPrInfoForShaCheck = await octokit.rest.pulls.get({
    owner,
    repo,
    pull_number: prNumber,
  });
  const currentHeadSha = latestPrInfoForShaCheck.data.head.sha;

  if (initialHeadSha !== currentHeadSha) {
    console.log(`PR #${prNumber} has been updated since the review process began. Initial SHA: ${initialHeadSha}, Current SHA: ${currentHeadSha}. Aborting approval/merge actions as the analysis may be stale.`);
    return; // Exit reviewPR for this PR to prevent actions on stale data
  }

  const { data } = await octokit.rest.users.getAuthenticated();
  const myLogin = data.login;

  // Approve the PR if not previously approved and all modules are approved
  if (allModulesApproved) {
    if (!approvers.has(myLogin)) {
      console.log('Approving the PR');
      await octokit.rest.pulls.createReview({
        owner,
        repo,
        pull_number: prNumber,
        event: 'APPROVE',
        body: 'Hello @bazelbuild/bcr-maintainers, all modules in this PR have been approved by their maintainers. This PR will be merged if all presubmit checks pass.',
      });
    }

    // Try to merge the PR
    try {
      await octokit.rest.pulls.merge({
        owner,
        repo,
        pull_number: prNumber,
        merge_method: 'squash',
      });

      // Add auto-merged label
      await octokit.rest.issues.addLabels({
        owner,
        repo,
        issue_number: prNumber,
        labels: ['auto-merged'],
      });

      console.log(`PR ${prNumber} merged successfully`);
    } catch (error) {
      console.error('Failed to merge PR:', error.message);
      console.error('This PR is not mergeable probably due to failed presubmit checks.');
    }
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
  const modifiedModuleVersions = await fetchAllModifiedModuleVersions(octokit, owner, repo, prNumber);
  const modifiedModules = new Set(Array.from(modifiedModuleVersions).map(module => module.split('@')[0]));
  console.log(`Modified modules: ${Array.from(modifiedModules).join(', ')}`);

  // Figure out maintainers for each modified module
  const [ maintainersMap, modulesWithoutGithubMaintainers ] = await generateMaintainersMap(octokit, owner, repo, modifiedModules, /* toNotifyOnly= */ true);

  // Notify maintainers for modules with module maintainers
  await notifyMaintainers(octokit, owner, repo, prNumber, maintainersMap);

  // Notify BCR maintainers for modules without module maintainers
  if (modulesWithoutGithubMaintainers.size > 0) {
    const modulesList = Array.from(modulesWithoutGithubMaintainers).join(', ');
    console.log(`Notifying @bazelbuild/bcr-maintainers for modules: ${modulesList}`);
    await postComment(octokit, owner, repo, prNumber,
      `Hello @bazelbuild/bcr-maintainers, modules without existing maintainers (${modulesList}) have been updated in this PR.
      Please review the changes. You can view a diff against the previous version in the "Generate module diff" check.`);
  }

  // Notify BCR maintainers for modules with only metadata.json changes
  const allModulesWithMetadataChange = await fetchAllModulesWithMetadataChange(octokit, owner, repo, prNumber);
  const modulesWithOnlyMetadataChanges = new Set(
    [...allModulesWithMetadataChange].filter(module => !modifiedModules.has(module))
  );

  if (modulesWithOnlyMetadataChanges.size > 0) {
    const modulesList = Array.from(modulesWithOnlyMetadataChanges).join(', ');
    console.log(`Notifying @bazelbuild/bcr-maintainers for modules with only metadata.json changes: ${modulesList}`);
    await postComment(octokit, owner, repo, prNumber,
      `Hello @bazelbuild/bcr-maintainers, modules with only metadata.json changes (${modulesList}) have been updated in this PR.
      Please review the changes.`);
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

const SKIP_CHECK_TRIGGER = "@bazel-io skip_check ";

async function runSkipCheck(octokit) {
  const payload = context.payload;
  if (!payload.comment.body.startsWith(SKIP_CHECK_TRIGGER)) {
    return;
  }
  const check = payload.comment.body.slice(SKIP_CHECK_TRIGGER.length);
  const owner = payload.repository.owner.login;
  const repo = payload.repository.name;
  if (check.trim() == "unstable_url") {
    await octokit.rest.issues.addLabels({
      owner,
      repo,
      issue_number: payload.issue.number,
      labels: ["skip-url-stability-check"],
    });
    await octokit.rest.reactions.createForIssueComment({
      owner,
      repo,
      comment_id: payload.comment.id,
      content: '+1',
    });
  } else if (check.trim() == "compatibility_level") {
    await octokit.rest.issues.addLabels({
      owner,
      repo,
      issue_number: payload.issue.number,
      labels: ["skip-compatibility-level-check"],
    });
    await octokit.rest.reactions.createForIssueComment({
      owner,
      repo,
      comment_id: payload.comment.id,
      content: '+1',
    });
  } else if (check.trim() == "incompatible_flags") {
    await octokit.rest.issues.addLabels({
      owner,
      repo,
      issue_number: payload.issue.number,
      labels: ["skip-incompatible-flags-test"],
    });
    await octokit.rest.reactions.createForIssueComment({
      owner,
      repo,
      comment_id: payload.comment.id,
      content: '+1',
    });
  } else {
    await octokit.rest.reactions.createForIssueComment({
      owner,
      repo,
      comment_id: payload.comment.id,
      content: 'confused',
    });
    console.error(`unknown check: ${check}`);
    setFailed(`unknown check: ${check}`);
  }
}

async function runDiffModule(octokit) {
  const prNumber = context.issue.number;
  if (!prNumber) {
    console.log('Could not get pull request number from context, exiting');
    return;
  }
  console.log(`Diffing modules in PR #${prNumber}`);

  const { owner, repo } = context.repo;

  // Fetch modified modules
  const modifiedModuleVersions = await fetchAllModifiedModuleVersions(octokit, owner, repo, prNumber);
  console.log(`Modified modules: ${Array.from(modifiedModuleVersions).join(', ')}`);

  // Use group if more than one module are modified
  const groupStart = modifiedModuleVersions.size === 1 ? "" : "::group::";
  const groupEnd = modifiedModuleVersions.size === 1 ? "" : "::endgroup::";

  for (const moduleVersion of modifiedModuleVersions) {
    const [moduleName, versionName] = moduleVersion.split('@');
    try {
      const { data: metadataContent } = await octokit.rest.repos.getContent({
        owner,
        repo,
        path: `modules/${moduleName}/metadata.json`,
        ref: `refs/pull/${prNumber}/head`,
      });
      const metadata = JSON.parse(Buffer.from(metadataContent.content, 'base64').toString('utf-8'));

      // Assuming metadata.versions is sorted in ascending order, otherwise bcr_validation.py checks will fail anyway.
      let versionIndex = metadata.versions.findIndex(version => version === versionName);

      if (versionIndex === -1) {
        console.error(`Version ${versionName} not found in metadata.json for module ${moduleName}`);
        console.log(`Metadata content for module ${moduleName}@${versionName}: ${JSON.stringify(metadata, null, 2)}`);
        setFailed(`Failed to generate diff for module ${moduleName}@${versionName}`);
        return;
      }

      if (versionIndex === 0) {
        console.log(`No previous version to diff for module ${moduleName}@${versionName}`);
        continue;
      }

      const previousVersion = metadata.versions[versionIndex - 1];
      console.log(`${groupStart}Generating diff for module ${moduleName}@${versionName} against version ${previousVersion}`);

      const diffArgs = ['--color=always', '-urN', `modules/${moduleName}/${previousVersion}`, `modules/${moduleName}/${versionName}`];
      console.log(`Running command: diff ${diffArgs.join(' ')}`);
      const { spawnSync } = require('child_process');

      try {
        const result = spawnSync('diff', diffArgs, {
          encoding: 'utf8',
          stdio: ['inherit', 'pipe', 'pipe']
        });

        if (result.status === 0) {
          console.log(`No differences found!`);
        } else if (result.status === 1) {
          // diff command returns 1 when differences are found
          console.log(result.stdout);
          console.log(result.stderr);
        } else {
          setFailed(`Failed to generate diff for module ${moduleName}@${versionName}`);
          console.error(result.stderr);
          throw new Error(`Diff command failed with status ${result.status}`);
        }
      } catch (error) {
        console.error(`Error executing diff: ${error.message}`);
        throw error;
      }

      console.log(`${groupEnd}`);
    } catch (error) {
      if (error.status === 404) {
        console.log(`Module ${moduleName} does not have a metadata.json file on the PR branch.`);
      } else {
        console.error(`Error processing module ${moduleName}: ${error}`);
        setFailed(`Failed to generate diff for module ${moduleName}@${versionName}`);
      }
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
  } else if (action_type === "skip_check") {
    await runSkipCheck(octokit);
  } else if (action_type === "diff_module") {
    await runDiffModule(octokit);
  } else {
    console.log(`Unknown action type: ${action_type}`);
  }
}

run().catch(err => {
  console.error(err);
  setFailed(err.message);
});
