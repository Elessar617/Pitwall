import { readdirSync, statSync, existsSync } from 'node:fs';
import { join, extname, relative } from 'node:path';
import { spawnSync } from 'node:child_process';
import { parseMarkdown, normalizeRecord, filenameStem } from './frontmatter.mjs';

const DIR_KIND_MAP = {
  agents: 'agent',
  skills: 'skill',
  commands: 'command',
  rules: 'rule',
};

function* walkMarkdown(dir) {
  if (!existsSync(dir)) return;
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    const s = statSync(p);
    if (s.isDirectory()) yield* walkMarkdown(p);
    else if (extname(p) === '.md') yield p;
  }
}

export function getEccSha(eccPath) {
  const result = spawnSync('git', ['-C', eccPath, 'rev-parse', 'HEAD'], {
    encoding: 'utf8',
  });
  if (result.status !== 0) return null;
  return result.stdout.trim();
}

export function scrapeEcc(eccPath) {
  const eccSha = getEccSha(eccPath);
  const skipped = [];
  const out = { agents: [], skills: [], commands: [], rules: [], mcps: [] };

  for (const [subdir, kind] of Object.entries(DIR_KIND_MAP)) {
    const dirPath = join(eccPath, subdir);
    for (const file of walkMarkdown(dirPath)) {
      const parsed = parseMarkdown(file);
      if (parsed.parseError) {
        skipped.push({ file, reason: parsed.parseError });
        continue;
      }
      const record = normalizeRecord(parsed, {
        filenameStem: filenameStem(file),
        kind,
        source: 'ecc',
      });
      record.path = relative(eccPath, file);
      record.ecc_sha = eccSha;
      const bucket =
        kind === 'agent' ? 'agents'
        : kind === 'skill' ? 'skills'
        : kind === 'command' ? 'commands'
        : 'rules';
      out[bucket].push(record);
    }
  }

  const mcpDir = join(eccPath, 'mcp-configs');
  if (existsSync(mcpDir)) {
    for (const entry of readdirSync(mcpDir)) {
      const p = join(mcpDir, entry);
      if (extname(p) === '.json') {
        out.mcps.push({
          name: filenameStem(p),
          kind: 'mcp',
          source: 'ecc',
          path: relative(eccPath, p),
          description: '',
          ecc_sha: eccSha,
        });
      }
    }
  }

  return { ...out, skipped, eccSha };
}
