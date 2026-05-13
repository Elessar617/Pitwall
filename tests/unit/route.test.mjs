import { test } from 'node:test';
import assert from 'node:assert/strict';
import { detectTaskType, detectLanguages, detectOutputSkills, route } from '../../scripts/route.mjs';

test('detectTaskType matches "add" -> build', () => {
  assert.equal(detectTaskType('add a rate limiter to the gateway'), 'build');
});

test('detectTaskType matches "fix" -> bug', () => {
  assert.equal(detectTaskType('fix the broken login redirect'), 'bug');
});

test('detectTaskType matches "refactor" -> refactor', () => {
  assert.equal(detectTaskType('refactor the auth module'), 'refactor');
});

test('detectTaskType matches "investigate" -> spike', () => {
  assert.equal(detectTaskType('investigate why GraphQL is slow'), 'spike');
});

test('detectTaskType matches "RFC" -> spec-author', () => {
  assert.equal(detectTaskType('write an RFC for the new auth flow'), 'spec-author');
});

test('detectTaskType matches "release" -> ship', () => {
  assert.equal(detectTaskType('cut a v0.3.0 release'), 'ship');
});

test('detectTaskType returns null when no signal', () => {
  assert.equal(detectTaskType('thanks!'), null);
});

test('detectLanguages from go files', () => {
  assert.deepEqual(detectLanguages(['gateway/handler.go']), ['go']);
});

test('detectLanguages from mixed files', () => {
  const langs = detectLanguages(['a.py', 'b.ts']);
  assert.ok(langs.includes('python'));
  assert.ok(langs.includes('typescript'));
});

test('detectOutputSkills from release artifact files', () => {
  const skills = detectOutputSkills(['ship/docs/report.pdf', 'ship/docs/report.docx']);
  assert.deepEqual(skills.sort(), ['docx', 'pdf']);
});

test('route returns native-only fallback on no match', () => {
  const r = route({
    prompt: 'thanks!',
    files_in_scope: [],
    registry: { agents: [], skills: [], commands: [], mcps: [] },
  });
  assert.equal(r.branch, 'fallback');
  assert.ok(r.agents.includes('planner'));
  assert.ok(r.agents.includes('implementer'));
  assert.equal(r.hook_profile, 'standard');
});

test('route recommends minimal profile for spike', () => {
  const r = route({
    prompt: 'investigate the GraphQL latency regression',
    files_in_scope: [],
    registry: { agents: [], skills: [], commands: [], mcps: [] },
  });
  assert.equal(r.branch, 'spike');
  assert.equal(r.hook_profile, 'minimal');
});

test('route recommends strict profile for ship', () => {
  const r = route({
    prompt: 'cut the v0.3.0 release and write changelog',
    files_in_scope: [],
    registry: { agents: [], skills: [], commands: [], mcps: [] },
  });
  assert.equal(r.branch, 'ship');
  assert.equal(r.hook_profile, 'strict');
});

test('route adds output skills for ship files', () => {
  const r = route({
    prompt: 'release the report',
    files_in_scope: ['ship/docs/report.pdf'],
    registry: { agents: [], skills: [], commands: [], mcps: [] },
  });
  assert.equal(r.branch, 'ship');
  assert.ok(r.skills.includes('pdf'));
});

test('route adds Go language items for go-feature task', () => {
  const r = route({
    prompt: 'add a rate limiter to the gateway service',
    files_in_scope: ['gateway/handler.go'],
    registry: { agents: [], skills: [], commands: [], mcps: [] },
  });
  assert.equal(r.branch, 'build');
  assert.ok(r.agents.includes('go-reviewer'));
  assert.ok(r.skills.includes('golang-patterns'));
});
