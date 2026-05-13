import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { refreshVendoredSkills } from '../../scripts/refresh-vendored.mjs';

function setupRepo() {
  return mkdtempSync(join(tmpdir(), 'rv-repo-'));
}
function setupCache() {
  return mkdtempSync(join(tmpdir(), 'rv-cache-'));
}
function writeSkill(dir, name, content) {
  const skillDir = join(dir, '.claude', 'skills', name);
  mkdirSync(skillDir, { recursive: true });
  writeFileSync(join(skillDir, 'SKILL.md'), content);
}
function writeUpstream(cache, plugin, version, skill, content) {
  const dir = join(cache, plugin, version, 'skills', skill);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'SKILL.md'), content);
}

test('refreshVendoredSkills bumps version and updates body to latest upstream', () => {
  const repo = setupRepo();
  const cache = setupCache();
  try {
    writeSkill(repo, 'test-skill',
      `---
name: test-skill
description: old description
vendored_from: "test-plugin@1.0.0"
license: MIT
---

# Test Skill (v1.0.0 content)
`);
    writeUpstream(cache, 'test-plugin', '1.0.0', 'test-skill',
      `---
name: test-skill
description: old description
---

# Test Skill (v1.0.0 content)
`);
    writeUpstream(cache, 'test-plugin', '2.0.0', 'test-skill',
      `---
name: test-skill
description: new description
---

# Test Skill (v2.0.0 content)
`);

    const results = refreshVendoredSkills(repo, cache);

    const r = results.find((x) => x.name === 'test-skill');
    assert.equal(r.status, 'version-bumped');
    assert.equal(r.version, '2.0.0');
    assert.equal(r.previousVersion, '1.0.0');

    const updated = readFileSync(join(repo, '.claude', 'skills', 'test-skill', 'SKILL.md'), 'utf8');
    assert.ok(updated.includes('# Test Skill (v2.0.0 content)'), 'body updated');
    assert.ok(updated.includes('2.0.0'), 'vendored_from bumped to 2.0.0');
    assert.ok(updated.includes('license') && updated.includes('MIT'), 'license preserved');
    assert.ok(updated.includes('new description'), 'upstream frontmatter pulled in');
  } finally {
    rmSync(repo, { recursive: true, force: true });
    rmSync(cache, { recursive: true, force: true });
  }
});

test('refreshVendoredSkills skips skills without vendored_from frontmatter', () => {
  const repo = setupRepo();
  const cache = setupCache();
  try {
    const original = `---
name: native-skill
description: a native skill, not vendored
---

# Native (untouched)
`;
    writeSkill(repo, 'native-skill', original);

    const results = refreshVendoredSkills(repo, cache);
    assert.equal(results.length, 0, 'native skill not in results');

    const after = readFileSync(join(repo, '.claude', 'skills', 'native-skill', 'SKILL.md'), 'utf8');
    assert.equal(after, original, 'native skill content untouched');
  } finally {
    rmSync(repo, { recursive: true, force: true });
    rmSync(cache, { recursive: true, force: true });
  }
});

test('refreshVendoredSkills reports upstream-not-found when plugin cache missing', () => {
  const repo = setupRepo();
  const cache = setupCache();
  try {
    writeSkill(repo, 'orphaned',
      `---
name: orphaned
description: vendored from a plugin not in this cache
vendored_from: "missing-plugin@1.0.0"
license: MIT
---

# Body
`);
    const results = refreshVendoredSkills(repo, cache);
    const r = results.find((x) => x.name === 'orphaned');
    assert.equal(r.status, 'upstream-not-found');
  } finally {
    rmSync(repo, { recursive: true, force: true });
    rmSync(cache, { recursive: true, force: true });
  }
});

test('refreshVendoredSkills reports up-to-date when version + content match', () => {
  const repo = setupRepo();
  const cache = setupCache();
  try {
    const body = `# Same Content
`;
    writeSkill(repo, 'stable',
      `---
name: stable
description: same
vendored_from: "stable-plugin@3.0.0"
license: MIT
---

${body}`);
    writeUpstream(cache, 'stable-plugin', '3.0.0', 'stable',
      `---
name: stable
description: same
---

${body}`);

    const results = refreshVendoredSkills(repo, cache);
    const r = results.find((x) => x.name === 'stable');
    assert.equal(r.status, 'up-to-date');
    assert.equal(r.version, '3.0.0');
  } finally {
    rmSync(repo, { recursive: true, force: true });
    rmSync(cache, { recursive: true, force: true });
  }
});

test('refreshVendoredSkills picks latest numeric version when multiple present', () => {
  const repo = setupRepo();
  const cache = setupCache();
  try {
    writeSkill(repo, 'multi-version',
      `---
name: multi-version
description: test
vendored_from: "pkg@1.0.0"
license: MIT
---

# v1
`);
    // Versions out of lexical order to test numeric sort
    writeUpstream(cache, 'pkg', '1.0.0', 'multi-version', `# v1\n`);
    writeUpstream(cache, 'pkg', '10.0.0', 'multi-version', `# v10\n`);
    writeUpstream(cache, 'pkg', '2.0.0', 'multi-version', `# v2\n`);

    const results = refreshVendoredSkills(repo, cache);
    const r = results.find((x) => x.name === 'multi-version');
    assert.equal(r.version, '10.0.0', 'numeric sort picks 10.0.0 over 2.0.0');
  } finally {
    rmSync(repo, { recursive: true, force: true });
    rmSync(cache, { recursive: true, force: true });
  }
});

test('refreshVendoredSkills keeps third-party license version in sync on version bump', () => {
  const repo = setupRepo();
  const cache = setupCache();
  try {
    writeSkill(repo, 'licensed-skill',
      `---
name: licensed-skill
description: test
vendored_from: "test-org/test-plugin@1.0.0"
license: MIT
---

# v1
`);
    mkdirSync(join(repo, '.claude', 'skills'), { recursive: true });
    writeFileSync(join(repo, '.claude', 'skills', 'THIRD_PARTY_LICENSES.md'),
      `# Third-Party Licenses

## test-plugin -- Maintainer

- **Version vendored:** 1.0.0
- **Skills imported:** \`licensed-skill\`
`);
    writeUpstream(cache, 'test-org/test-plugin', '2.0.0', 'licensed-skill', `# v2\n`);

    const results = refreshVendoredSkills(repo, cache);

    const r = results.find((x) => x.name === 'licensed-skill');
    assert.equal(r.status, 'version-bumped');
    const licenses = readFileSync(join(repo, '.claude', 'skills', 'THIRD_PARTY_LICENSES.md'), 'utf8');
    assert.ok(licenses.includes('- **Version vendored:** 2.0.0'));
    assert.ok(!licenses.includes('- **Version vendored:** 1.0.0'));
  } finally {
    rmSync(repo, { recursive: true, force: true });
    rmSync(cache, { recursive: true, force: true });
  }
});
