const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { getPrApprovers, moduleVersionDir, escapingPathForDiff, reviewPR, runPrReviewer, runHandleComment } = require('./index.js');

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
    state: 'open',
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

// Tests for the `@bazel-io review` comment command.

const github = require('@actions/github');

const HEAD_SHA = 'head-sha';

function reviewCommandOctokit({
  state = 'open',
  merged = false,
  draft = false,
  approved = true,
  mergeError = null,
  sensitiveMetadata = false,
  newModule = false,
} = {}) {
  const calls = [];
  const metadata = {
    maintainers: [{ github: 'Maintainer', github_user_id: 7 }],
    versions: ['1.0.0', '1.1.0'],
  };
  const files = [{ filename: 'modules/foo/1.1.0/source.json' }];
  if (sensitiveMetadata || newModule) {
    files.push({ filename: 'modules/foo/metadata.json' });
  }
  const octokit = {
    paginate: async (fn, params) => (await fn(params)).data,
    request: async (route) => {
      assert.equal(route, 'GET /user/{account_id}');
      return { data: { login: 'Maintainer' } };
    },
    rest: {
      pulls: {
        get: async () => ({
          data: {
            state,
            merged,
            draft,
            changed_files: files.length,
            head: { sha: HEAD_SHA },
            user: { login: 'author', id: 1 },
            labels: [],
            requested_reviewers: [],
            requested_teams: [],
          },
        }),
        listFiles: async () => ({ data: files }),
        listCommits: async () => ({ data: [{ sha: HEAD_SHA, parents: [{ sha: 'base' }] }] }),
        listReviews: async () => ({
          data: approved
            ? [{ user: { login: 'Maintainer' }, state: 'APPROVED', commit_id: HEAD_SHA, submitted_at: '2026-09-30T00:00:00Z' }]
            : [],
        }),
        createReview: async ({ event }) => calls.push(['createReview', event]),
        merge: async ({ sha }) => {
          if (mergeError) {
            throw new Error(mergeError);
          }
          calls.push(['merge', sha]);
        },
        requestReviewers: async () => calls.push(['requestReviewers']),
      },
      repos: {
        getContent: async ({ ref }) => {
          // A new module doesn't have a metadata.json on the main branch yet.
          if (newModule && ref === 'main') {
            throw Object.assign(new Error('Not Found'), { status: 404 });
          }
          // The PR head changes a non-versions field of metadata.json when `sensitiveMetadata` is set.
          const content = sensitiveMetadata && ref !== 'main' ? { ...metadata, homepage: 'https://example.com' } : metadata;
          return { data: { content: Buffer.from(JSON.stringify(content)).toString('base64') } };
        },
      },
      users: {
        getByUsername: async () => ({ data: { id: 7 } }),
        getAuthenticated: async () => ({ data: { login: 'bazel-io' } }),
      },
      issues: {
        addLabels: async ({ labels }) => calls.push(['addLabels', labels]),
        createComment: async ({ body }) => calls.push(['createComment', body]),
        listComments: async () => ({ data: [] }),
      },
      reactions: {
        createForIssueComment: async ({ content }) => calls.push(['reaction', content]),
      },
      actions: {
        listRepoWorkflows: async () => ({ data: { workflows: [{ id: 5, path: '.github/workflows/dismiss_approvals.yml' }] } }),
        listWorkflowRuns: async () => ({ data: { total_count: 0, workflow_runs: [] } }),
      },
      search: {
        issuesAndPullRequests: async () => ({ data: { total_count: 1 } }),
        code: async () => ({ data: { total_count: 1 } }),
      },
    },
  };
  return { octokit, calls };
}

async function runComment(body, options) {
  github.context.payload = {
    repository: { name: 'bazel-central-registry', owner: { login: 'bazelbuild' } },
    issue: { number: 42, pull_request: {} },
    comment: { id: 1001, body, user: { login: 'Commenter' } },
  };
  const { octokit, calls } = reviewCommandOctokit(options);
  const originalLog = console.log;
  const originalError = console.error;
  console.log = () => {};
  console.error = () => {};
  try {
    await runHandleComment(octokit);
  } finally {
    console.log = originalLog;
    console.error = originalError;
  }
  return calls;
}

test('@bazel-io review: merges a PR whose modules are all approved', async () => {
  const calls = await runComment('@bazel-io review\n');

  assert.deepEqual(calls, [
    ['reaction', 'eyes'],
    ['createReview', 'APPROVE'],
    ['merge', HEAD_SHA],
    ['addLabels', ['auto-merged']],
    ['reaction', 'rocket'],
  ]);
});

test('@bazel-io review: reports modules that still need maintainer approval', async () => {
  const calls = await runComment('@bazel-io review', { approved: false });

  assert.equal(calls.some(([name]) => name === 'merge'), false);
  assert.deepEqual(calls.at(-1), [
    'createComment',
    '@Commenter, this PR could not be merged yet. The following modules still need approval from one of their maintainers: foo.',
  ]);
});

test('@bazel-io review: reports why an approved PR could not be merged', async () => {
  const calls = await runComment('@bazel-io review', { mergeError: 'Required status check "presubmit" is expected.' });

  const [name, body] = calls.at(-1);
  assert.equal(name, 'createComment');
  assert.match(body, /^@Commenter, this PR could not be merged yet\. All modules in this PR have been approved/);
  assert.match(body, /Required status check "presubmit" is expected\./);
});

test('@bazel-io review: does not merge a PR with sensitive metadata.json changes', async () => {
  const calls = await runComment('@bazel-io review', { sensitiveMetadata: true });

  assert.equal(calls.some(([name]) => name === 'merge'), false);
  assert.deepEqual(calls.at(-1), [
    'createComment',
    '@Commenter, this PR could not be merged yet. This PR has sensitive metadata.json changes, it needs to be reviewed by a BCR maintainer.',
  ]);
});

test('@bazel-io review: asks for a BCR maintainer review when a new module is added', async () => {
  const calls = await runComment('@bazel-io review', { newModule: true });

  assert.equal(calls.some(([name]) => name === 'merge'), false);
  assert.deepEqual(calls.at(-1), [
    'createComment',
    '@Commenter, this PR could not be merged yet. This PR adds a new module, it needs to be reviewed by a BCR maintainer.',
  ]);
});

test('@bazel-io review: does not review a closed PR', async () => {
  const calls = await runComment('@bazel-io review', { state: 'closed' });

  assert.deepEqual(calls, [
    ['reaction', 'eyes'],
    ['createComment', '@Commenter, this PR could not be merged yet. This PR is already closed.'],
  ]);
});

test('@bazel-io review: does not review a merged PR', async () => {
  const calls = await runComment('@bazel-io review', { state: 'closed', merged: true });

  assert.deepEqual(calls, [
    ['reaction', 'eyes'],
    ['createComment', '@Commenter, this PR could not be merged yet. This PR is already merged.'],
  ]);
});

test('@bazel-io review: does not review a draft PR', async () => {
  const calls = await runComment('@bazel-io review', { draft: true });

  assert.deepEqual(calls, [
    ['reaction', 'eyes'],
    ['createComment', '@Commenter, this PR could not be merged yet. This PR is a draft, mark it as ready for review first.'],
  ]);
});

test('@bazel-io review: ignores comments that are not exactly the command', async () => {
  const calls = await runComment('@bazel-io review this please');

  assert.deepEqual(calls, []);
});

// moduleVersionDir() only rewrites strings, so its results are cwd-relative: run the
// filesystem-touching assertions from a scratch tree laid out like the runner's.
function withModuleTree(fn) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'bcr-symlink-test-'));
  const cwd = process.cwd();
  const outside = path.join(dir, 'host');
  try {
    fs.mkdirSync(path.join(dir, 'modules', 'rules_cc', '1.2.3'), { recursive: true });
    fs.mkdirSync(path.join(dir, 'modules', 'rules_cc', '1.3.0'), { recursive: true });
    fs.mkdirSync(outside, { recursive: true });
    fs.writeFileSync(path.join(outside, 'runner-secret.txt'), 'SECRET\n');
    process.chdir(dir);
    return fn({ dir, outside });
  } finally {
    process.chdir(cwd);
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

test('moduleVersionDir: a module name that escapes modules/ is rejected', () => {
  // The PR file list feeds moduleName, and "modules/../1.0.0/f" matches the caller's
  // regex with moduleName "..", which used to anchor the check at the workspace root.
  assert.equal(moduleVersionDir('..', '0.9.0'), null);
  assert.equal(moduleVersionDir('.', '1.0.0'), null);
});

test('escapingPathForDiff: real version directories inside the module are allowed', () => {
  withModuleTree(() => {
    assert.equal(escapingPathForDiff('rules_cc', ['modules/rules_cc/1.2.3', 'modules/rules_cc/1.3.0']), null);
  });
});

test('escapingPathForDiff: a version directory that is a symlink out of the module is rejected', () => {
  withModuleTree(({ outside }) => {
    fs.rmSync('modules/rules_cc/1.2.3', { recursive: true, force: true });
    fs.symlinkSync(outside, 'modules/rules_cc/1.2.3');
    assert.equal(escapingPathForDiff('rules_cc', ['modules/rules_cc/1.2.3']), 'modules/rules_cc/1.2.3');
  });
});

test('escapingPathForDiff: a symlink nested in a version directory is rejected', () => {
  withModuleTree(({ outside }) => {
    fs.symlinkSync(path.join(outside, 'runner-secret.txt'), 'modules/rules_cc/1.3.0/leak.txt');
    assert.equal(
      escapingPathForDiff('rules_cc', ['modules/rules_cc/1.3.0']),
      'modules/rules_cc/1.3.0/leak.txt',
    );
  });
});

test('escapingPathForDiff: a symlink to a directory of secrets is rejected', () => {
  withModuleTree(({ outside }) => {
    fs.symlinkSync(outside, 'modules/rules_cc/1.3.0/dirlink');
    assert.equal(escapingPathForDiff('rules_cc', ['modules/rules_cc/1.3.0']), 'modules/rules_cc/1.3.0/dirlink');
  });
});

test('escapingPathForDiff: a symlink that stays inside the module is allowed', () => {
  withModuleTree(() => {
    fs.symlinkSync(path.resolve('modules/rules_cc/1.2.3/BUILD.bazel'), path.resolve('modules/rules_cc/1.3.0/BUILD.bazel'));
    assert.equal(escapingPathForDiff('rules_cc', ['modules/rules_cc/1.3.0']), null);
  });
});

test('escapingPathForDiff: a symlink reached through an escaping intermediate dir is rejected', () => {
  withModuleTree(({ outside }) => {
    fs.mkdirSync(path.resolve('modules/rules_cc/1.3.0/nested'), { recursive: true });
    fs.symlinkSync(path.join(outside, 'runner-secret.txt'), 'modules/rules_cc/1.3.0/nested/leak.txt');
    assert.equal(
      escapingPathForDiff('rules_cc', ['modules/rules_cc/1.3.0']),
      'modules/rules_cc/1.3.0/nested/leak.txt',
    );
  });
});

test('escapingPathForDiff: the previous-version side is checked as well as the current one', () => {
  withModuleTree(({ outside }) => {
    fs.symlinkSync(path.join(outside, 'runner-secret.txt'), 'modules/rules_cc/1.2.3/leak.txt');
    assert.equal(
      escapingPathForDiff('rules_cc', ['modules/rules_cc/1.2.3', 'modules/rules_cc/1.3.0']),
      'modules/rules_cc/1.2.3/leak.txt',
    );
  });
});

test('escapingPathForDiff: a module directory that is itself a symlink out of modules/ is rejected', () => {
  withModuleTree(({ outside }) => {
    fs.mkdirSync(path.join(outside, 'elsewhere'), { recursive: true });
    fs.rmSync(path.resolve('modules/rules_cc'), { recursive: true, force: true });
    fs.symlinkSync(path.join(outside, 'elsewhere'), path.resolve('modules/rules_cc'));
    assert.equal(escapingPathForDiff('rules_cc', ['modules/rules_cc/1.3.0']), path.join('modules', 'rules_cc'));
  });
});
