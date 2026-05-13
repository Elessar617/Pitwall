# v1 Limitations and Deferred Work

> Snapshot of what the ECC-bridge v1 does NOT do, and what's intentionally left for later. Kept here so a contributor (or future-you) doesn't re-discover the gaps as "bugs."
>
> Related: `docs/superpowers/specs/2026-05-11-ecc-bridge-and-routing-design.md` (§10 Resolved Decisions, §12 Future Work).

---

## 1. Acknowledged limitations in v1

### 1.1 Registry validation is strict

`scripts/rebuild-registry.mjs` validates that every backticked name in `ROUTING.md` and `.claude/routing/*.md` resolves to an entry in some `.claude/registry/*.json`. Native workspace-blueprint agents/skills/rules/MCPs are indexed into `native-inventory.json`; hook profile keys are indexed as hook-profile records; project MCPs are read from `.claude/settings.json`.

**Status:** Resolved after the post-merge audit. New dangling references fail the rebuild instead of being logged as informational warnings.

**Remaining caveat:** Harness plugin entries still describe the local operator's installed plugin set. Paths are now portable relative to the plugin cache, but another machine must install matching plugins or refresh the harness registry after setup.

### 1.2 `BLUEPRINT_HOOK_PROFILE` activation

The 4 native hooks honor the env var (`minimal` → exit 0; `standard`/`strict` → run). Activation flows two ways: `./scripts/with-profile.sh <profile> <command>` (per-task, since 2026-05-12) or `export BLUEPRINT_HOOK_PROFILE=<profile>` (shell-wide).

**Status:** Resolved. The `with-profile.sh` wrapper closes the auto-activation gap from spec §12 (F3). The auto-selector still recommends a profile in its injected context; the operator now has a one-liner to adopt it instead of typing `export`.

**Remaining caveat:** The wrapper does not currently update `.current.json`'s recommended profile from `route.mjs` output automatically; the operator chooses the profile at invocation time. If you want truly hands-off activation, that's an additional follow-up (e.g., a shell alias that reads the cache before exec'ing).

### 1.3 MCP routing is recommendation-only

`route.mjs` produces an `mcps:` list in its output, but Claude Code MCP servers are session-scoped — there's no per-task enable/disable. The selector advises; the agent uses them when relevant.

**Status:** Working as designed (spec §10.5).

**Resolution path:** Build the Option B MCP routing server (spec §12 F2) if LLM compliance with preamble-driven routing proves unreliable.

### 1.4 ECC submodule has one parse-skipped file — RESOLVED

**Status:** Resolved 2026-05-12 by bumping the ECC submodule pin from `7fa1e5b6` to `894ee039` (commit `b6695c3`). The scraper now reports `skipped: 0`.

**Original issue:** `external/ecc/agents/a11y-architect.md` at SHA `7fa1e5b6` had a duplicate YAML key — `model: sonnet` on line 4 AND `model: opus` on line 6. YAML 1.2 forbids duplicate mapping keys; `gray-matter` rejected the file and the scraper marked it skipped (defensive schema, spec §6.6).

**Upstream fix:** Already in `affaan-m/everything-claude-code` HEAD before we investigated. The maintainer removed the `model: opus` line, keeping `model: sonnet`. No upstream PR needed; the pin bump flowed the fix in.

**Lesson worth keeping:** Always check upstream `main` before opening a PR — costs ~30 seconds, prevents wrong-direction or duplicate work. My initial guess that "line 6 was the deliberate update" was wrong (upstream actually removed line 6).

### 1.5 Partial cross-IDE alignment check

The unit snapshot suite verifies that `route.mjs` emits only registry-resolvable names for the routing cases. It does not yet run each non-CC harness through the inline Markdown traversal and compare the agent's chosen inventory.

**Status:** Deterministic selector coverage exists. Real cross-IDE agent-compliance testing remains trust-based, with practical blockers — Cursor has no headless mode for CI invocation; per-IDE auth + recurring API spend; natural-language output requires structured-prompt conventions.

**Resolution paths:**
- *Shipped:* "Cleanroom CI" in §2 hardens the deterministic half (`route.mjs` + registries + bootstrap) by running on every push/PR. Catches the part of F1 that can be verified without invoking agents.
- *Deferred:* Full agent-compliance testing remains trigger-gated to observed non-CC routing drift (see §2 below).

---

## 2. Tracked items (active, deferred, shipped)

Reorganized 2026-05-12 from the original spec §12 single-list view because reality moved on: F3 shipped, F1's literal scope hit practical blockers, and new items had emerged in conversation. F-IDs preserved for backreference to commits and the original spec.

### Active or planned

*(none currently planned — all items shipped or trigger-gated; see below)*

### Deferred (trigger-gated; do not implement until trigger fires)

| Item | Trigger | Notes |
|------|---------|-------|
| Cross-IDE agent compliance check (formerly full F1) | "Observed non-CC routing drift" | Spec §12 wanted CI invoking each non-CC harness on snapshot prompts and diffing the agent's narrowing against `route.mjs`. Practical blocker: Cursor has no headless mode. Cost: recurring API spend × N IDEs × M prompts per CI run. Cleanroom CI (above) covers the deterministic half; full agent-compliance remains deferred. |
| F2: Custom MCP routing server (Option B) | "If LLM compliance with preamble proves unreliable in Cursor/Codex/Gemini" | Trigger unchanged. YAGNI per spec. |
| F4: `/refresh-routing` slash command | "If we observe cache staleness in real use" | UX nice-to-have. Cache invalidation via transition phrases works; no observed problems. |
| F5: Multi-repo support (additional submodules) | "When we want to bring in `obra/superpowers` (or similar) as a second source" | `rebuild-registry.mjs`'s source-list mechanism generalizes naturally. |

### Shipped

| Item | Shipped | Reference |
|------|---------|-----------|
| F3: BLUEPRINT_HOOK_PROFILE auto-activation | 2026-05-12 | `scripts/with-profile.sh` (commit `80fc73f`). See §1.2 above. |
| Cleanroom CI (formerly F1 Tier A) | 2026-05-12 | `.github/workflows/ci.yml` (commit `353e72f`); first real catch was the dangling-references-on-empty-harness bug, fixed in `103893e`. |
| SKILLS.md consolidation (vendoring + refresh + discovery surface) | 2026-05-12 | Three slices: 4 harness skills vendored under `.claude/skills/<name>/` with MIT attribution in `THIRD_PARTY_LICENSES.md` (`103893e`); `scripts/refresh-vendored.mjs` lifecycle (`a63dc04`); repo-root `SKILLS.md` as human-readable inventory (`913179a`). |
| ECC submodule pin bump | 2026-05-12 | Bumped pin from `7fa1e5b6` to `894ee039` (108 commits ahead). Inventory diff: +13 agents, +77 skills, +7 commands, 1→0 skipped (a11y-architect resolved). All 7 routing files validate cleanly against the new registry. Commit `b6695c3`. Resolves the §1.4 limitation. |

---

## 3. Open questions resolved during spec review (now closed)

All five "open questions" from the original spec §10 were resolved before implementation. Captured here for posterity:

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Frontmatter normalization | Defensive schema in `scripts/lib/frontmatter.mjs` — required vs optional fields, type coercion, parse-error catch-and-skip |
| Q2 | Slash command description fallback | 3-tier: frontmatter → first paragraph → filename derivation |
| Q3 | `route.mjs` runtime | ESM `.mjs` (Node 18+); `.mjs` extension per-file, no `"type": "module"` in package.json |
| Q4 | Hook profile mechanism | Pulled from §12 future-work into v1; 3-line gate in each of the 4 hooks, env-var driven |
| Q5 | MCP server activation per task | Recommendation-only; no dynamic enable/disable |

---

## 4. Pragmatic deviations from the plan during execution

These were operational choices made by the implementer during the 39-task run; they don't change the design but are worth recording.

- **`scripts/lib/ecc-scraper.mjs` path bug.** Plan's `.slice(eccPath.length)` was buggy when `eccPath` was relative (e.g., `./external/ecc`); fixed to `path.relative(eccPath, file)` in commit `8af6b20`.
- **`package.json` `test:unit` script.** Plan used `node --test tests/unit/`; Node 25's `--test` doesn't auto-discover `.test.mjs` files in directory mode. Fixed to explicit glob `node --test tests/unit/*.test.mjs` in commit `9a9e972`.
- **`go-patterns` / `nextjs-patterns` name drift.** Final code reviewer caught these as real dangling references in the original validator. Renamed to `golang-patterns`; removed `nextjs-patterns` entirely (no ECC equivalent). Commit `7a47ebe`.

---

## 5. Things that are NOT limitations (by design)

So they're not re-investigated:

- **Registry JSONs are committed.** They're snapshots like a lockfile; `bootstrap.sh` re-runs `rebuild-registry` to refresh from the local ECC submodule + local harness on first checkout. The committed copy lets a fresh clone work immediately even before bootstrap.
- **Worktree's `.serena/` was not committed.** Per-user IDE state; gitignored. See commit history.
- **Update scripts stage but don't auto-commit.** Matches the operator's established preference for surgical commits.
- **No tests for the deterministic-module/agent-inline-routing alignment.** Listed in §1.5 above; trust-based for v1, CI job for later.

---

*Last updated: 2026-05-12 — refreshed tracked-items list (§2 restructured into Active/Deferred/Shipped sub-tables; §1.5 updated to reflect Cleanroom CI as the shipped deterministic guard). Maintain alongside the spec, plan, and `docs/development-log.md` whenever items move between buckets.*
