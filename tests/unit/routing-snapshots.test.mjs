import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { route } from '../../scripts/route.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CASES_DIR = join(__dirname, '..', 'routing-cases');

const loadRegistry = () => {
  const dir = join(__dirname, '..', '..', '.claude', 'registry');
  const read = (f) => {
    try { return JSON.parse(readFileSync(join(dir, f), 'utf8')); }
    catch { return []; }
  };
  return {
    agents: read('ecc-agents.json'),
    native: read('native-inventory.json'),
    skills: [...read('ecc-skills.json'), ...read('harness-skills.json')],
    commands: read('ecc-commands.json'),
    mcps: [...read('ecc-mcps.json'), ...read('harness-mcps.json')],
    builtins: read('harness-builtins.json'),
  };
};

const registry = loadRegistry();

for (const file of readdirSync(CASES_DIR)) {
  if (!file.endsWith('.json')) continue;
  const tc = JSON.parse(readFileSync(join(CASES_DIR, file), 'utf8'));
  test(`routing-case: ${tc.name}`, () => {
    const r = route({ ...tc.input, registry });
    if (tc.expected.branch) assert.equal(r.branch, tc.expected.branch, 'branch');
    if (tc.expected.hook_profile) assert.equal(r.hook_profile, tc.expected.hook_profile, 'hook_profile');
    if (tc.expected.languages_detected) {
      assert.deepEqual(r.languages_detected.sort(), tc.expected.languages_detected.sort(), 'languages');
    }
    if (tc.expected.languages_detected_must_include) {
      for (const lang of tc.expected.languages_detected_must_include) {
        assert.ok(r.languages_detected.includes(lang), `language missing: ${lang}`);
      }
    }
    if (tc.expected.agents_must_include) {
      for (const a of tc.expected.agents_must_include) {
        assert.ok(r.agents.includes(a), `agent missing: ${a}`);
      }
    }
    if (tc.expected.skills_must_include) {
      for (const s of tc.expected.skills_must_include) {
        assert.ok(r.skills.includes(s), `skill missing: ${s}`);
      }
    }

    const registryNames = new Set(Object.values(registry)
      .flat()
      .filter(Boolean)
      .map((item) => item.name));
    const routedNames = [
      ...r.agents,
      ...r.skills,
      ...(r.commands || []).map((cmd) => cmd.replace(/^\//, '')),
      ...r.mcps,
    ];
    for (const name of routedNames) {
      assert.ok(registryNames.has(name), `routed item does not resolve: ${name}`);
    }
  });
}
