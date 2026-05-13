// refresh-vendored.mjs — refresh `.claude/skills/<name>/SKILL.md` files marked
// with `vendored_from:` frontmatter from the local Claude Code plugin cache.
//
// Usage:
//   node scripts/refresh-vendored.mjs    # walks all vendored skills, prints status
//
// Matches the operator pattern of update-ecc.sh / refresh-harness.sh: pulls the
// freshest content available locally, writes changes to the working tree,
// does NOT auto-commit. The operator reviews `git diff` before committing.
//
// What it does for each skill in .claude/skills/<name>/SKILL.md:
//   1. Parse frontmatter. If no `vendored_from:` field, skip.
//   2. Parse `vendored_from: "<plugin-cache-path>@<version>"`.
//   3. Look in ~/.claude/plugins/cache/<plugin-cache-path>/ for available versions.
//   4. Pick the highest version (numeric/semver-ish sort).
//   5. Read the upstream SKILL.md at that version.
//   6. If local matches upstream byte-for-byte: status "up-to-date".
//   7. Otherwise: overwrite local with upstream body + frontmatter, but preserve
//      our `vendored_from:` (updated version) and `license:` fields.
//
// Status codes returned:
//   - 'version-bumped'        — upstream version is newer than what was vendored
//   - 'content-changed'       — same version, upstream content differs
//   - 'up-to-date'            — nothing to do
//   - 'upstream-not-found'    — plugin not in local cache (skipped, not an error)
//   - 'invalid-vendored-from' — frontmatter could not be parsed

import { existsSync, readdirSync, readFileSync, writeFileSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';
import { isDeepStrictEqual } from 'node:util';
import matter from 'gray-matter';

const DEFAULT_PLUGIN_CACHE = join(homedir(), '.claude', 'plugins', 'cache');

function findLatestVersion(pluginDir) {
  if (!existsSync(pluginDir)) return null;
  const entries = readdirSync(pluginDir)
    .filter((v) => !v.startsWith('.'))
    .filter((v) => {
      try {
        return statSync(join(pluginDir, v)).isDirectory();
      } catch {
        return false;
      }
    });
  if (entries.length === 0) return null;
  entries.sort((a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' }));
  return entries[entries.length - 1];
}

function updateThirdPartyLicenseVersion(skillsDir, pluginPath, version) {
  const licenseFile = join(skillsDir, 'THIRD_PARTY_LICENSES.md');
  if (!existsSync(licenseFile)) return false;

  const pluginName = pluginPath.split('/').at(-1);
  const lines = readFileSync(licenseFile, 'utf8').split('\n');
  const headingIndex = lines.findIndex((line) => line.startsWith('## ') && line.includes(pluginName));
  if (headingIndex === -1) return false;

  const nextHeadingIndex = lines.findIndex((line, index) => index > headingIndex && line.startsWith('## '));
  const endIndex = nextHeadingIndex === -1 ? lines.length : nextHeadingIndex;
  for (let i = headingIndex + 1; i < endIndex; i++) {
    if (lines[i].startsWith('- **Version vendored:**')) {
      const nextLine = `- **Version vendored:** ${version}`;
      if (lines[i] === nextLine) return false;
      lines[i] = nextLine;
      writeFileSync(licenseFile, lines.join('\n'));
      return true;
    }
  }

  return false;
}

export function refreshVendoredSkills(repoRoot, pluginCacheDir = DEFAULT_PLUGIN_CACHE) {
  const skillsDir = join(repoRoot, '.claude', 'skills');
  const results = [];
  if (!existsSync(skillsDir)) return results;

  for (const entry of readdirSync(skillsDir)) {
    const skillFile = join(skillsDir, entry, 'SKILL.md');
    if (!existsSync(skillFile)) continue;

    const localContent = readFileSync(skillFile, 'utf8');
    const localParsed = matter(localContent);
    if (!localParsed.data.vendored_from) continue;

    const m = String(localParsed.data.vendored_from).match(/^(.+)@(.+)$/);
    if (!m) {
      results.push({ name: entry, status: 'invalid-vendored-from' });
      continue;
    }
    const [, pluginPath, currentVersion] = m;

    const pluginDir = join(pluginCacheDir, pluginPath);
    const latest = findLatestVersion(pluginDir);
    if (!latest) {
      results.push({ name: entry, status: 'upstream-not-found' });
      continue;
    }

    const upstreamFile = join(pluginDir, latest, 'skills', entry, 'SKILL.md');
    if (!existsSync(upstreamFile)) {
      results.push({ name: entry, status: 'upstream-not-found' });
      continue;
    }

    const upstreamContent = readFileSync(upstreamFile, 'utf8');
    const upstreamParsed = matter(upstreamContent);

    // Semantic comparison: would running this script produce any change?
    // Compute what we WOULD write, compare to what's there. This ignores
    // format-only differences (gray-matter's canonical YAML output may differ
    // from how the file was originally authored — quoting style, folded long
    // strings, key order). Handles the edge case where upstream itself has a
    // `license:` frontmatter field (e.g., karpathy-guidelines): we don't strip
    // local's license unconditionally; we just check semantic equality of the
    // computed frontmatter against what's already on disk.
    const newFm = {
      ...upstreamParsed.data,
      vendored_from: `${pluginPath}@${latest}`,
      license: localParsed.data.license || upstreamParsed.data.license || 'MIT',
    };
    const versionMatches = currentVersion === latest;
    const bodyMatches = upstreamParsed.content.trim() === localParsed.content.trim();
    const fmMatches = isDeepStrictEqual(newFm, localParsed.data);

    if (versionMatches && bodyMatches && fmMatches) {
      results.push({ name: entry, status: 'up-to-date', version: latest });
    } else {
      const newContent = matter.stringify(upstreamParsed.content, newFm);
      writeFileSync(skillFile, newContent);
      const status = !versionMatches ? 'version-bumped' : 'content-changed';
      const licenseUpdated = status === 'version-bumped'
        ? updateThirdPartyLicenseVersion(skillsDir, pluginPath, latest)
        : false;
      results.push({
        name: entry,
        status,
        version: latest,
        previousVersion: currentVersion,
        ...(licenseUpdated ? { licenseUpdated: true } : {}),
      });
    }
  }

  return results;
}

// CLI mode
if (import.meta.url === `file://${process.argv[1]}`) {
  const __dirname = dirname(fileURLToPath(import.meta.url));
  const REPO_ROOT = dirname(__dirname);
  const results = refreshVendoredSkills(REPO_ROOT);
  if (results.length === 0) {
    console.log('[refresh-vendored] no vendored skills found (no SKILL.md with `vendored_from:` frontmatter)');
  }
  let bumped = 0;
  let changed = 0;
  let upToDate = 0;
  let missing = 0;
  for (const r of results) {
    if (r.status === 'version-bumped') {
      console.log(`[refresh-vendored] ${r.name}: version-bumped ${r.previousVersion} → ${r.version}`);
      bumped++;
    } else if (r.status === 'content-changed') {
      console.log(`[refresh-vendored] ${r.name}: content-changed at ${r.version}`);
      changed++;
    } else if (r.status === 'up-to-date') {
      console.log(`[refresh-vendored] ${r.name}: up-to-date at ${r.version}`);
      upToDate++;
    } else if (r.status === 'upstream-not-found') {
      console.warn(`[refresh-vendored] ${r.name}: upstream not found in local plugin cache; skipped`);
      missing++;
    } else if (r.status === 'invalid-vendored-from') {
      console.warn(`[refresh-vendored] ${r.name}: invalid vendored_from frontmatter; skipped`);
    }
  }
  if (bumped > 0 || changed > 0) {
    console.log(`[refresh-vendored] ${bumped} bumped, ${changed} content-changed, ${upToDate} up-to-date, ${missing} missing — review with: git diff .claude/skills/`);
  } else {
    console.log(`[refresh-vendored] ${upToDate} up-to-date, ${missing} missing — nothing to stage`);
  }
}
