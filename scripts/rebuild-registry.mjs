import { readFileSync, writeFileSync, mkdirSync, existsSync, renameSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';
import { scrapeEcc } from './lib/ecc-scraper.mjs';
import { scrapeHarness } from './lib/harness-scraper.mjs';
import { scrapeNative } from './lib/native-scraper.mjs';
import { extractNames, classifyNames } from './lib/validate.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');
const REGISTRY_DIR = join(REPO_ROOT, '.claude', 'registry');
const ROUTING_DIR = join(REPO_ROOT, '.claude', 'routing');
const ROUTING_MD = join(REPO_ROOT, 'ROUTING.md');

const HARNESS_ONLY = process.argv.includes('--harness-only');

function resolveEccPath() {
  const cfg = JSON.parse(readFileSync(join(REGISTRY_DIR, 'ecc-config.json'), 'utf8'));
  if (process.env[cfg.env_override_key]) return process.env[cfg.env_override_key];
  return cfg.ecc_path_default.replace('${REPO_ROOT}', REPO_ROOT);
}

function writeJsonAtomic(path, data) {
  mkdirSync(dirname(path), { recursive: true });
  const tmp = path + '.tmp';
  writeFileSync(tmp, JSON.stringify(data, null, 2) + '\n');
  renameSync(tmp, path);
}

async function main() {
  let eccResult = { agents: [], skills: [], commands: [], rules: [], mcps: [], skipped: [] };

  if (!HARNESS_ONLY) {
    const eccPath = resolveEccPath();
    console.log(`[rebuild-registry] ECC path: ${eccPath}`);
    if (existsSync(eccPath)) {
      eccResult = scrapeEcc(eccPath);
      console.log(`[rebuild-registry] ECC: ${eccResult.agents.length} agents, ${eccResult.skills.length} skills, ${eccResult.commands.length} commands, ${eccResult.mcps.length} mcps, ${eccResult.skipped.length} skipped`);
    } else {
      console.warn(`[rebuild-registry] ECC path missing: ${eccPath} - skipping ECC scrape`);
    }
  }

  const native = scrapeNative(REPO_ROOT);
  const hookProfiles = [
    { name: 'minimal', kind: 'hook-profile', source: 'native', description: 'Hooks no-op; exit 0 immediately.' },
    { name: 'standard', kind: 'hook-profile', source: 'native', description: 'Current hook behavior (default).' },
    { name: 'strict', kind: 'hook-profile', source: 'native', description: 'Current behavior plus future stricter variants.' },
  ];
  const harness = scrapeHarness({
    settingsPaths: [
      join(REPO_ROOT, '.claude', 'settings.json'),
      join(homedir(), '.claude', 'settings.json'),
    ],
  });
  console.log(`[rebuild-registry] Harness: ${harness.skills.length} skills, ${harness.mcps.length} mcps`);
  console.log(`[rebuild-registry] Native: ${native.length} items`);

  if (!HARNESS_ONLY) {
    writeJsonAtomic(join(REGISTRY_DIR, 'ecc-agents.json'), eccResult.agents);
    writeJsonAtomic(join(REGISTRY_DIR, 'ecc-skills.json'), eccResult.skills);
    writeJsonAtomic(join(REGISTRY_DIR, 'ecc-commands.json'), eccResult.commands);
    writeJsonAtomic(join(REGISTRY_DIR, 'ecc-mcps.json'), eccResult.mcps);
    writeJsonAtomic(join(REGISTRY_DIR, 'ecc-language-rules.json'), eccResult.rules);
    writeJsonAtomic(join(REGISTRY_DIR, 'ecc-hook-profiles.json'), hookProfiles);
  }
  writeJsonAtomic(join(REGISTRY_DIR, 'native-inventory.json'), native);
  writeJsonAtomic(join(REGISTRY_DIR, 'harness-skills.json'), harness.skills);
  writeJsonAtomic(join(REGISTRY_DIR, 'harness-mcps.json'), harness.mcps);
  writeJsonAtomic(join(REGISTRY_DIR, 'harness-builtins.json'), harness.builtins);

  const fullRegistry = {
    agents: HARNESS_ONLY
      ? (existsSync(join(REGISTRY_DIR, 'ecc-agents.json')) ? JSON.parse(readFileSync(join(REGISTRY_DIR, 'ecc-agents.json'), 'utf8')) : [])
      : eccResult.agents,
    skills: [
      ...(HARNESS_ONLY ? (existsSync(join(REGISTRY_DIR, 'ecc-skills.json')) ? JSON.parse(readFileSync(join(REGISTRY_DIR, 'ecc-skills.json'), 'utf8')) : []) : eccResult.skills),
      ...harness.skills,
    ],
    commands: HARNESS_ONLY
      ? (existsSync(join(REGISTRY_DIR, 'ecc-commands.json')) ? JSON.parse(readFileSync(join(REGISTRY_DIR, 'ecc-commands.json'), 'utf8')) : [])
      : eccResult.commands,
    mcps: [
      ...(HARNESS_ONLY ? (existsSync(join(REGISTRY_DIR, 'ecc-mcps.json')) ? JSON.parse(readFileSync(join(REGISTRY_DIR, 'ecc-mcps.json'), 'utf8')) : []) : eccResult.mcps),
      ...harness.mcps,
    ],
    builtins: harness.builtins,
    native,
    hookProfiles,
    rules: HARNESS_ONLY
      ? (existsSync(join(REGISTRY_DIR, 'ecc-language-rules.json')) ? JSON.parse(readFileSync(join(REGISTRY_DIR, 'ecc-language-rules.json'), 'utf8')) : [])
      : eccResult.rules,
  };

  const filesToValidate = [];
  if (existsSync(ROUTING_MD)) filesToValidate.push(ROUTING_MD);
  if (existsSync(ROUTING_DIR)) {
    for (const f of readdirSync(ROUTING_DIR)) {
      if (f.endsWith('.md')) filesToValidate.push(join(ROUTING_DIR, f));
    }
  }
  let totalDangling = 0;
  for (const file of filesToValidate) {
    const names = extractNames(readFileSync(file, 'utf8'));
    const { dangling } = classifyNames(names, fullRegistry);
    if (dangling.length) {
      console.warn(`[rebuild-registry] ${file}: dangling references: ${dangling.join(', ')}`);
      totalDangling += dangling.length;
    }
  }
  if (totalDangling > 0) {
    throw new Error(`routing validation failed with ${totalDangling} dangling reference(s)`);
  }
  if (totalDangling === 0 && filesToValidate.length > 0) {
    console.log(`[rebuild-registry] All ${filesToValidate.length} routing files validated cleanly.`);
  }

  console.log('[rebuild-registry] Done.');
}

main().catch((e) => {
  console.error('[rebuild-registry] FAILED:', e.stack || e.message);
  process.exit(1);
});
