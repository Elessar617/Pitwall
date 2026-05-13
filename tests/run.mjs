import { spawnSync } from 'node:child_process';
import { readdirSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
let failures = 0;

console.log('--- unit tests ---');
const unitDir = join(__dirname, 'unit');
const unitFiles = existsSync(unitDir)
  ? readdirSync(unitDir).filter((f) => f.endsWith('.test.mjs')).map((f) => join(unitDir, f))
  : [];
const unit = spawnSync('node', ['--test', ...unitFiles], { stdio: 'inherit' });
if (unit.status !== 0) failures++;

console.log('\n--- hook tests ---');
const hookDir = join(__dirname, 'hook');
if (existsSync(hookDir)) {
  for (const f of readdirSync(hookDir)) {
    if (!f.endsWith('.sh')) continue;
    const r = spawnSync('bash', [join(hookDir, f)], { stdio: 'inherit' });
    if (r.status !== 0) failures++;
  }
}

console.log('\n--- integration tests ---');
const intDir = join(__dirname, 'integration');
if (existsSync(intDir)) {
  for (const f of readdirSync(intDir)) {
    if (!f.endsWith('.sh')) continue;
    const r = spawnSync('bash', [join(intDir, f)], { stdio: 'inherit' });
    if (r.status !== 0) failures++;
  }
}

console.log(`\n--- summary: ${failures} failure(s) ---`);
process.exit(failures === 0 ? 0 : 1);
