import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { scrapeNative } from '../../scripts/lib/native-scraper.mjs';

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');

test('scrapeNative indexes local agents, skills, rules, and project MCPs', () => {
  const root = mkdtempSync(join(tmpdir(), 'native-'));
  mkdirSync(join(root, '.claude', 'agents'), { recursive: true });
  mkdirSync(join(root, '.claude', 'skills', 'tdd-loop'), { recursive: true });
  mkdirSync(join(root, '.claude', 'rules'), { recursive: true });

  writeFileSync(join(root, '.claude', 'agents', 'reviewer-agent.md'),
    '---\ntools: Read, Bash, Grep\n---\n# Reviewer\n');
  writeFileSync(join(root, '.claude', 'skills', 'tdd-loop', 'SKILL.md'),
    '---\nname: tdd-loop\ndescription: TDD\n---\n# TDD\n');
  writeFileSync(join(root, '.claude', 'rules', 'testing-discipline.md'), '# Testing\n');
  writeFileSync(join(root, '.claude', 'settings.json'), JSON.stringify({
    mcpServers: {
      filesystem: { command: 'npx' },
    },
  }));

  const result = scrapeNative(root);
  const reviewer = result.find((item) => item.name === 'reviewer' && item.kind === 'agent');
  assert.ok(reviewer);
  assert.deepEqual(reviewer.tools, ['Read', 'Bash', 'Grep']);
  assert.ok(result.some((item) => item.name === 'tdd-loop' && item.kind === 'skill'));
  assert.ok(result.some((item) => item.name === 'testing-discipline' && item.kind === 'rule'));
  assert.ok(result.some((item) => item.name === 'filesystem' && item.kind === 'mcp'));

  rmSync(root, { recursive: true, force: true });
});

test('scrapeNative includes vendored harness skills (cleanroom-bootstrap invariant)', () => {
  // These four skills are referenced by .claude/routing/*.md branch files but
  // originate from harness plugins (superpowers, andrej-karpathy-skills).
  // To make routing deterministic on a fresh clone with no plugins installed,
  // they are vendored as markdown under .claude/skills/<name>/SKILL.md with
  // proper attribution (MIT license preserved in .claude/skills/THIRD_PARTY_LICENSES.md).
  // If this test fails, see docs/development-log.md for the 2026-05-12 CI-driven
  // vendoring decision.
  const REQUIRED = ['systematic-debugging', 'karpathy-guidelines', 'writing-plans', 'brainstorming'];
  const result = scrapeNative(REPO_ROOT);
  const skillNames = result.filter((r) => r.kind === 'skill').map((r) => r.name);
  for (const name of REQUIRED) {
    assert.ok(skillNames.includes(name), `vendored skill missing from native inventory: ${name}`);
  }
});
