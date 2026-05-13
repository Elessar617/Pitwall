import { test } from 'node:test';
import assert from 'node:assert/strict';
import { detectTransition, isMidTaskChatter, mergeWithCache } from '../../scripts/route.mjs';

test('detectTransition fires on "now let\'s"', () => {
  assert.equal(detectTransition("now let's work on the auth piece"), true);
});

test('detectTransition fires on "switch to"', () => {
  assert.equal(detectTransition('switch to the python module'), true);
});

test('detectTransition fires on "actually,"', () => {
  assert.equal(detectTransition('actually, let me try the other approach'), true);
});

test('detectTransition does NOT fire on mid-task chatter', () => {
  assert.equal(detectTransition('yes do that'), false);
  assert.equal(detectTransition('ok'), false);
  assert.equal(detectTransition('explain more'), false);
});

test('isMidTaskChatter only matches short continuations', () => {
  assert.equal(isMidTaskChatter('yes do that'), true);
  assert.equal(isMidTaskChatter('ok'), true);
  assert.equal(isMidTaskChatter('explain more'), true);
  assert.equal(isMidTaskChatter('fix the broken login redirect'), false);
});

test('mergeWithCache reuses cache for mid-task chatter with no fresh route', () => {
  const cache = { branch: 'build', agents: ['planner'], skills: [] };
  const fresh = { branch: 'fallback', agents: ['implementer'], skills: ['x'] };
  const result = mergeWithCache(cache, fresh, false, 'yes do that');
  assert.deepEqual(result, cache);
});

test('mergeWithCache uses fresh route for a new task without transition phrase', () => {
  const cache = { branch: 'build', agents: ['planner'] };
  const fresh = { branch: 'bug', agents: ['implementer'] };
  const result = mergeWithCache(cache, fresh, false, 'fix the broken login redirect');
  assert.deepEqual(result, fresh);
});

test('mergeWithCache uses fresh when transition detected', () => {
  const cache = { branch: 'build', agents: ['planner'] };
  const fresh = { branch: 'bug', agents: ['implementer'] };
  const result = mergeWithCache(cache, fresh, true, 'actually, fix the bug');
  assert.deepEqual(result, fresh);
});
