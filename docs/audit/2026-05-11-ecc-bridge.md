# ECC-bridge post-merge audit — findings record

> **Audited:** Post-merge state of the ECC-bridge routing system (commit range `1c28eaa..ce0c88e`).
> **Audit date:** 2026-05-11.
> **Remediation:** Commit `1bbb3b3 fix(routing): harden ECC bridge audit findings`. 31 files, +762/−729.
> **Why this doc exists:** Commit `1bbb3b3` is subject-only — its 14 distinct findings are not captured in the commit body itself. This file is the permanent record so future contributors don't have to reverse-engineer the change from the diff. Captured originally in https://github.com/Elessar617/workspace-blueprint/pull/1.

---

## 1. Validator hardening

### F1.1 — Dangling references in routing markdowns were not blocking the build

`scripts/rebuild-registry.mjs` walked `ROUTING.md` and `.claude/routing/*.md` extracting every backticked name. Names that didn't resolve in any registry were logged as informational warnings — `rebuild-registry` still exited 0.

**Fix:** `scripts/rebuild-registry.mjs:109-111` — throws `routing validation failed with N dangling reference(s)` when `totalDangling > 0`.

### F1.2 — Workspace-blueprint's own agents/skills/rules were not a registry source

References to `planner`, `implementer`, `tdd-loop`, `commit-discipline`, etc. (this repo's *native* inventory) were only resolved if they coincidentally appeared in an ECC entry. The native inventory had no first-class registry.

**Fix:** New `scripts/lib/native-scraper.mjs` produces `.claude/registry/native-inventory.json` (4 agents + 10 skills + 7 rules + 4 MCPs = 25 records). Wired into `rebuild-registry.mjs:43`.

### F1.3 — Hook profile names were unaddressable by the validator

`minimal` / `standard` / `strict` were stored as an object map keyed by name (`{ minimal: { description: ... }, ... }`), with no `name` field on each record. The `extractNames` validator couldn't see them.

**Fix:** `rebuild-registry.mjs:44-48` — emit as ordinary `{ name, kind: 'hook-profile', source: 'native' }` records, like every other inventory entry.

### F1.4 — Built-in Claude Code subagents were dangling

`general-purpose`, `Explore`, `Plan` are Claude Code built-ins referenced by the `spike` and `spec-author` branches in `scripts/route.mjs`. They were not in any registry — they would have been dangling once F1.1 made dangling references fatal.

**Fix:** `scripts/lib/harness-scraper.mjs:5-9` — `BUILTINS` constant baked into the scrape output regardless of plugin cache state.

### F1.5 — Routing markdown name drift surfaced by the now-strict validator

Five routing files + three top-level docs had name references that didn't resolve once the validator went strict.

**Fix:** Small targeted edits in `.claude/routing/{bug,build,refactor,ship,spike}.md`, `AGENTS.md`, `ROUTING.md`, `README.md`. The `refactor` branch now references `code-simplifier`; `spike` drops `brave-search` MCP (not in harness inventory on a clean install).

---

## 2. Scraper determinism & portability

### F2.1 — Harness plugin paths were absolute

`plugin_path` in `harness-skills.json` contained the operator's home directory: `/Users/.../plugins/cache/...`. Re-running `rebuild-registry` on a different machine produced a diff in the registry.

**Fix:** `scripts/lib/harness-scraper.mjs:48` — `relative(pluginsDir, skillPath).replaceAll('\\', '/')`.

### F2.2 — Multiple cached plugin versions indexed as separate skills

If the harness plugin cache had `0.1.2/` and `0.1.3/` for the same plugin, both versions' skills got indexed as if distinct. Registry counts depended on local cache cleanliness.

**Fix:** `harness-scraper.mjs:36-40` — `skillsByKey` map keyed on `marketplace/plugin/skill`, retains the highest version via a numeric `compareVersion` collator.

### F2.3 — Repo-level `.claude/settings.json` MCPs were not inventoried

`harness-scraper` only scanned `~/.claude/settings.json` for MCP definitions. The repo's *own* `.claude/settings.json` (with `filesystem`, `git`, `fetch`, `github`) was invisible to the registry.

**Fix:** `rebuild-registry.mjs:53-57` — passes `settingsPaths: [repo, home]`; scraper dedupes via `seenMcps` Set. Registry now correctly inventories all 4 project MCPs.

### F2.4 — `indexed_at` ISO timestamps in every registry record

Every record carried `indexed_at: "2026-XX-XXTXX:XX:XX.XXXZ"`. Every `rebuild-registry` run produced a diff even when nothing else changed — defeating the "registry as lockfile" model.

**Fix:** Removed from `scripts/lib/ecc-scraper.mjs` (lines 32/50/71) and `harness-scraper.mjs`. Registry is now byte-stable across runs on identical input — verified post-fix by running `rebuild-registry` and observing `git status` remains clean.

---

## 3. Routing logic

### F3.1 — Mid-task chatter clobbered cached routing

A follow-up like "yes" / "ok" / "continue" routed as `fallback` (no detected task type). The cache-merge logic then replaced the in-flight cached routing with the fallback, losing context mid-task.

**Fix:** `scripts/route.mjs:146-151` — new `isMidTaskChatter(prompt)` matches short affirmations against a regex. When the prompt is chatter, cached routing is preserved.

### F3.2 — Cache-vs-fresh precedence was backwards

`mergeWithCache` preferred cache over fresh-route on every prompt when no transition phrase was detected. That meant a new task whose prompt was a clear category match would still inherit the previous task's routing.

**Fix:** `route.mjs:155-159` — inverted. Fresh wins by default; cache only wins when (a) no transition phrase AND (b) the prompt is mid-task chatter.

### F3.3 — Office skills never auto-added to `ship` routing

The `ship` branch's spec calls for `.docx` / `.pptx` / `.xlsx` / `.pdf` skills to be added when the corresponding file extensions appear in scope. Logic was missing.

**Fix:** `route.mjs:17-22, 43-50, 115` — `OUTPUT_SKILL_BY_EXT` map + `detectOutputSkills(files)` triggered only on `detected === 'ship'`.

---

## 4. Misc

### F4.1 — Codex desktop app artifacts not ignored

`.agents/` and `.codex/` directories appear in the repo root when the Codex desktop app is run against this checkout.

**Fix:** `.gitignore` — 4 lines added.

### F4.2 — Test coverage for new logic

**Added:** `tests/unit/harness-scraper.test.mjs`, `tests/unit/native-scraper.test.mjs`. **Expanded:** `cache.test.mjs`, `route.test.mjs`, `routing-snapshots.test.mjs`.

---

## What this audit did NOT fix

The five v1 limitations in `docs/limitations-and-deferred.md §1` (auto-activation, MCP runtime enable/disable, parse-skipped ECC file, partial cross-IDE alignment, harness path portability caveat) are unchanged. Five F1–F5 future-work items remain queued.
