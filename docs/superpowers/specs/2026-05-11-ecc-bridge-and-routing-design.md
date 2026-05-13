# ECC Bridge and Cross-IDE Auto-Routing — Design

**Status:** Draft (awaiting user review)
**Date:** 2026-05-11
**Repo:** `Elessar617/workspace-blueprint` (private)
**Related:** [`affaan-m/everything-claude-code`](https://github.com/affaan-m/everything-claude-code) (external; consumed via git submodule)

---

## 1. Summary

This spec describes how to integrate the `workspace-blueprint` repo with the `everything-claude-code` (ECC) repo to produce a hybrid setup that:

1. Keeps both repos clean and separately versioned, with ECC included as a git submodule under `external/ecc/`.
2. Adds a markdown decision-tree routing layer (`ROUTING.md` + per-branch files) that the agent consults on every prompt to narrow which agents, skills, slash commands, MCPs, hook profiles, and language-specific rule sets are relevant.
3. Works across Claude Code, Codex, Cursor, Gemini CLI, and OpenCode via per-IDE preamble files that all point at the same `ROUTING.md`.
4. Adds a Claude Code–specific `UserPromptSubmit` hook for token-efficient out-of-band routing, with graceful degradation to preamble-driven routing where the hook is unavailable.
5. Indexes ECC content, harness-installed plugins/MCPs, and workspace-blueprint native content into generated JSON registries under `.claude/registry/`.
6. Is pullable as a single private GitHub repo (`git clone --recursive` + `./scripts/bootstrap.sh`) on any machine.

The integration is strictly additive to `workspace-blueprint`: no existing file is moved or removed; one file (`CLAUDE.md`) gets a single-line addition. The blueprint's 3-layer routing, `spec/lab/build/ship` workspaces, 4-agent loop, and portability rules are preserved.

---

## 2. Motivation

`workspace-blueprint` provides a *workflow chassis* (token-budgeted 3-layer routing, numbered iterations, a 4-agent review loop, portability discipline) optimized for software development. It ships 4 native agents, 10 skills, 5 rules, and 4 hooks.

`everything-claude-code` (ECC) provides *content and breadth* (48 agents, 185 skills, 68 slash commands, per-language reviewers and build-resolvers, multi-IDE configs for 8+ harnesses, hook-profile gating, etc.) optimized for cross-harness operator workflows.

The two are complementary in shape rather than overlapping. The goal is to combine them so that:

- The blueprint's chassis stays as the operator's primary mental model.
- ECC's content becomes addressable through the chassis without bloating the blueprint repo or requiring the operator to remember the full inventory.
- A markdown decision tree picks the right subset for each task automatically, with the agent traversing it on every prompt.

Operating sub-goal: the operator should be able to clone the hybrid from a private GitHub repo to any machine and have everything work after one bootstrap command.

---

## 3. Key Decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Integration shape | **Bridge** (both repos stay separate) | Preserves the blueprint's portability discipline and ECC's update cadence. Reversible. |
| 2 | ECC location on disk | **Git submodule at `external/ecc/`** | Single `git clone --recursive`; version-pinned via submodule SHA; deliberate upstream bumps. |
| 3 | Distribution model | **Private GitHub repo `Elessar617/workspace-blueprint`** + `scripts/bootstrap.sh` | Already exists; bootstrap handles ECC + registry on new machines. |
| 4 | Selector scope | **All six categories** (agents, skills, MCPs, slash commands, hook profiles, language-specific rules) | Operator's request; matches "super repo" framing. |
| 5 | Selector mechanism | **Per-IDE preamble + Claude Code `UserPromptSubmit` hook** | Universal coverage; CC hook is now load-bearing for token economy. |
| 6 | Consultation cadence | **Per prompt**, with `.current.json` cache for mid-task chatter and split-file `ROUTING.md` for cheap reads | Operator's explicit pick; cost stays bounded via split-file + cache. |
| 7 | Registry sourcing | **Three sources:** ECC submodule scrape, harness scan (`~/.claude/`), native blueprint | Each source has distinct authority and update cadence. |
| 8 | Update workflow | **Stage-but-not-commit** for `update-ecc.sh` and `refresh-harness.sh` | Matches operator's preference for surgical commits. |
| 9 | Failure handling | **Fail-open at runtime; warn loud at rebuild time** | Maintenance noise stays in maintenance mode; runtime stays out of the way. |

---

## 4. Architecture Overview

### 4.1 New files added to `workspace-blueprint`

```
workspace-blueprint/
├─ ROUTING.md                          [NEW] entry-level decision tree
├─ AGENTS.md                           [NEW] cross-IDE preamble (Codex, OpenCode)
├─ .cursorrules                        [NEW] Cursor preamble
├─ GEMINI.md                           [NEW] Gemini CLI preamble
├─ CLAUDE.md                           [UPDATED] one-line pointer to ROUTING.md
├─ .gitmodules                         [NEW] declares the ECC submodule
├─ external/
│  └─ ecc/                             [NEW] git submodule → affaan-m/everything-claude-code
├─ .claude/
│  ├─ routing/
│  │  ├─ build.md                      [NEW] feature-implementation branch
│  │  ├─ bug.md                        [NEW] bug-fix branch
│  │  ├─ refactor.md                   [NEW]
│  │  ├─ spike.md                      [NEW]
│  │  ├─ spec-author.md                [NEW]
│  │  ├─ ship.md                       [NEW]
│  │  └─ .current.json                 [generated; gitignored] per-prompt cache
│  ├─ registry/
│  │  ├─ ecc-config.json               [NEW; committed] submodule path config
│  │  ├─ ecc-agents.json               [generated; committed]
│  │  ├─ ecc-skills.json               [generated; committed]
│  │  ├─ ecc-commands.json             [generated; committed]
│  │  ├─ ecc-mcps.json                 [generated; committed]
│  │  ├─ ecc-hook-profiles.json        [generated; committed]
│  │  ├─ ecc-language-rules.json       [generated; committed]
│  │  ├─ harness-skills.json           [generated; committed]
│  │  ├─ harness-mcps.json             [generated; committed]
│  │  ├─ harness-builtins.json         [generated; committed]
│  │  └─ native-inventory.json         [generated; committed; optional]
│  └─ hooks/
│     └─ route-inject.sh               [NEW] UserPromptSubmit hook (CC-only)
└─ scripts/
   ├─ route.mjs                        [NEW] deterministic routing module
   ├─ rebuild-registry.mjs             [NEW] scrapes ECC + harness, rewrites .claude/registry/
   ├─ bootstrap.sh                     [NEW] new-machine setup
   ├─ update-ecc.sh                    [NEW] submodule bump + registry rebuild
   └─ refresh-harness.sh               [NEW] re-scrapes harness inventory
```

### 4.2 What stays unchanged

- The 3-layer routing (`CLAUDE.md` → `CONTEXT.md` → workspace `CONTEXT.md`) is preserved; `ROUTING.md` is a parallel decision-tree layer that complements `CONTEXT.md` rather than replacing it.
- The `spec/`, `lab/`, `build/`, `ship/` workspaces are unchanged.
- The 4-agent loop (planner → implementer ↔ reviewer ↔ adversary) is unchanged.
- The 5 portability rules and 4 bash hooks (`pre-commit-tdd.sh`, `block-cycle-overrun.sh`, `block-output-without-signoff.sh`, `enforce-portability.sh`) are unchanged.
- The 4 MCP servers configured in `settings.json` (`filesystem`, `git`, `fetch`, `github`) are unchanged.
- ECC's clone is read-only from the bridge's perspective.

### 4.3 ECC reference resolution

The submodule SHA pinned in `.gitmodules` records exactly which ECC version the registry was built against. Paths in `ecc-*.json` are relative to `external/ecc/`. An `ECC_PATH` env var may override the default submodule path; the default in `ecc-config.json` is `${REPO_ROOT}/external/ecc`.

---

## 5. ROUTING.md Structure

### 5.1 Entry file: `ROUTING.md`

Contains:

- A short instruction header explaining how the agent traverses the tree.
- A Step 1 table mapping fuzzy prompt signals to (workspace, branch file) pairs.
- A task-transition detection paragraph (cache-invalidation rules).
- A fallback section describing native-only routing when no branch matches.

Approximate size: 1 KB / ~250 tokens.

### 5.2 Branch files: `.claude/routing/<branch>.md`

One per task type:

- `build.md` — feature implementation
- `bug.md` — bug fix
- `refactor.md` — refactoring / migration
- `spike.md` — exploratory investigation
- `spec-author.md` — RFC, ADR, brief authoring
- `ship.md` — release artifacts, changelog, docs

Each branch file contains:

- **Always-load section:** agents, skills, slash commands, MCPs, hook profile, rules that apply to every task in this branch regardless of language or specifics.
- **Language matrix:** table mapping file-pattern detection to language-specific additions from ECC (e.g., `*.py` → `python-reviewer + python-patterns`, `*.go` → `go-reviewer + go-build-resolver + go-patterns`).
- **Specialty additions:** further narrowing for sub-cases (e.g., Python + ML libraries → `+ pytorch-patterns`).

Each branch file is ~1 KB / ~250 tokens.

### 5.3 Authoring conventions

- Items in routing files are referenced **by name only** (e.g., `python-reviewer`), not by path. Name resolution happens at runtime via `.claude/registry/*.json`. This decouples `ROUTING.md` from ECC's filesystem layout, so an ECC restructure upstream only requires a registry rebuild, not edits to ROUTING.md.
- Names with namespaces use `namespace:item` form (e.g., `superpowers:brainstorming`) to match Claude Code's plugin naming.
- Tables use the same Markdown table format throughout for parsability.
- Each branch file ends with a `## Notes` section for authoring-time comments (intentionally not scraped by `route.mjs`).

### 5.4 Relationship to existing `CONTEXT.md`

`CONTEXT.md` remains the canonical "task → workspace" router (Layer 2 of the existing 3-layer scheme). `ROUTING.md` is a new "task → inventory subset" tree. They are complementary:

- `CONTEXT.md` answers **where do I work?** (which workspace + which files to load).
- `ROUTING.md` answers **what do I use?** (which items from the inventory).

Both can be consulted by the agent. Each IDE's preamble (`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex / OpenCode, `.cursorrules` for Cursor, `GEMINI.md` for Gemini CLI) directs the agent to consult `CONTEXT.md` for workspace routing and `ROUTING.md` for inventory narrowing. `CLAUDE.md` is additionally auto-loaded by Claude Code as the always-on chassis map.

### 5.5 Example traversal

```
Prompt: "add a rate limiter to the Go gateway service"

1. Agent reads ROUTING.md → matches Step 1 "add" → §A Build → branch: build.md
2. Agent reads .claude/routing/build.md
3. Always-load: planner, implementer, reviewer, adversary, tdd-loop, all 5 rules, hook-profile=standard
4. Detects files in scope are *.go → matches Go row in language matrix
5. Adds: go-reviewer, go-build-resolver, go-patterns
6. Resolves names via .claude/registry/ecc-agents.json + ecc-skills.json
   → external/ecc/agents/go-reviewer.md, external/ecc/skills/go-patterns/, etc.
7. Agent proceeds with the narrowed inventory.
```

---

## 6. Registry Mechanism

### 6.1 Three scrape sources

| Source | Path | Authority | Rebuild trigger |
|---|---|---|---|
| ECC submodule | `external/ecc/` | Pinned submodule SHA | `update-ecc.sh` |
| Claude Code harness | `~/.claude/plugins/`, `~/.claude/settings.json` | Current install state | `refresh-harness.sh` or `bootstrap.sh` |
| Workspace-blueprint native | `.claude/agents/`, `.claude/skills/`, `.claude/rules/` | Repo content | `bootstrap.sh` (optional) |

### 6.2 Registry files under `.claude/registry/`

- `ecc-config.json` — submodule path, env-override key, scrape settings.
- `ecc-agents.json` — 48 ECC agents (current snapshot).
- `ecc-skills.json` — 185 ECC skills.
- `ecc-commands.json` — 68 ECC slash commands.
- `ecc-mcps.json` — ECC's `mcp-configs/` entries.
- `ecc-hook-profiles.json` — minimal/standard/strict profiles and per-hook details.
- `ecc-language-rules.json` — per-language rule files (10 languages).
- `harness-skills.json` — currently installed Claude Code plugin skills.
- `harness-mcps.json` — currently configured MCP servers.
- `harness-builtins.json` — built-in subagent types and slash commands.
- `native-inventory.json` — workspace-blueprint's own agents/skills/rules (optional).

**Note on MCP entries:** `ecc-mcps.json`, `harness-mcps.json`, and references to MCPs in routing files are *advisory only*. The auto-selector recommends which MCPs are likely needed for a task; the agent uses them when relevant. The bridge does NOT enable/disable MCPs dynamically — all configured MCPs remain available throughout the session.

### 6.3 Record format

```json
{
  "name": "python-reviewer",
  "kind": "agent",
  "source": "ecc",
  "path": "agents/python-reviewer.md",
  "description": "Reviews Python code for style, idioms, common errors",
  "languages": ["python"],
  "tools": ["Read", "Grep", "Bash"],
  "model": "sonnet",
  "indexed_at": "2026-05-11T08:30:00Z",
  "ecc_sha": "abc123def456"
}
```

For harness-sourced entries, `source: "harness"`, no `ecc_sha`, and `plugin_path` instead of `path`. For native entries, `source: "native"` and `path` is relative to `.claude/`.

### 6.4 Scrape strategy (`scripts/rebuild-registry.mjs`)

**Runtime:** ESM `.mjs` (Node 18+ required). New scripts (`route.mjs`, `rebuild-registry.mjs`) use the `.mjs` extension explicitly rather than setting `"type": "module"` in `package.json` — this avoids forcing the entire repo into ESM. Single external dependency: `gray-matter` for YAML frontmatter parsing.

1. Read `ecc-config.json`, resolve ECC path (env override applied if present).
2. For each ECC subdir (`agents/`, `skills/`, `commands/`, `mcp-configs/`, `hooks/`, `rules/`):
   - Walk files. For `.md` files, parse YAML frontmatter using `gray-matter` (or equivalent).
   - Extract `name`, `description`, `languages`, `tools`, `model` fields when present.
   - Infer `kind` from the parent directory.
   - For commands with sparse frontmatter, use the first non-frontmatter paragraph as description.
   - For JSON MCP configs, parse and extract server names + commands.
3. Scan `~/.claude/plugins/cache/` for installed plugins:
   - Each plugin directory has a manifest (`plugin.json` or similar). Read it.
   - For each declared skill, record the name + namespace + plugin path.
4. Read `~/.claude/settings.json` → `mcpServers` section → emit `harness-mcps.json`.
5. (Optional) Scan workspace-blueprint's own `.claude/` directories → `native-inventory.json`.
6. Stamp each record with `indexed_at` (ISO-8601) and (for ECC entries) `ecc_sha` from `git -C external/ecc rev-parse HEAD`.
7. Validate: for every name referenced in `ROUTING.md` and `.claude/routing/*.md`, confirm a registry entry exists. Print warnings for dangling names. Do not fail on warnings.
8. Write all JSONs atomically (temp-file + rename) so a crashed rebuild never leaves partial output.

### 6.5 Validation step

After every rebuild, `rebuild-registry.mjs` grep-scans `ROUTING.md` and `.claude/routing/*.md` for item-name tokens. Each token must resolve to a registry entry; otherwise a warning is logged. This catches name drift after ECC upstream renames an item.

### 6.6 Frontmatter normalization

ECC's items have inconsistent frontmatter (some omit `languages`, some use scalar instead of array values, some include `model`, some don't). The scraper applies a defensive schema:

- **Required fields:**
  - `name` — defaults to filename stem if frontmatter omits it.
  - `kind` — always set by the scraper based on parent directory (`agents/` → `agent`, `skills/` → `skill`, `commands/` → `command`, `mcp-configs/` → `mcp`, etc.).
  - `source` — always set by the scraper (`ecc`, `harness`, or `native`).
- **Optional fields with defaults:**
  - `description` — fallback chain: frontmatter value → first non-frontmatter paragraph (≤ 200 chars) → empty string.
  - `languages` — default `[]` (language-agnostic).
  - `tools` — default `[]`.
  - `model` — default `null` (meaning "harness default").
- **Type coercion:** scalar → array for `languages` and `tools`. Example: `languages: python` becomes `["python"]`.
- **Parse failure handling:** YAML parse errors are caught; the offending file is skipped with a warning to stderr. The rebuild continues. A summary at end of rebuild reports total files skipped.
- **Slash command resolution:** commands in `commands/` typically have sparser frontmatter than agents/skills. Resolution order: (1) frontmatter `description`; (2) first non-frontmatter paragraph (≤ 200 chars); (3) filename derivation (e.g., `tdd-workflow.md` → `"TDD Workflow"`).

---

## 7. Data Flow & Regeneration

### 7.1 Per-prompt flow (every prompt)

```
[User sends prompt]
    │
    ▼
[Preamble file loaded by IDE]  CC→CLAUDE.md  Codex→AGENTS.md  Cursor→.cursorrules  Gemini→GEMINI.md
    │
    ▼
[Claude Code only: UserPromptSubmit hook fires]
    │ Hook script calls scripts/route.mjs(prompt, files_in_scope)
    │ route.mjs reads ROUTING.md + matching branch + registries
    │ Hook injects ~80-token narrowing summary into agent's context
    ▼
[Agent receives prompt + (CC) injected narrowing OR (non-CC) just preamble pointer]
    │ Non-CC: agent reads ROUTING.md (~250 tokens), determines branch,
    │ reads .claude/routing/<branch>.md (~250 tokens), looks up names in registries.
    │ Both: agent checks .claude/routing/.current.json cache;
    │       if prompt suggests no task transition, reuse cached narrowing.
    ▼
[Agent has narrowed inventory; proceeds with task]
    │
    ▼
[Agent writes new narrowing (if changed) to .claude/routing/.current.json]
```

Approximate per-prompt routing overhead:
- **Claude Code (with hook):** ~80 tokens (the injected name list).
- **Non-CC, cache miss / task transition:** ~500 tokens (entry + one branch file).
- **Non-CC, cache hit:** ~50 tokens (just re-read `.current.json`).

### 7.2 Bootstrap lifecycle (`scripts/bootstrap.sh`)

Run once per machine after `git clone --recursive`:

1. Verify `external/ecc/` is populated. If empty, run `git submodule update --init --recursive`.
2. Scan `~/.claude/plugins/cache/` → rebuild `harness-skills.json` and `harness-builtins.json`.
3. Read `~/.claude/settings.json` → rebuild `harness-mcps.json`.
4. Compare current submodule HEAD SHA to `ecc_sha` stamps in `ecc-*.json` registries. If they match, skip ECC re-scrape. Otherwise re-scrape ECC.
5. Validate name resolution across `ROUTING.md` and all `.claude/routing/*.md`. Print warnings for dangling names.
6. Print summary: "Indexed N agents, M skills, K commands, P MCPs from ECC. Found Q harness skills, R MCP servers, S built-in subagents."
7. Exit 0 unless `ROUTING.md` is malformed.

Idempotent: re-running with no state changes is a no-op.

### 7.3 Update-ECC lifecycle (`scripts/update-ecc.sh`)

Run when bumping ECC to a newer upstream commit:

1. `git submodule update --remote external/ecc` — pulls latest upstream.
2. Re-run `rebuild-registry.mjs` for the ECC sources.
3. Compute and print diff vs. previous registry: items added, removed, renamed.
4. Validate name resolution; print warnings for newly-dangling names in `ROUTING.md`.
5. Stage the submodule pin update + the regenerated `ecc-*.json` files for commit.
6. Print: "Review diff with `git diff --staged`, then commit when ready."

Does NOT auto-commit. The operator reviews the diff and decides whether to bump or roll back.

### 7.4 Refresh-harness lifecycle (`scripts/refresh-harness.sh`)

Run after `/plugin install`, `/plugin remove`, or any change to `~/.claude/settings.json`:

1. Re-scan `~/.claude/plugins/cache/` → rebuild `harness-skills.json` + `harness-builtins.json`.
2. Re-read `~/.claude/settings.json` → rebuild `harness-mcps.json`.
3. Print diff: new plugins detected, removed ones gone.
4. Stage; suggest `ROUTING.md` edits if a new plugin's skills look routing-worthy.

### 7.5 Cache invalidation

`.claude/routing/.current.json` is invalidated by task-transition signals defined in `ROUTING.md`'s entry section:

- Prompt contains transition phrases ("now let's do…", "switch to…", "actually…").
- File scope changes substantially (different language, different workspace).
- Explicit `/refresh-routing` slash command (optional, low priority for v1).

Mid-task chatter ("yes", "explain more", "do that") preserves the cache.

### 7.6 Hook profile mechanism

Three profiles control whether the workspace-blueprint hooks fire and at what strictness:

- **`minimal`** — hooks no-op (exit 0 immediately). Useful for spikes in `lab/` where TDD enforcement and review-gate checks would be premature.
- **`standard`** — current behavior (default). All 4 hooks run their normal checks.
- **`strict`** — current behavior plus any future stricter variants. Reserved for `ship/` workflows; currently identical to `standard`.

**Activation:** the operator sets `BLUEPRINT_HOOK_PROFILE=<profile>` in the shell environment before launching the IDE. Each of the 4 existing hooks (`pre-commit-tdd.sh`, `block-cycle-overrun.sh`, `block-output-without-signoff.sh`, `enforce-portability.sh`) gets a 3-line gate at the top:

```bash
PROFILE="${BLUEPRINT_HOOK_PROFILE:-standard}"
[ "$PROFILE" = "minimal" ] && exit 0
# rest of hook unchanged
```

**Recommendation flow:** the auto-selector outputs the recommended profile in its routing injection (CC) or branch file (non-CC). The operator activates manually via `export BLUEPRINT_HOOK_PROFILE=<profile>`. v1 does NOT auto-activate (would require shell-launcher integration; deferred to future work).

**Per-branch default recommendations** (encoded in `.claude/routing/<branch>.md`):

| Branch | Recommended profile |
|--------|---------------------|
| `build.md` (feature) | `standard` |
| `bug.md` | `standard` |
| `refactor.md` | `standard` |
| `spike.md` (exploration) | `minimal` |
| `spec-author.md` | `minimal` |
| `ship.md` (release) | `strict` |

---

## 8. Error Handling

All failure modes degrade gracefully. The common pattern: **warn loud at rebuild time, skip silent at runtime.**

| Failure | Detected by | Degraded behavior |
|---------|-------------|-------------------|
| `external/ecc/` missing | `bootstrap.sh`, `route.mjs` | Skip ECC registry; native-only routing |
| Submodule SHA ≠ registry `ecc_sha` | `bootstrap.sh` diff check | Warn; rebuild `ecc-*.json` |
| `.claude/registry/*.json` missing | `route.mjs` | Warn; native-only routing |
| Dangling name in `ROUTING.md` | `rebuild-registry.mjs` validation | Warn at rebuild; runtime skip |
| `ROUTING.md` missing | `route.mjs` | Fall back to `CONTEXT.md` routing only |
| `.claude/routing/<branch>.md` missing | `route.mjs` | Use Step 1 always-load defaults only |
| `.current.json` corrupted | `route.mjs` | Discard cache; full re-traverse |
| `route-inject.sh` hook errors | Hook itself | Exit 0 silently; preamble path takes over |
| Harness MCP unavailable | Tool-call time | Agent gets tool-error; tries alternative |
| Plugin uninstalled but still in registry | Tool-call time | Agent gets unknown-skill; falls back |
| Two branches both match | `route.mjs` | Pick first by Step 1 table order; log |
| No branch matches | `route.mjs` | Native defaults only |
| Mixed-language files in scope | `route.mjs` | Union of language items |

The worst-case failure mode is "bridge layer absent → blueprint behaves like it did before the integration." There is no catastrophic state.

---

## 9. Testing Strategy

### 9.1 Single source of routing truth

`scripts/route.mjs` is the deterministic module: given `(prompt, files_in_scope, registry)`, it produces a narrowing. It is called by:

- `.claude/hooks/route-inject.sh` (Claude Code hook).
- `scripts/update-ecc.sh` (validation after submodule bump).
- All unit and snapshot tests.

The agent's inline routing (used in non-CC IDEs) should produce results matching `route.mjs`'s output for the same input. An optional periodic alignment check verifies this.

### 9.2 Test layout

```
tests/
├─ unit/
│  ├─ frontmatter-parse.test.mjs       parses YAML frontmatter correctly
│  ├─ rebuild-registry.test.mjs        builds registry from mock filesystem
│  ├─ route.test.mjs                   core routing logic
│  └─ cache-invalidate.test.mjs        cache invalidation rules
│
├─ routing-cases/                       snapshot tests
│  ├─ go-feature.json
│  ├─ python-bugfix.json
│  ├─ ts-refactor.json
│  ├─ spike-investigation.json
│  ├─ mixed-language.json
│  └─ no-match-fallback.json
│
├─ integration/
│  ├─ bootstrap-cleanroom.sh           clean-checkout bootstrap
│  ├─ update-ecc-dry-run.sh
│  └─ refresh-harness.sh
│
└─ hook/
   ├─ route-inject.test.sh             hook produces expected injection
   └─ inject-on-error.test.sh          hook fails gracefully on malformed input
```

### 9.3 Snapshot test format

Each routing case under `tests/routing-cases/`:

```json
{
  "name": "go-feature-implementation",
  "prompt": "add a rate limiter to the gateway service",
  "files_in_scope": ["gateway/handler.go", "gateway/middleware.go"],
  "expected_narrowing": {
    "agents": ["planner", "implementer", "reviewer", "adversary", "go-reviewer", "go-build-resolver"],
    "skills": ["tdd-loop", "go-patterns"],
    "commands": ["/tdd", "/build-fix"],
    "mcps": ["filesystem", "git"],
    "rules": ["all"],
    "hook_profile": "standard"
  }
}
```

`scripts/route.mjs(prompt, files_in_scope, registry)` is invoked; output must equal `expected_narrowing`.

### 9.4 Verification gates

- **Pre-commit:** if `scripts/route.mjs` or any `.claude/routing/*.md` changed, all `routing-cases` must pass. Integrates with the existing `pre-commit-tdd.sh` hook.
- **On ECC bump (`update-ecc.sh`):** validation runs; new dangling names reported as warnings, never blocking.
- **On bootstrap:** validates name resolution + registry completeness; prints summary; exits non-zero only if `ROUTING.md` itself is malformed.
- **Optional CI smoke test:** clean-checkout bootstrap + all routing-cases. Catches drift between `ROUTING.md` and the registry.

---

## 10. Resolved Design Decisions

Questions raised during brainstorming, resolved before implementation:

1. **Frontmatter format normalization.** Resolved in §6.6: defensive schema with required/optional fields, default values, type coercion, and parse-failure handling.
2. **Slash command description fallback.** Resolved in §6.6 (last bullet): three-tier resolution order (frontmatter → paragraph → filename).
3. **`scripts/route.mjs` runtime.** Resolved in §6.4: ESM `.mjs` (Node 18+); `.mjs` extension per-file rather than `package.json "type": "module"` to avoid forcing the whole repo into ESM.
4. **Hook profile mechanism.** Resolved in §7.6 (pulled from former §12 future work). Three profiles (`minimal`/`standard`/`strict`) gated by `BLUEPRINT_HOOK_PROFILE` env var. Implementation modifies the 4 existing hook scripts with a 3-line gate; recommendations flow from the selector but activation is manual in v1.
5. **MCP server activation per task.** Resolved in §6.2: MCPs are recommendation-only. The selector advises which MCPs are likely needed; the agent uses them when relevant. No dynamic enable/disable.

## 11. Non-Goals

- **Vendoring ECC's content into `workspace-blueprint`.** Considered and rejected (Option A in brainstorming).
- **Modifying ECC's clone.** The submodule is treated as read-only. Any edits would defeat the bridge philosophy and break upstream sync.
- **Building or maintaining a custom MCP routing server (Option B).** Considered; rejected for v1 to keep infrastructure surface minimal. May be revisited later.
- **Cross-IDE hook parity.** Only Claude Code gets a hook. Other IDEs rely on preamble + agent compliance.
- **Auto-installing harness plugins.** The bridge indexes what's already installed; it does not install plugins on the operator's behalf.
- **Running ECC's installer scripts (`install.sh`, `install.ps1`).** The submodule provides ECC's source files; the bridge consumes them directly without running ECC's installer.

---

## 12. Future Work

- **Periodic alignment check** between `route.mjs` output and the agent's inline routing in non-CC harnesses (a CI job that runs the agent against the same cases and diffs).
- **Custom MCP routing server (Option B)** if LLM compliance with the preamble proves unreliable in non-CC IDEs.
- **Auto-activation of `BLUEPRINT_HOOK_PROFILE`** via a shell-launcher wrapper (e.g., `./scripts/with-profile.sh minimal claude`) that sets the env var before launching the IDE, eliminating the manual `export` step.
- **`/refresh-routing` slash command** for manual mid-session re-narrowing.
- **Multi-repo support:** if the operator wants to extend the bridge pattern to additional sources (e.g., `obra/superpowers` as a second submodule), the registry mechanism generalizes — `external/superpowers/` + `scripts/rebuild-registry.mjs` walks an additional source.

---

## 13. Appendix — Captured Harness Inventory (snapshot, 2026-05-11)

State of the operator's Claude Code harness at design time. Subject to change as plugins are installed/removed; the `refresh-harness.sh` lifecycle keeps `harness-*.json` in sync.

### Plugin-skills (≈ 40 available)

- **`superpowers:*`** — `systematic-debugging`, `requesting-code-review`, `finishing-a-development-branch`, `dispatching-parallel-agents`, `executing-plans`, `test-driven-development`, `writing-plans`, `verification-before-completion`, `using-git-worktrees`, `using-superpowers`, `subagent-driven-development`, `writing-skills`, `receiving-code-review`, `brainstorming`.
- **`mempalace:*`** — `search`, `status`, `mine`, `init`, `help`, `mempalace`.
- **`firecrawl:*`** — `skill-gen`, `firecrawl-cli`, `firecrawl-crawl`, `firecrawl-search`, `firecrawl-map`, `firecrawl-scrape`, `firecrawl-instruct`, `firecrawl-agent`, `firecrawl-download`.
- **`ralph-loop:*`** — `help`, `cancel-ralph`, `ralph-loop`.
- **`code-review:*`** — `code-review`.
- **`claude-code-setup:*`** — `claude-automation-recommender`.
- **`remember:*`** — `remember`.
- **`andrej-karpathy-skills:*`** — `karpathy-guidelines`.
- **`ai:*`** — `building-pydantic-ai-agents`.
- **Built-ins:** `init`, `review`, `security-review`, `simplify`, `loop`, `schedule`, `claude-api`, `update-config`, `keybindings-help`, `fewer-permission-prompts`.

### MCP servers (≈ 13 configured)

`brave-search`, `claude_ai_Gmail`, `claude_ai_Google_Calendar`, `claude_ai_Google_Drive`, `claude_ai_Spotify`, `fetch`, `filesystem`, `git`, `github`, `plugin_context7_context7`, `plugin_mempalace_mempalace`, `plugin_serena_serena`, `sentry`.

### Built-in subagent types

`claude-code-guide`, `code-simplifier`, `Explore`, `general-purpose`, `Plan`, `statusline-setup`.

### Built-in tools

(Out of routing scope but listed for completeness:) `Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`, `Agent`, `AskUserQuestion`, `ScheduleWakeup`, `Skill`, `ToolSearch`, `TaskCreate`, `TaskUpdate`, `TaskList`, `TaskGet`, `Monitor`, `EnterPlanMode`, `ExitPlanMode`, `EnterWorktree`, `ExitWorktree`, `CronCreate`, `CronList`, `CronDelete`, `WebFetch`, `WebSearch`, `NotebookEdit`, `ListMcpResourcesTool`, `ReadMcpResourceTool`, `PushNotification`, `RemoteTrigger`.

---

*End of design spec. Implementation plan to follow once this is approved by the operator.*
