import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseMarkdown, normalizeRecord } from '../../scripts/lib/frontmatter.mjs';
import { writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

const mkfile = (dir, name, body) => {
  const p = join(dir, name);
  writeFileSync(p, body);
  return p;
};

test('parses frontmatter and body', () => {
  const dir = mkdtempSync(join(tmpdir(), 'fm-'));
  const file = mkfile(dir, 'a.md',
    '---\nname: foo\ndescription: A thing\n---\nFirst paragraph.\n\nSecond.');
  const r = parseMarkdown(file);
  assert.equal(r.frontmatter.name, 'foo');
  assert.equal(r.frontmatter.description, 'A thing');
  assert.match(r.firstParagraph, /First paragraph/);
  rmSync(dir, { recursive: true, force: true });
});

test('handles missing frontmatter', () => {
  const dir = mkdtempSync(join(tmpdir(), 'fm-'));
  const file = mkfile(dir, 'b.md', 'Just body, no frontmatter.\n');
  const r = parseMarkdown(file);
  assert.deepEqual(r.frontmatter, {});
  assert.match(r.firstParagraph, /Just body/);
  rmSync(dir, { recursive: true, force: true });
});

test('handles malformed YAML by returning empty frontmatter', () => {
  const dir = mkdtempSync(join(tmpdir(), 'fm-'));
  const file = mkfile(dir, 'c.md', '---\n: : broken\n---\nbody\n');
  const r = parseMarkdown(file);
  assert.deepEqual(r.frontmatter, {});
  assert.ok(r.parseError);
  rmSync(dir, { recursive: true, force: true });
});

test('normalizeRecord applies defaults', () => {
  const r = normalizeRecord({ frontmatter: {}, firstParagraph: 'Hello.' }, {
    filenameStem: 'go-reviewer',
    kind: 'agent',
    source: 'ecc',
  });
  assert.equal(r.name, 'go-reviewer');
  assert.equal(r.kind, 'agent');
  assert.equal(r.source, 'ecc');
  assert.equal(r.description, 'Hello.');
  assert.deepEqual(r.languages, []);
  assert.deepEqual(r.tools, []);
  assert.equal(r.model, null);
});

test('normalizeRecord coerces scalar languages to array', () => {
  const r = normalizeRecord(
    { frontmatter: { name: 'x', languages: 'python' }, firstParagraph: '' },
    { filenameStem: 'x', kind: 'skill', source: 'ecc' }
  );
  assert.deepEqual(r.languages, ['python']);
});

test('normalizeRecord uses filename when no name in frontmatter', () => {
  const r = normalizeRecord(
    { frontmatter: {}, firstParagraph: '' },
    { filenameStem: 'tdd-workflow', kind: 'command', source: 'ecc' }
  );
  assert.equal(r.name, 'tdd-workflow');
  assert.equal(r.description, '');
});
