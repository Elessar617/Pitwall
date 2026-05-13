import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..', '..');

function read(path) {
  return readFileSync(join(REPO_ROOT, path), 'utf8');
}

function readJson(path) {
  return JSON.parse(read(path));
}

function tableRow(markdown, label) {
  return markdown.split('\n').find((line) => line.startsWith(`| **${label}** |`)) || '';
}

function git(args) {
  const result = spawnSync('git', args, { cwd: REPO_ROOT, encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  return result.stdout.trim();
}

function gitMaybe(args) {
  return spawnSync('git', args, { cwd: REPO_ROOT, encoding: 'utf8' });
}

function localSkillCount() {
  const skillsDir = join(REPO_ROOT, '.claude', 'skills');
  return readdirSync(skillsDir)
    .filter((entry) => existsSync(join(skillsDir, entry, 'SKILL.md')))
    .length;
}

function unitTestCount() {
  const unitDir = join(REPO_ROOT, 'tests', 'unit');
  let count = 0;
  for (const file of readdirSync(unitDir)) {
    if (!file.endsWith('.test.mjs')) continue;
    if (file === 'routing-snapshots.test.mjs') continue;
    const content = readFileSync(join(unitDir, file), 'utf8');
    count += (content.match(/\btest\(/g) || []).length;
  }
  const routingCases = readdirSync(join(REPO_ROOT, 'tests', 'routing-cases'))
    .filter((file) => file.endsWith('.json'))
    .length;
  return count + routingCases;
}

test('human source-of-truth docs reflect current generated inventory', () => {
  const devLog = read('docs/development-log.md');
  const skillsDoc = read('SKILLS.md');
  const startHere = read('START-HERE.md');
  const readme = read('README.md');
  const claude = read('CLAUDE.md');
  const mcpSetup = read('.claude/MCP-SETUP.md');

  const eccShort = git(['-C', 'external/ecc', 'rev-parse', '--short=8', 'HEAD']);
  const eccDescribe = git(['-C', 'external/ecc', 'describe', '--tags', '--always', '--dirty']);
  assert.ok(tableRow(devLog, 'Submodule').includes(eccShort));
  assert.ok(tableRow(devLog, 'Submodule').includes(eccDescribe));
  assert.ok(skillsDoc.includes(`Submodule pinned at SHA \`${eccShort}\``));

  const registrySummary = [
    `${readJson('.claude/registry/ecc-agents.json').length} ECC agents`,
    `${readJson('.claude/registry/ecc-skills.json').length} skills`,
    `${readJson('.claude/registry/ecc-commands.json').length} commands`,
    `${readJson('.claude/registry/ecc-mcps.json').length} MCP`,
    `${readJson('.claude/registry/ecc-language-rules.json').length} lang-rules`,
    `${readJson('.claude/registry/ecc-hook-profiles.json').length} hook-profiles`,
    `${readJson('.claude/registry/harness-builtins.json').length} built-ins`,
    `${readJson('.claude/registry/native-inventory.json').length} native records`,
  ].join(' + ');
  assert.ok(tableRow(devLog, 'Registries').includes(registrySummary));
  assert.ok(tableRow(devLog, 'Registries').toLowerCase().includes('harness plugin counts are machine-specific'));

  const skills = localSkillCount();
  assert.ok(readme.includes(`- ${skills} skills (`));
  assert.ok(claude.includes(`- **${skills} skills**`));
  assert.ok(startHere.includes(`— ${skills} procedures`));
  assert.ok(mcpSetup.includes(`${skills} local skills`));
  assert.ok(tableRow(devLog, 'Skills').includes(`${skills} local skills`));

  assert.ok(tableRow(devLog, 'Tests').includes(`${unitTestCount()} unit`));
  assert.ok(tableRow(devLog, 'CI').includes('GitHub Actions'));
});

test('published surface omits local-only source markers', () => {
  const hiddenDocPath = ['docs', 't' + 'eaching'].join('/');
  const hiddenDocName = 't' + 'eaching';
  const privateSourceName = 'cl' + 'ief';
  const legacyExampleName = ['legacy', 'devrel', 'example'].join('-');
  const officeSourceName = ['office', 'skills', 'source'].join('-');
  const manualName = ['skills', 'field', 'manual'].join('_');
  const resourceName = ['resource', 'index'].join('_');
  const oldPdfPrefix = ['cl' + 'ief', 'notes'].join('_');

  const terms = [
    hiddenDocPath,
    hiddenDocName,
    privateSourceName,
    legacyExampleName,
    officeSourceName,
    manualName,
    resourceName,
    oldPdfPrefix,
  ];
  const pattern = terms.map((term) => term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
  const result = gitMaybe(['grep', '-n', '-I', '-i', '-E', pattern, '--', '.']);

  assert.equal(result.status, 1, result.stdout);
});
