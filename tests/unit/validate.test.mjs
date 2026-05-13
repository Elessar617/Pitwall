import { test } from 'node:test';
import assert from 'node:assert/strict';
import { extractNames, classifyNames } from '../../scripts/lib/validate.mjs';

test('extractNames pulls backticked tokens from markdown', () => {
  const md = 'Load `python-reviewer` and `go-build-resolver`. Also `superpowers:brainstorming`.';
  const names = extractNames(md);
  assert.ok(names.includes('python-reviewer'));
  assert.ok(names.includes('go-build-resolver'));
  assert.ok(names.includes('superpowers:brainstorming'));
});

test('extractNames ignores filesystem-looking tokens', () => {
  const md = 'See `agents/foo.md` and `/tdd` and `foo.json`.';
  const names = extractNames(md);
  assert.equal(names.length, 0);
});

test('classifyNames separates resolved vs dangling', () => {
  const registry = {
    agents: [{ name: 'python-reviewer' }],
    skills: [{ name: 'go-patterns' }],
  };
  const { resolved, dangling } = classifyNames(
    ['python-reviewer', 'go-patterns', 'no-such-thing'],
    registry
  );
  assert.deepEqual(resolved, ['python-reviewer', 'go-patterns']);
  assert.deepEqual(dangling, ['no-such-thing']);
});
