const NAME_TOKEN_RE = /`([a-z][a-z0-9-]*(?::[a-z][a-z0-9-]*)?)`/g;

export function extractNames(markdown) {
  const seen = new Set();
  let m;
  while ((m = NAME_TOKEN_RE.exec(markdown)) !== null) {
    const token = m[1];
    if (token.includes('/') || token.includes('.')) continue;
    if (token.startsWith('-')) continue;
    seen.add(token);
  }
  return [...seen];
}

export function classifyNames(names, registry) {
  const all = new Set();
  for (const list of Object.values(registry)) {
    if (!Array.isArray(list)) continue;
    for (const item of list) {
      if (item && item.name) all.add(item.name);
    }
  }
  const resolved = [];
  const dangling = [];
  for (const n of names) {
    if (all.has(n)) resolved.push(n);
    else dangling.push(n);
  }
  return { resolved, dangling };
}
