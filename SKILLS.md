# Skills, Agents, Commands, and MCPs

> Human-readable inventory of what this scaffold offers, organized by task. **Not loaded by agents** — the source of truth for routing is `ROUTING.md` + `.claude/routing/*.md` + `.claude/registry/*.json`. This doc orients humans so they know what to expect when a task starts, where each item lives, and how to add a new one.
>
> **Scope:** the ~46 items actively referenced by routing branch files. The full registry universe (~421 items across ECC + harness + native) is much larger; this is the curated subset that actually loads.
>
> **Token-cost note:** this file is not auto-loaded by any IDE preamble. It exists for discovery, not for routing. The strict validator in `scripts/rebuild-registry.mjs` does NOT scan this file; references here can drift from the routing files without breaking the build. **Routing files / registry / `npm run rebuild-registry` are authoritative — this doc is orientation.**

---

## What loads when (by task type)

### Implementing a feature — `.claude/routing/build.md`

Always-load:
- Agents: `planner`, `implementer`, `reviewer`, `adversary`
- Skills: `tdd-loop`
- Rules: all 7 native
- Hook profile: `standard`
- MCPs (advisory): `filesystem`, `git`

Plus language-specific helpers when source files are in scope: `python-reviewer` + `python-patterns` for Python, `go-reviewer` + `go-build-resolver` + `golang-patterns` for Go, `typescript-reviewer` for TypeScript, etc. See `.claude/routing/build.md` for the full language matrix.

### Fixing a bug — `.claude/routing/bug.md`

Always-load:
- Agents: `implementer`, `reviewer` (no planner — bugs have no design surface)
- Skills: `bug-investigation`, `tdd-loop`, `systematic-debugging`
- Rules: all 7 native
- Hook profile: `standard`
- MCPs (advisory): `filesystem`, `git`

Plus language-specific reviewers as above.

### Refactoring / migrating — `.claude/routing/refactor.md`

Always-load:
- Agents: `planner`, `implementer`, `reviewer`, `adversary`, `refactor-cleaner`, `code-simplifier`
- Skills: `tdd-loop`, `karpathy-guidelines`
- Rules: all 7 native
- Hook profile: `standard`
- MCPs (advisory): `filesystem`, `git`

Both reviewer AND adversary because regressions are the dominant risk in refactors.

### Investigating / spike — `.claude/routing/spike.md`

Always-load:
- Agents: `general-purpose`, `Explore`, `code-explorer`
- Skills: `spike-protocol`, `data-analysis`
- Rules: `portability-discipline` only (other rules relaxed during exploration)
- Hook profile: `minimal` (lab/ work doesn't need TDD enforcement)
- MCPs (advisory): `filesystem`, `fetch`

No language-specific agents by design — the spike's purpose is to discover constraints, not enforce them.

### Authoring a spec / ADR / brief — `.claude/routing/spec-author.md`

Always-load:
- Agents: `planner`, `architect`, `Plan`
- Skills: `spec-authoring`, `writing-plans`, `brainstorming`
- Rules: `portability-discipline`, `commit-discipline` (TDD / review / code-quality don't apply to docs)
- Hook profile: `minimal`
- MCPs (advisory): `filesystem`, `fetch`

### Releasing artifacts — `.claude/routing/ship.md`

Always-load:
- Agents: `reviewer`, `adversary`, `doc-updater`, `opensource-packager`
- Skills: none by default. The office skills (`docx` / `pptx` / `xlsx` / `pdf`) auto-load when the output path has the matching extension.
- Rules: all 7 native (maximum strictness)
- Hook profile: `strict`
- MCPs (advisory): `filesystem`, `git`, `github`

---

## Items by source

### Native — in this repo

**Agents** at `.claude/agents/`:

| Name | Path | Role |
|------|------|------|
| `planner` | `planner-agent.md` | One-shot: converts a `spec/` source artifact into `build/workflows/NN-<slug>/01-spec/SPEC.md`. |
| `implementer` | `implementer-agent.md` | Per cycle: writes production code in `src/`, process notes in `02-implement/`. |
| `reviewer` | `reviewer-agent.md` | Per cycle (parallel with adversary): verdict against SPEC.md acceptance criteria. |
| `adversary` | `adversary-agent.md` | Per cycle (parallel with reviewer): edge cases, attack surfaces, race conditions. |

**Skills** at `.claude/skills/`:

| Name | Path | Origin |
|------|------|--------|
| `tdd-loop` | `tdd-loop/SKILL.md` | Native — TDD red→green→refactor for the build pipeline. |
| `bug-investigation` | `bug-investigation/SKILL.md` | Native — reproduce-before-fix discipline. |
| `spike-protocol` | `spike-protocol/SKILL.md` | Native — PREFLIGHT → prototype → VERIFY → REPORT for lab/. |
| `data-analysis` | `data-analysis/SKILL.md` | Native — guidance for analysis spikes. |
| `spec-authoring` | `spec-authoring/SKILL.md` | Native — RFC / ADR / brief shapes for the planner agent. |
| `refactor-protocol` | `refactor-protocol/SKILL.md` | Native — blast-radius + behavior-equivalence discipline. |
| `docx` | `docx/SKILL.md` | Vendored from `anthropics/skills`. |
| `pptx` | `pptx/SKILL.md` | Vendored from `anthropics/skills`. |
| `xlsx` | `xlsx/SKILL.md` | Vendored from `anthropics/skills`. |
| `pdf` | `pdf/SKILL.md` | Vendored from `anthropics/skills`. |
| `systematic-debugging` | `systematic-debugging/SKILL.md` | Vendored from `superpowers@5.1.0` (MIT). |
| `karpathy-guidelines` | `karpathy-guidelines/SKILL.md` | Vendored from `andrej-karpathy-skills@1.0.0` (MIT). |
| `writing-plans` | `writing-plans/SKILL.md` | Vendored from `superpowers@5.1.0` (MIT). |
| `brainstorming` | `brainstorming/SKILL.md` | Vendored from `superpowers@5.1.0` (MIT). |

Vendored-skill attribution and license text: `.claude/skills/THIRD_PARTY_LICENSES.md`. Refresh from upstream when plugin cache has a newer version: `npm run refresh-vendored`.

**Rules** at `.claude/rules/`:

| Name | What it enforces |
|------|------------------|
| `code-quality` | Linter + format pass before promoting to `04-output/`. No debug statements, no dead code. |
| `commit-discipline` | One logical change per commit, Conventional Commits, never `--no-verify`. |
| `testing-discipline` | TDD; test files precede implementation. Enforced by `pre-commit-tdd.sh` hook. |
| `review-discipline` | Reviewer + adversary both run per cycle; 5-cycle cap. Enforced by `block-cycle-overrun.sh`. |
| `portability-discipline` | `.claude/rules/` and `.claude/skills/` stay domain-agnostic. Enforced by `enforce-portability.sh`. |
| `unix-philosophy` | One responsibility per unit, plain-text contracts (applicability-driven). |
| `nasa-power-of-10` | Subset of JPL Power-of-10 rules (loops with bounds, return-value checking, short functions, strict warnings) — applicability-driven. |

**MCPs** declared in `.claude/settings.json`:

| Name | Server | Purpose |
|------|--------|---------|
| `filesystem` | `@modelcontextprotocol/server-filesystem` | Repo-rooted filesystem access. |
| `git` | `@modelcontextprotocol/server-git` | Git read/write against this repo. |
| `fetch` | `@modelcontextprotocol/server-fetch` | HTTP fetch (no auth, credential-free). |
| `github` | `@modelcontextprotocol/server-github` | GitHub API (requires `GITHUB_PERSONAL_ACCESS_TOKEN` env var). |

### ECC — in `external/ecc/` submodule

Submodule pinned at SHA `894ee039`. Items below are referenced by routing branch files; the strict validator (`scripts/rebuild-registry.mjs`) fails the rebuild if any of these don't resolve.

**Agents:** `python-reviewer`, `go-reviewer`, `typescript-reviewer`, `java-reviewer`, `kotlin-reviewer`, `cpp-reviewer`, `csharp-reviewer`, `flutter-reviewer`, `go-build-resolver`, `java-build-resolver`, `kotlin-build-resolver`, `cpp-build-resolver`, `dart-build-resolver`, `refactor-cleaner`, `code-simplifier`, `doc-updater`, `opensource-packager`, `architect`, `code-explorer`.

**Skills:** `python-patterns`, `golang-patterns`.

**Commands:** `/build-fix`.

The other ~540 items in the ECC submodule are discoverable through the registry (`jq '.[].name' .claude/registry/ecc-*.json`) but not currently routed. To add a new routing reference, name the item in the relevant branch file under `.claude/routing/` and run `npm run rebuild-registry` to validate.

### Harness built-in subagents

Provided by Claude Code itself. Always present in `harness-builtins.json` regardless of plugin install state (per `BUILTINS` constant in `scripts/lib/harness-scraper.mjs`):

| Name | Role |
|------|------|
| `general-purpose` | Generic delegation agent. |
| `Explore` | Read-only search / exploration agent. |
| `Plan` | Software-architect planning agent. |

### Harness plugins — for reference, not vendored

The `scripts/lib/harness-scraper.mjs` script reads `~/.claude/plugins/cache/` on the operator's machine, but routing branch files do not reference harness-installed plugins directly anymore (the 4 that were referenced — `systematic-debugging`, `karpathy-guidelines`, `writing-plans`, `brainstorming` — have been vendored into `.claude/skills/` for portability). If a future routing branch wants to depend on a harness-installed plugin, it should be vendored first (see "How to add a new item" below).

---

## How to add a new item

### A new native agent / skill / rule

1. Create the file under `.claude/agents/`, `.claude/skills/<name>/SKILL.md`, or `.claude/rules/`.
2. Add it to the relevant `.claude/routing/<branch>.md` if you want it auto-loaded for a task type.
3. Run `npm run rebuild-registry` — it indexes into `.claude/registry/native-inventory.json` and the strict validator confirms the reference resolves.
4. Run `npm test` to confirm no regressions.

### A new ECC reference

1. Confirm the item exists in `external/ecc/` (e.g., `ls external/ecc/agents/`).
2. Reference it by name in the relevant `.claude/routing/<branch>.md`.
3. Run `npm run rebuild-registry`. The strict validator hard-fails if the name doesn't resolve.

### A new vendored skill (from a harness plugin)

1. Copy upstream `SKILL.md` to `.claude/skills/<name>/SKILL.md`.
2. Add `vendored_from: "<plugin-cache-path>@<version>"` and `license: <license>` to frontmatter.
3. Update `.claude/skills/THIRD_PARTY_LICENSES.md` with the upstream copyright + license text.
4. Reference by name in the relevant `.claude/routing/<branch>.md`.
5. Run `npm run rebuild-registry` to confirm resolution and run `npm test` to confirm no regressions.
6. Future maintenance: `npm run refresh-vendored` re-copies from the local plugin cache when upstream has newer content.

### A new MCP

1. Add the server declaration to `.claude/settings.json` `mcpServers`.
2. The harness scraper picks it up automatically on the next `npm run rebuild-registry`.
3. Reference by name in the relevant `.claude/routing/<branch>.md` if it should be advisory for that task type.

---

## What this doc is NOT

- **Not loaded by agents.** Agents use `ROUTING.md` + `.claude/routing/*.md` + `.claude/registry/*.json`.
- **Not the routing source of truth.** When this doc drifts from the routing files / registry, the routing files / registry are correct.
- **Not exhaustive.** Only the items actively referenced by routing branch files. The full ECC catalog is ~421 items; this curated subset is ~46.
- **Not validated.** The strict validator does not scan this file. References here can fall out of date silently; cross-reference with `npm run rebuild-registry` output before relying on a claim made here.
