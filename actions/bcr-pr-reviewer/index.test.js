const test = require('node:test');
const assert = require('node:assert/strict');
const { getPrApprovers } = require('./index.js');

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
