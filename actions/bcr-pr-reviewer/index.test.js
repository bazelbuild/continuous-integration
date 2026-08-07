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

test('getPrApprovers: a stale approval does not count once a merge commit changes the PR head', async () => {
  // C1 gets approved by a maintainer, then C2 (a merge commit -- 2 parents) is
  // pushed afterwards and becomes the PR's real HEAD. The maintainer's review
  // predates C2 and never saw its content.
  const commits = [
    { sha: 'C1', parents: [{ sha: 'base' }], commit: { author: { date: '2026-08-06T00:00:00Z' } } },
    { sha: 'C2-merge', parents: [{ sha: 'C1' }, { sha: 'other' }], commit: { author: { date: '2026-08-06T00:20:00Z' } } },
  ];
  const reviews = [
    { user: { login: 'maintainer' }, state: 'APPROVED', submitted_at: '2026-08-06T00:10:00Z' },
  ];

  const approvers = await getPrApprovers(fakeOctokit({ commits, reviews }), 'owner', 'repo', 1);

  assert.equal(approvers.has('maintainer'), false, 'a review submitted before the real HEAD must not count as approving it');
});

test('getPrApprovers: an approval submitted after a merge commit still counts', async () => {
  const commits = [
    { sha: 'C1', parents: [{ sha: 'base' }], commit: { author: { date: '2026-08-06T00:00:00Z' } } },
    { sha: 'C2-merge', parents: [{ sha: 'C1' }, { sha: 'other' }], commit: { author: { date: '2026-08-06T00:20:00Z' } } },
  ];
  const reviews = [
    { user: { login: 'maintainer' }, state: 'APPROVED', submitted_at: '2026-08-06T00:30:00Z' },
  ];

  const approvers = await getPrApprovers(fakeOctokit({ commits, reviews }), 'owner', 'repo', 1);

  assert.equal(approvers.has('maintainer'), true, 'a review submitted after the real HEAD should still count');
});

test('getPrApprovers: works normally when the PR has no merge commits at all', async () => {
  const commits = [
    { sha: 'C1', parents: [{ sha: 'base' }], commit: { author: { date: '2026-08-06T00:00:00Z' } } },
  ];
  const reviews = [
    { user: { login: 'maintainer' }, state: 'APPROVED', submitted_at: '2026-08-06T00:05:00Z' },
  ];

  const approvers = await getPrApprovers(fakeOctokit({ commits, reviews }), 'owner', 'repo', 1);

  assert.equal(approvers.has('maintainer'), true);
});
