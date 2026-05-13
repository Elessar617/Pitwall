import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, extname } from 'node:path';
import { parseMarkdown, normalizeRecord, filenameStem } from './frontmatter.mjs';

function readMarkdownRecord(file, repoRoot, { kind, name }) {
  const parsed = parseMarkdown(file);
  const record = normalizeRecord(parsed, {
    filenameStem: name || filenameStem(file),
    kind,
    source: 'native',
  });
  record.path = relative(repoRoot, file).replaceAll('\\', '/');
  return record;
}

function pushIfMarkdown(out, file, repoRoot, opts) {
  if (existsSync(file) && extname(file) === '.md') out.push(readMarkdownRecord(file, repoRoot, opts));
}

export function scrapeNative(repoRoot) {
  const out = [];

  const agentsDir = join(repoRoot, '.claude', 'agents');
  if (existsSync(agentsDir)) {
    for (const entry of readdirSync(agentsDir)) {
      const file = join(agentsDir, entry);
      if (!statSync(file).isFile() || extname(file) !== '.md') continue;
      const stem = filenameStem(file).replace(/-agent$/, '');
      pushIfMarkdown(out, file, repoRoot, { kind: 'agent', name: stem });
    }
  }

  const skillsDir = join(repoRoot, '.claude', 'skills');
  if (existsSync(skillsDir)) {
    for (const entry of readdirSync(skillsDir)) {
      const file = join(skillsDir, entry, 'SKILL.md');
      pushIfMarkdown(out, file, repoRoot, { kind: 'skill', name: entry });
    }
  }

  const rulesDir = join(repoRoot, '.claude', 'rules');
  if (existsSync(rulesDir)) {
    for (const entry of readdirSync(rulesDir)) {
      const file = join(rulesDir, entry);
      if (!statSync(file).isFile()) continue;
      pushIfMarkdown(out, file, repoRoot, { kind: 'rule' });
    }
  }

  const settingsPath = join(repoRoot, '.claude', 'settings.json');
  if (existsSync(settingsPath)) {
    try {
      const settings = JSON.parse(readFileSync(settingsPath, 'utf8'));
      for (const [name, config] of Object.entries(settings.mcpServers || {})) {
        out.push({
          name,
          kind: 'mcp',
          source: 'native',
          command: config.command || '',
          description: '',
        });
      }
    } catch (e) {
      console.warn(`[native-scraper] could not parse ${settingsPath}: ${e.message}`);
    }
  }

  return out;
}
