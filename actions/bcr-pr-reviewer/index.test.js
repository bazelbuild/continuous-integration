const test = require('node:test');
const assert = require('node:assert/strict');
const { getPrApprovers, moduleVersionDir, reviewPR, runPrReviewer } = require('./index.js');

function fakeOctokit({ commits, reviews }) {
  return {
    paginate: async (fn, params) => {
      if (fn === fakeOctokit.pullsListCommitsMarker) return commits;
      if (fn === fakeOctokit.pullsListReviewsMarker) return reviews;
      throw new Error('unexpected paginate call');
    },
    rest: {
      pulls: {
        listCommits: fakeOctokit.pullsListCommitsMarker,
        listReviews: fakeOctokit.pullsListReviewsMarker,
      },
    },
  };
}
fakeOctokit.pullsListCommitsMarker = Symbol('listCommits');
fakeOctokit.pullsListReviewsMarker = Symbol('listReviews');

test('getPrApprovers: an approval submitted against an earlier commit does not count once a merge commit changes the PR head', async () => {
  // C1 gets approved by a maintainer, then C2 (a merge commit -- 2 parents) is
  // pushed afterwards and becomes the PR's real HEAD. The maintainer's review
  // was submitted against C1 and never saw C2's content.
  const commits = [
    { sha: 'C1', parents: [{ sha: 'base' }], commit: { author: { date: '2026-08-06T00:00:00Z' } } },
    { sha: 'C2-merge', parents: [{ sha: 'C1' }, { sha: 'other' }], commit: { author: { date: '2026-08-06T00:20:00Z' } } },
  ];
  const reviews = [
    { user: { login: 'maintainer' }, state: 'APPROVED', commit_id: 'C1', submitted_at: '2026-08-06T00:10:00Z' },
  ];

  const approvers = await getPrApprovers(fakeOctokit({ commits, reviews }), 'owner', 'repo', 1);

  assert.equal(approvers.has('maintainer'), false, 'a review submitted against a commit that is no longer the head must not count');
});

test('getPrApprovers: a stale approval stays rejected even when the new head commit is backdated (author.date is attacker-controlled)', async () => {
  // The attacker gets C1 approved, then pushes C2-evil as the new head but forges
  // its author.date to BEFORE the approval (GIT_AUTHOR_DATE). A timestamp cutoff
  // (review.submitted_at >= head author.date) would wrongly treat the stale C1
  // approval as fresh for C2-evil. Matching on the review's commit_id is immune
  // to the forged date.
  const commits = [
    { sha: 'C1', parents: [{ sha: 'base' }], commit: { author: { date: '2026-08-06T10:00:00Z' } } },
    // Pushed after the approval, but its author date is forged into the past.
    { sha: 'C2-evil', parents: [{ sha: 'C1' }], commit: { author: { date: '2020-01-01T00:00:00Z' } } },
  ];
  const reviews = [
    { user: { login: 'maintainer' }, state: 'APPROVED', commit_id: 'C1', submitted_at: '2026-08-06T10:05:00Z' },
  ];

  const approvers = await getPrApprovers(fakeOctokit({ commits, reviews }), 'owner', 'repo', 1);

  assert.equal(approvers.has('maintainer'), false, 'a backdated head commit must not let a stale approval count as fresh');
});

test('getPrApprovers: an approval submitted against the current head merge commit still counts', async () => {
  const commits = [
    { sha: 'C1', parents: [{ sha: 'base' }], commit: { author: { date: '2026-08-06T00:00:00Z' } } },
    { sha: 'C2-merge', parents: [{ sha: 'C1' }, { sha: 'other' }], commit: { author: { date: '2026-08-06T00:20:00Z' } } },
  ];
  const reviews = [
    { user: { login: 'maintainer' }, state: 'APPROVED', commit_id: 'C2-merge', submitted_at: '2026-08-06T00:30:00Z' },
  ];

  const approvers = await getPrApprovers(fakeOctokit({ commits, reviews }), 'owner', 'repo', 1);

  assert.equal(approvers.has('maintainer'), true, 'a review submitted against the current head should count');
});

test('getPrApprovers: the latest review state against the head wins (a later request-changes overrides an earlier approval)', async () => {
  const commits = [
    { sha: 'C1', parents: [{ sha: 'base' }], commit: { author: { date: '2026-08-06T00:00:00Z' } } },
  ];
  const reviews = [
    { user: { login: 'maintainer' }, state: 'APPROVED', commit_id: 'C1', submitted_at: '2026-08-06T00:05:00Z' },
    { user: { login: 'maintainer' }, state: 'CHANGES_REQUESTED', commit_id: 'C1', submitted_at: '2026-08-06T00:09:00Z' },
  ];

  const approvers = await getPrApprovers(fakeOctokit({ commits, reviews }), 'owner', 'repo', 1);

  assert.equal(approvers.has('maintainer'), false, 'a newer non-approving review against the same head must override the earlier approval');
});

test('getPrApprovers: works normally when a single-commit PR is approved at head', async () => {
  const commits = [
    { sha: 'C1', parents: [{ sha: 'base' }], commit: { author: { date: '2026-08-06T00:00:00Z' } } },
  ];
  const reviews = [
    { user: { login: 'maintainer' }, state: 'APPROVED', commit_id: 'C1', submitted_at: '2026-08-06T00:05:00Z' },
  ];

  const approvers = await getPrApprovers(fakeOctokit({ commits, reviews }), 'owner', 'repo', 1);

  assert.equal(approvers.has('maintainer'), true);
});

test('moduleVersionDir: a normal version resolves to its directory under the module', () => {
  assert.equal(moduleVersionDir('rules_cc', '1.2.3'), 'modules/rules_cc/1.2.3');
});

test('moduleVersionDir: versions with dots and dashes are not treated as traversal', () => {
  // Only a "../" path segment escapes; dots inside a version are ordinary characters.
  assert.equal(moduleVersionDir('rules_cc', '0.9.0-rc.1..2'), 'modules/rules_cc/0.9.0-rc.1..2');
  assert.equal(moduleVersionDir('rules_cc', '1.0.0+build.5'), 'modules/rules_cc/1.0.0+build.5');
});

test('moduleVersionDir: a version escaping the module directory is rejected', () => {
  // metadata.json is read from the PR head, so these are attacker-supplied values.
  assert.equal(moduleVersionDir('rules_cc', '../../..'), null);
  assert.equal(moduleVersionDir('rules_cc', '..'), null);
  assert.equal(moduleVersionDir('rules_cc', '../other_module/1.0.0'), null);
  assert.equal(moduleVersionDir('rules_cc', 'nested/1.0.0'), null);
  assert.equal(moduleVersionDir('rules_cc', '/etc'), null);
  assert.equal(moduleVersionDir('rules_cc', '/etc/passwd'), null);
});

test('moduleVersionDir: a version naming the module directory itself is rejected', () => {
  assert.equal(moduleVersionDir('rules_cc', '.'), null);
  assert.equal(moduleVersionDir('rules_cc', ''), null);
});

// A fake octokit for reviewPR/runPrReviewer on a PR touching one module
// (`foo`) maintained by `alice`, who has approved the PR at its head commit.
function fakeReviewOctokit({ prAuthor, prs = [], failingPrs = new Set() }) {
  const calls = { createReview: [], createComment: [], requestReviewers: [], merge: [] };
  const listCommits = Symbol('listCommits');
  // getPrApprovers paginates listReviews while requestBcrMaintainers calls it
  // directly, so it must be both a paginate marker and callable.
  const listReviews = async () => ({ data: [] });
  const listComments = Symbol('listComments');
  const listPulls = Symbol('listPulls');
  const prData = (pull_number) => ({
    number: pull_number,
    draft: false,
    changed_files: 1,
    user: { login: prAuthor, id: 42 },
    head: { sha: 'HEAD' },
    labels: [{ name: 'presubmit-auto-run' }],
    requested_reviewers: [],
    requested_teams: [],
  });
  const octokit = {
    calls,
    paginate: async (fn, params) => {
      if (fn === listCommits) return [{ sha: 'HEAD' }];
      if (fn === listReviews) {
        return [{ user: { login: 'alice' }, state: 'APPROVED', commit_id: 'HEAD', submitted_at: '2026-09-30T00:00:00Z' }];
      }
      if (fn === listComments) return [];
      if (fn === listPulls) return prs;
      throw new Error('unexpected paginate call');
    },
    request: async (route, params) => {
      assert.equal(route, 'GET /user/{account_id}');
      return { data: { login: 'alice' } };
    },
    rest: {
      pulls: {
        get: async ({ pull_number }) => {
          if (failingPrs.has(pull_number)) throw new Error(`boom #${pull_number}`);
          return { data: prData(pull_number) };
        },
        list: listPulls,
        listCommits,
        listReviews,
        listFiles: async () => ({ data: [{ filename: 'modules/foo/1.0.0/MODULE.bazel' }] }),
        createReview: async (params) => {
          calls.createReview.push(params);
          if (prAuthor === 'bazel-io') {
            const error = new Error('Unprocessable Entity: "Can not approve your own pull request"');
            error.status = 422;
            throw error;
          }
        },
        requestReviewers: async (params) => { calls.requestReviewers.push(params); },
        merge: async (params) => { calls.merge.push(params); },
      },
      issues: {
        listComments,
        createComment: async (params) => { calls.createComment.push(params); },
        addLabels: async () => {},
      },
      repos: {
        getContent: async ({ path }) => {
          assert.equal(path, 'modules/foo/metadata.json');
          const metadata = { maintainers: [{ github: 'alice', github_user_id: 1 }], versions: ['1.0.0'] };
          return { data: { content: Buffer.from(JSON.stringify(metadata)).toString('base64') } };
        },
      },
      users: {
        getAuthenticated: async () => ({ data: { login: 'bazel-io' } }),
      },
      actions: {
        listRepoWorkflows: async () => ({ data: { workflows: [{ id: 7, path: '.github/workflows/dismiss_approvals.yml' }] } }),
        listWorkflowRuns: async () => ({ data: { workflow_runs: [], total_count: 0 } }),
      },
    },
  };
  return octokit;
}

test('reviewPR: approves and merges a fully approved PR opened by someone else', async () => {
  const octokit = fakeReviewOctokit({ prAuthor: 'contributor' });

  await reviewPR(octokit, 'owner', 'repo', 1);

  assert.equal(octokit.calls.createReview.length, 1);
  assert.equal(octokit.calls.createReview[0].event, 'APPROVE');
  assert.equal(octokit.calls.merge.length, 1);
});

test('reviewPR: does not try to approve a PR opened by the bot itself and asks BCR maintainers instead', async () => {
  const octokit = fakeReviewOctokit({ prAuthor: 'bazel-io' });

  await reviewPR(octokit, 'owner', 'repo', 1);

  assert.deepEqual(octokit.calls.createReview, [], 'GitHub rejects reviews on your own PR');
  assert.equal(octokit.calls.createComment.length, 1);
  assert.match(octokit.calls.createComment[0].body, /opened by @bazel-io and cannot be approved by itself/);
  assert.deepEqual(octokit.calls.requestReviewers.map(r => r.team_reviewers), [['bcr-maintainers']]);
  // Still attempts the merge, which succeeds once a BCR maintainer has approved.
  assert.equal(octokit.calls.merge.length, 1);
});

test('runPrReviewer: a failure on one PR does not stop reviewing the remaining PRs', async () => {
  const github = require('@actions/github');
  github.context.payload = { repository: { owner: { login: 'owner' }, name: 'repo' } };
  const now = new Date().toISOString();
  const octokit = fakeReviewOctokit({
    prAuthor: 'contributor',
    prs: [{ number: 1, updated_at: now }, { number: 2, updated_at: now }],
    failingPrs: new Set([1]),
  });

  await runPrReviewer(octokit);

  assert.deepEqual(octokit.calls.merge.map(m => m.pull_number), [2]);
  assert.equal(process.exitCode, 1, 'the run should still be marked as failed');
  process.exitCode = 0;
});
