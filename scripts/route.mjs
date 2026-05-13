const TASK_RULES = [
  { branch: 'build', keywords: ['add ', 'implement', 'feature', 'build ', 'create '], profile: 'standard' },
  { branch: 'bug', keywords: ['fix', 'bug', 'broken', 'crash'], profile: 'standard' },
  { branch: 'refactor', keywords: ['refactor', 'migrate', 'rename', 'restructure', 'cleanup'], profile: 'standard' },
  { branch: 'spike', keywords: ['investigate', 'spike', 'explore', 'prototype'], profile: 'minimal' },
  { branch: 'spec-author', keywords: ['rfc', 'adr', 'design ', 'spec ', 'brief', 'propose'], profile: 'minimal' },
  { branch: 'ship', keywords: ['release', 'ship', 'changelog', 'publish', 'cut a v'], profile: 'strict' },
];

const LANGUAGE_BY_EXT = {
  '.py': 'python', '.go': 'go', '.ts': 'typescript', '.tsx': 'typescript',
  '.js': 'javascript', '.jsx': 'javascript', '.java': 'java', '.kt': 'kotlin',
  '.cpp': 'cpp', '.cc': 'cpp', '.h': 'cpp', '.hpp': 'cpp', '.cs': 'csharp',
  '.dart': 'dart', '.rs': 'rust', '.rb': 'ruby', '.php': 'php', '.swift': 'swift',
};

const OUTPUT_SKILL_BY_EXT = {
  '.docx': 'docx',
  '.pptx': 'pptx',
  '.xlsx': 'xlsx',
  '.pdf': 'pdf',
};

export function detectTaskType(prompt) {
  const lower = prompt.toLowerCase();
  for (const rule of TASK_RULES) {
    for (const kw of rule.keywords) {
      if (lower.includes(kw)) return rule.branch;
    }
  }
  return null;
}

export function detectLanguages(files) {
  const langs = new Set();
  for (const f of files) {
    const ext = '.' + f.split('.').pop();
    if (LANGUAGE_BY_EXT[ext]) langs.add(LANGUAGE_BY_EXT[ext]);
  }
  return [...langs];
}

export function detectOutputSkills(files) {
  const skills = new Set();
  for (const f of files) {
    const ext = '.' + f.split('.').pop();
    if (OUTPUT_SKILL_BY_EXT[ext]) skills.add(OUTPUT_SKILL_BY_EXT[ext]);
  }
  return [...skills];
}

const BRANCH_BASE = {
  build: { agents: ['planner', 'implementer', 'reviewer', 'adversary'], skills: ['tdd-loop'], rules: ['all'], mcps: ['filesystem', 'git'] },
  bug: { agents: ['implementer', 'reviewer'], skills: ['bug-investigation', 'tdd-loop', 'systematic-debugging'], commands: ['/build-fix'], rules: ['all'], mcps: ['filesystem', 'git'] },
  refactor: { agents: ['planner', 'implementer', 'reviewer', 'adversary', 'refactor-cleaner', 'code-simplifier'], skills: ['tdd-loop', 'karpathy-guidelines'], rules: ['all'], mcps: ['filesystem', 'git'] },
  spike: { agents: ['general-purpose', 'Explore', 'code-explorer'], skills: ['spike-protocol', 'data-analysis'], rules: ['portability-discipline'], mcps: ['filesystem', 'fetch'] },
  'spec-author': { agents: ['planner', 'architect', 'Plan'], skills: ['spec-authoring', 'writing-plans', 'brainstorming'], rules: ['portability-discipline', 'commit-discipline'], mcps: ['filesystem', 'fetch'] },
  ship: { agents: ['reviewer', 'adversary', 'doc-updater'], skills: [], rules: ['all'], mcps: ['filesystem', 'git', 'github'] },
  fallback: { agents: ['planner', 'implementer', 'reviewer', 'adversary'], skills: ['tdd-loop'], rules: ['all'], mcps: ['filesystem', 'git'] },
};

const LANGUAGE_ADDITIONS = {
  build: {
    python: { agents: ['python-reviewer'], skills: ['python-patterns'] },
    go: { agents: ['go-reviewer', 'go-build-resolver'], skills: ['golang-patterns'] },
    typescript: { agents: ['typescript-reviewer'], skills: [] },
    java: { agents: ['java-reviewer', 'java-build-resolver'], skills: [] },
    kotlin: { agents: ['kotlin-reviewer', 'kotlin-build-resolver'], skills: [] },
    cpp: { agents: ['cpp-reviewer', 'cpp-build-resolver'], skills: [] },
    csharp: { agents: ['csharp-reviewer'], skills: [] },
    dart: { agents: ['dart-build-resolver', 'flutter-reviewer'], skills: [] },
  },
  bug: {
    python: { agents: ['python-reviewer'] },
    go: { agents: ['go-reviewer', 'go-build-resolver'] },
    typescript: { agents: ['typescript-reviewer'] },
    java: { agents: ['java-reviewer', 'java-build-resolver'] },
    kotlin: { agents: ['kotlin-reviewer', 'kotlin-build-resolver'] },
    cpp: { agents: ['cpp-reviewer', 'cpp-build-resolver'] },
  },
  refactor: {
    python: { agents: ['python-reviewer'], skills: ['python-patterns'] },
    go: { agents: ['go-reviewer'], skills: ['golang-patterns'] },
    typescript: { agents: ['typescript-reviewer'] },
    java: { agents: ['java-reviewer'] },
    kotlin: { agents: ['kotlin-reviewer'] },
  },
};

const BRANCH_TO_PROFILE = {
  build: 'standard', bug: 'standard', refactor: 'standard',
  spike: 'minimal', 'spec-author': 'minimal', ship: 'strict',
  fallback: 'standard',
};

export function route({ prompt, files_in_scope = [], registry = {} }) {
  const detected = detectTaskType(prompt) || 'fallback';
  const langs = detectLanguages(files_in_scope);
  const outputSkills = detected === 'ship' ? detectOutputSkills(files_in_scope) : [];

  const base = BRANCH_BASE[detected] || BRANCH_BASE.fallback;
  let agents = [...base.agents];
  let skills = [...(base.skills || [])];
  let commands = [...(base.commands || [])];
  let mcps = [...(base.mcps || [])];
  const rules = [...(base.rules || [])];

  const langAdds = LANGUAGE_ADDITIONS[detected] || {};
  for (const lang of langs) {
    if (langAdds[lang]) {
      if (langAdds[lang].agents) agents.push(...langAdds[lang].agents);
      if (langAdds[lang].skills) skills.push(...langAdds[lang].skills);
    }
  }
  skills.push(...outputSkills);

  agents = [...new Set(agents)];
  skills = [...new Set(skills)];
  commands = [...new Set(commands)];
  mcps = [...new Set(mcps)];

  return {
    branch: detected,
    agents,
    skills,
    commands,
    mcps,
    rules,
    hook_profile: BRANCH_TO_PROFILE[detected],
    languages_detected: langs,
    transition_detected: false,
  };
}

const TRANSITION_PHRASES = [
  /\bnow\s+let'?s\b/i,
  /\bswitch\s+to\b/i,
  /\bactually[,\s]/i,
  /\bpivot\s+to\b/i,
];

export function detectTransition(prompt) {
  return TRANSITION_PHRASES.some((re) => re.test(prompt));
}

const CHATTER_RE = /^(yes|yep|yeah|ok|okay|sure|do that|continue|go ahead|sounds good|explain more|tell me more|thanks|thank you)\b/i;

export function isMidTaskChatter(prompt) {
  const trimmed = prompt.trim();
  if (!trimmed) return false;
  if (trimmed.length > 80) return false;
  return CHATTER_RE.test(trimmed);
}

export function mergeWithCache(cache, fresh, transitionDetected, prompt = '') {
  if (transitionDetected || !cache) return fresh;
  if (fresh.branch === 'fallback' && isMidTaskChatter(prompt)) return cache;
  return fresh;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const promptIdx = args.indexOf('--prompt');
  const prompt = promptIdx >= 0 ? args[promptIdx + 1] : '';
  if (!prompt) process.exit(0);

  const fs = await import('node:fs');
  const { join, dirname } = await import('node:path');
  const { fileURLToPath } = await import('node:url');
  const __dirname = dirname(fileURLToPath(import.meta.url));
  const REPO_ROOT = join(__dirname, '..');
  const REG = join(REPO_ROOT, '.claude', 'registry');
  const CACHE = join(REPO_ROOT, '.claude', 'routing', '.current.json');

  const safe = (f) => {
    try { return JSON.parse(fs.readFileSync(join(REG, f), 'utf8')); }
    catch { return []; }
  };
  const registry = {
    agents: safe('ecc-agents.json'),
    skills: [...safe('ecc-skills.json'), ...safe('harness-skills.json')],
    commands: safe('ecc-commands.json'),
    mcps: [...safe('ecc-mcps.json'), ...safe('harness-mcps.json')],
  };

  let cache = null;
  try { cache = JSON.parse(fs.readFileSync(CACHE, 'utf8')); } catch {}
  const transition = detectTransition(prompt);
  const fresh = route({ prompt, files_in_scope: [], registry });
  const final = mergeWithCache(cache, fresh, transition, prompt);

  try {
    fs.mkdirSync(dirname(CACHE), { recursive: true });
    fs.writeFileSync(CACHE, JSON.stringify(final, null, 2));
  } catch {}

  const usedCache = final === cache;
  const tag = transition ? ' [transition]' : (usedCache ? ' [cached]' : '');
  const out = [
    `ROUTING: branch=${final.branch} profile=${final.hook_profile} langs=${(final.languages_detected || []).join(',') || 'none'}${tag}`,
    `agents: ${final.agents.join(', ')}`,
    `skills: ${final.skills.join(', ')}`,
    final.commands?.length ? `commands: ${final.commands.join(', ')}` : '',
    `mcps: ${final.mcps.join(', ')}`,
  ].filter(Boolean).join('\n');
  console.log(out);
}
