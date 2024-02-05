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
      console.error(`Error processing module ${moduleName}: ${error}`);
      setFailed(`Failed to notify maintainers for module ${moduleName}`);
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
  for (const [modulesList, maintainers] of moduleListToMaintainers.entries()) {
    const maintainersList = Array.from(maintainers).join(', ');
    console.log(`Notifying ${maintainersList} for modules: ${modulesList}`);
    const commentBody = `Hello ${maintainersList}, modules you maintain (${modulesList}) have been updated in this PR. Please review the changes.`;
    await postComment(octokit, owner, repo, prNumber, commentBody);
  }
}

async function postComment(octokit, owner, repo, prNumber, body) {
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

async function run() {
  const token = getInput("token");
  const octokit = getOctokit(token);

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
    await postComment(octokit, owner, repo, prNumber, `Hello @bazelbuild/bcr-maintainers, modules without specific maintainers (${modulesList}) have been updated in this PR. Please review the changes.`);
  }
}

run().catch(err => {
  console.error(err);
  setFailed(err.message);
});
