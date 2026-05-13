import { readFileSync } from 'node:fs';
import { basename, extname } from 'node:path';
import matter from 'gray-matter';

export function parseMarkdown(filePath) {
  const raw = readFileSync(filePath, 'utf8');
  let frontmatter = {};
  let body = raw;
  let parseError = null;
  try {
    const parsed = matter(raw);
    frontmatter = parsed.data || {};
    body = parsed.content || '';
  } catch (e) {
    parseError = e.message;
    const m = raw.match(/^---\n[\s\S]*?\n---\n([\s\S]*)$/);
    if (m) body = m[1];
  }
  const firstParagraph = body.split(/\n\s*\n/)[0].trim().slice(0, 200);
  return { frontmatter, body, firstParagraph, parseError };
}

const toArray = (v) => {
  if (v == null) return [];
  if (Array.isArray(v)) return v;
  if (typeof v === 'string' && v.includes(',')) {
    return v.split(',').map((item) => item.trim()).filter(Boolean);
  }
  return [v];
};

export function normalizeRecord(parsed, { filenameStem, kind, source }) {
  const fm = parsed.frontmatter || {};
  return {
    name: fm.name || filenameStem,
    kind,
    source,
    description: (fm.description || parsed.firstParagraph || '').trim(),
    languages: toArray(fm.languages),
    tools: toArray(fm.tools),
    model: fm.model || null,
  };
}

export function filenameStem(filePath) {
  return basename(filePath, extname(filePath));
}
