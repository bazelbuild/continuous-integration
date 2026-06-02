const test = require('node:test');
const assert = require('node:assert/strict');

const {
  canUserUseSkipCheck,
  checkIfAllModifiedModulesApproved,
  getModifiedModules,
  isMaintainerForAllModifiedModules,
} = require('./index.js');

test('getModifiedModules normalizes module@version entries', () => {
  const modifiedModules = getModifiedModules(new Set(['rules_cc@1.2.3', 'bazel_skylib@1.7.1']));
  assert.deepEqual(Array.from(modifiedModules).sort(), ['bazel_skylib', 'rules_cc']);
});

test('isMaintainerForAllModifiedModules requires full coverage', () => {
  const modifiedModules = new Set(['rules_cc', 'bazel_skylib']);
  const maintainersMap = new Map([
    ['alice', new Set(['rules_cc', 'bazel_skylib'])],
    ['bob', new Set(['rules_cc'])],
  ]);

  assert.equal(isMaintainerForAllModifiedModules('alice', modifiedModules, maintainersMap), true);
  assert.equal(isMaintainerForAllModifiedModules('ALICE', modifiedModules, maintainersMap), true);
  assert.equal(isMaintainerForAllModifiedModules('bob', modifiedModules, maintainersMap), false);
  assert.equal(isMaintainerForAllModifiedModules('carol', modifiedModules, maintainersMap), false);
});

test('canUserUseSkipCheck allows the PR author', async () => {
  const allowed = await canUserUseSkipCheck(
      {},
      'bazelbuild',
      'bazel-central-registry',
      123,
      'AUTHOR',
      'author');
  assert.equal(allowed, true);
});

test('canUserUseSkipCheck allows repository collaborators', async () => {
  const allowed = await canUserUseSkipCheck(
      {},
      'bazelbuild',
      'bazel-central-registry',
      123,
      'reviewer',
      'author',
      {
        isRepoCollaboratorFn: async () => true,
      });
  assert.equal(allowed, true);
});

test('canUserUseSkipCheck allows a maintainer covering all modified modules', async () => {
  const allowed = await canUserUseSkipCheck(
      {},
      'bazelbuild',
      'bazel-central-registry',
      123,
      'maintainer',
      'author',
      {
        isRepoCollaboratorFn: async () => false,
        fetchAllModifiedModuleVersionsFn: async () => new Set(['rules_cc@1.2.3', 'bazel_skylib@1.7.1']),
        generateMaintainersMapFn: async () => [
          new Map([['maintainer', new Set(['rules_cc', 'bazel_skylib'])]]),
          new Set(),
        ],
      });
  assert.equal(allowed, true);
});

test('canUserUseSkipCheck rejects a maintainer with partial coverage', async () => {
  const allowed = await canUserUseSkipCheck(
      {},
      'bazelbuild',
      'bazel-central-registry',
      123,
      'maintainer',
      'author',
      {
        isRepoCollaboratorFn: async () => false,
        fetchAllModifiedModuleVersionsFn: async () => new Set(['rules_cc@1.2.3', 'bazel_skylib@1.7.1']),
        generateMaintainersMapFn: async () => [
          new Map([['maintainer', new Set(['rules_cc'])]]),
          new Set(),
        ],
      });
  assert.equal(allowed, false);
});

test('canUserUseSkipCheck rejects a public commenter with no authorization', async () => {
  const allowed = await canUserUseSkipCheck(
      {},
      'bazelbuild',
      'bazel-central-registry',
      123,
      'random-user',
      'author',
      {
        isRepoCollaboratorFn: async () => false,
        fetchAllModifiedModuleVersionsFn: async () => new Set(['rules_cc@1.2.3']),
        generateMaintainersMapFn: async () => [
          new Map([['maintainer', new Set(['rules_cc'])]]),
          new Set(),
        ],
      });
  assert.equal(allowed, false);
});

test('checkIfAllModifiedModulesApproved accepts a maintainer review', async () => {
  const result = await checkIfAllModifiedModulesApproved(
      new Set(['rules_cc']),
      new Map([['maintainer', new Set(['rules_cc'])]]),
      new Set(['maintainer']));

  assert.equal(result.allModulesApproved, true);
  assert.equal(result.anyModuleApproved, true);
  assert.deepEqual(result.modulesNotApproved, []);
});

test('checkIfAllModifiedModulesApproved requires reviewer approval', async () => {
  const result = await checkIfAllModifiedModulesApproved(
      new Set(['rules_cc']),
      new Map([['author', new Set(['rules_cc'])]]),
      new Set());

  assert.equal(result.allModulesApproved, false);
  assert.equal(result.anyModuleApproved, false);
  assert.deepEqual(result.modulesNotApproved, ['rules_cc']);
});
