# Spec: Resync Pitwall scaffold with workspace-blueprint

**Status:** Draft — awaiting user review
**Date:** 2026-05-12
**Author:** Planning session (gardnerwilson + Claude)
**Related:** [`docs/superpowers/specs/2026-05-11-pitwall-design.md`](2026-05-11-pitwall-design.md), [`docs/superpowers/specs/2026-05-10-workspace-blueprint-software-redesign-design.md`](2026-05-10-workspace-blueprint-software-redesign-design.md)

---

## 1. Context

Pitwall was scaffolded from [`workspace-blueprint`](https://github.com/Elessar617/workspace-blueprint) at commit `ce97dd9` ("initial scaffold from workspace-blueprint"). Since then, blueprint has shipped ~30 commits adding a significant new subsystem:

- **Routing/registry layer** (`ROUTING.md`, `.claude/routing/`, `.claude/registry/`, `route-inject.sh` hook) — auto-narrows context per task.
- **ECC submodule** (`external/ecc/`, vendored from `affaan-m/everything-claude-code`) — supplies registry content.
- **Multi-IDE preambles** (`AGENTS.md`, `GEMINI.md`, `.cursorrules`, `.codex/`, `.agents/`, `.superpowers/`).
- **Node tooling** (`package.json`, `package-lock.json`, scripts under `scripts/`).
- **4 new skills** (`brainstorming`, `karpathy-guidelines`, `systematic-debugging`, `writing-plans`).
- **2 new rules** (`nasa-power-of-10.md`, `unix-philosophy.md`).
- **Living docs** (`docs/development-log.md`, `docs/audit/`, `docs/limitations-and-deferred.md`).
- **`tests/`** at repo root.

Pitwall is early enough in development that adopting these now is cheap. Once src/pitwall grows large or a long-lived iteration is in-flight, the cost rises sharply.

This spec defines the migration so it can be executed without losing:
- F1 domain content (`data/`, `src/pitwall/`, `lab/01-openf1-feed-eval/`, F1 facts in `.claude/reference/`, F1 terms in `.portability-deny.txt`, F1 specs under `docs/superpowers/`).
- Pitwall-specific software-dev customizations (project-specific MCP configurations, build/test command choices, project-architecture decisions added since the scaffold).

## 2. Goal

End state: Pitwall has every blueprint feature listed above, AND retains all F1 domain content AND retains all Pitwall-specific software-dev choices. The merge is performed on a feature branch with one logical step per commit, then opened as a PR against main.

## 3. Non-goals

- **Wiring new skills/rules into existing Pitwall workflows.** That's a follow-up iteration after the scaffold lands.
- **Editing existing Pitwall specs** (`2026-05-11-pitwall-design.md`, `2026-05-11-pitwall-v01-season-tracker.md`). They are Pitwall artifacts, not scaffold artifacts.
- **Touching `faceoff/`** (gitignored reference repo) or **`data/`** (runtime data).
- **Re-running the planner agent for any in-flight Pitwall iteration.**

## 4. Success criteria

The migration is complete when every item below is verifiably true. None are aspirational.

1. `./scripts/bootstrap.sh` from a fresh clone of the merged result exits 0.
2. `node scripts/rebuild-registry.mjs` exits 0.
3. `npm run rebuild-registry` succeeds AND blueprint's bootstrap step that "validates that every name referenced in `ROUTING.md` resolves to a registry entry" (per blueprint README) passes — confirm by inspecting `bootstrap.sh` and running the validation it invokes.
4. All 5 hooks execute without error on a sample edit: `block-cycle-overrun`, `block-output-without-signoff`, `enforce-portability`, `pre-commit-tdd`, `route-inject`.
5. `enforce-portability.sh` FAILS when fed a synthetic edit to `.claude/rules/code-quality.md` containing an F1 deny-term. (Proves the deny-list is wired.)
6. `pre-commit-tdd.sh` FAILS when fed a synthetic new-file commit lacking a test. (Proves TDD enforcement still active.)
7. `diff -r <main>:src/pitwall <branch>:src/pitwall` is empty. (F1 source untouched.)
8. `diff -r <main>:data <branch>:data` is empty.
9. `diff -r <main>:lab/01-openf1-feed-eval <branch>:lab/01-openf1-feed-eval` is empty.
10. `diff -r <main>:shared <branch>:shared` is empty.
11. `grep -r "fastf1\|openf1\|jolpica" .claude/reference/` returns hits — F1 facts present in the new reference files.
12. `grep -rE "fastf1|openf1|jolpica|pitwall|formula" .claude/rules/ .claude/skills/` returns ZERO hits outside vendored office-skill paths. (Portability preserved.)
13. Every F1 term that appeared in pre-merge `.claude/reference/*.md` is present in post-merge `.claude/reference/*.md` (checklist from `.migration-scratch/pitwall-overlay.md` cleared).
14. Every Pitwall-specific software-dev customization that appeared in pre-merge `.claude/reference/*.md`, `.claude/settings.json`, `.claude/MCP-SETUP.md`, `CLAUDE.md`, `CONTEXT.md`, `README.md`, `START-HERE.md` is present in their post-merge counterparts (same checklist).
15. `git log main..chore/blueprint-resync --oneline` shows 22 commits — one logical change per commit; no mega-commits (with the exception of B1 which is intentionally a single bulk commit for the wholesale overlay, reviewable by `diff -r` against blueprint).
16. The PR is merged with a merge commit (not squashed); per-step history is preserved on main.

## 5. Architecture / approach

### 5.1. Branching

- Base: `main` at current HEAD (`7c58a34` at time of writing).
- Feature branch: `chore/blueprint-resync`.
- Source for new content: local `workspace-blueprint` checkout at `/Users/gardnerwilson/workspace/github.com/elessar617/workspace-blueprint`.
- Integration mechanic: per-file copy (additive paths) or per-file overwrite + manual replay (shared paths). NOT a git merge across unrelated histories.

### 5.2. Pre-flight snapshot (the safety net)

Before any overlay commit, capture Pitwall's pre-merge state of every file that will be overwritten. This is the sole rollback guarantee for the "blueprint wins" replay strategy.

Snapshot location: `.migration-scratch/` (added to `.gitignore` for the duration; deleted in the final commit).

Contents:

- `pitwall-pre-resync/.claude/reference/*.md` — all 7 differing reference files.
- `pitwall-pre-resync/.claude/.portability-deny.txt`.
- `pitwall-pre-resync/.claude/{settings.json,settings.local.json,MCP-SETUP.md}`.
- `pitwall-pre-resync/.claude/hooks/*.sh` — all 4 differing hooks (for diffing only; we adopt blueprint's).
- `pitwall-pre-resync/{CLAUDE.md,CONTEXT.md,README.md,START-HERE.md}`.
- `pitwall-overlay.md` — flat checklist of every piece of content (F1 domain OR software-dev customization) that must be replayed onto blueprint's versions. Generated by hand-scanning the snapshot above. Two sections:
  - **F1 domain content:** tyre compounds, FastF1, OpenF1, Jolpica, circuits, session types, etc.
  - **Software-dev customizations:** Pitwall-specific MCP configs, build/test commands, project-architecture choices, anything in `CLAUDE.md` or `CONTEXT.md` that describes Pitwall's stack/conventions.

### 5.3. Overlay commits (the merge itself)

> **Revision note (2026-05-12):** The original spec proposed an 11-commit Phase B (additive) + 8-commit Phase C (replace+replay). Adversary review (`2026-05-12-blueprint-resync-adversary-review.md`) flagged the intermediate "blueprint without F1" states in commits C4/C7 as an aesthetic friction worth removing. Revised sequence below: **a single wholesale-overlay commit** brings blueprint content in across all files at once, then **purely additive replay commits** layer F1 + dev content back onto the new base. Same end-state; same git history preservation; no per-file lossy intermediate state.

Each item below is exactly one commit. Type prefixes follow `.claude/rules/commit-discipline.md`.

**Phase A — pre-flight (no scaffold changes yet):**

| # | Commit | Description |
|---|---|---|
| A1 | `chore(migration): snapshot pre-resync state` | Add `.migration-scratch/pitwall-pre-resync/` + `pitwall-overlay.md`. Add `.migration-scratch/` to `.gitignore` (rule says: this dir is temporary, will be deleted in final commit). |
| A2 | `chore(scaffold): remove empty build/workflows placeholders` | Delete `build/workflows/{01-spec,02-implement,03-validate,04-output}/` (all `.gitkeep`-only). Iterations get created on demand under `NN-slug/`. Done before B1 so the overlay doesn't have to worry about them. |

**Phase B — wholesale overlay (one big commit):**

| # | Commit | Description |
|---|---|---|
| B1 | `chore(scaffold): wholesale overlay of blueprint onto Pitwall` | Single `rsync -avc /path/to/workspace-blueprint/ ./ --exclude=.git --exclude=node_modules --exclude=external/ecc --exclude=.serena --exclude=.remember` — note `-c` (checksum mode) to compare by content rather than mtime, avoiding spurious "transfers" of byte-identical files. Result: every blueprint file is now in Pitwall; shared files hold blueprint's versions. Pitwall-exclusive directories (`data/`, `src/pitwall/`, `shared/`, `lab/01-openf1-feed-eval/`, `spec/briefs/pitwall-overview.md`, `docs/teaching/`, `docs/superpowers/{specs,plans}/2026-05-1{1,2}-pitwall-*`) are **untouched** by `rsync` because it doesn't delete dest-only files when `--delete` is omitted. Run `npm install` locally for verification (do NOT commit `node_modules/`).<br><br>**Confirmed overwrite list (20 files, verified via dry-run on 2026-05-12):** `.gitignore`, `CLAUDE.md`, `CONTEXT.md`, `README.md`, `START-HERE.md`, `.claude/.portability-deny.txt`, `.claude/MCP-SETUP.md`, `.claude/settings.json`, `.claude/settings.local.json`, `.claude/hooks/{block-cycle-overrun,block-output-without-signoff,enforce-portability,pre-commit-tdd}.sh`, `.claude/reference/{claude-platform-capabilities,external-resources,frontend-stack,glossary,mcp-servers,project-architecture,tech-stack}.md`. Each is the target of an explicit replay commit in Phase C (no overwrite goes unreconciled). |

**Phase C — additive F1 + dev replays (every commit is purely additive against B1's state):**

Order is dependency-driven: deny list first (so portability hook is sane during subsequent replays), then reference files, then top-level docs, then settings reconciliation. Each commit clears its corresponding section of `.migration-scratch/pitwall-overlay.md`.

| # | Commit | Description |
|---|---|---|
| C1 | `chore(portability): restore Pitwall deny terms` | Re-add Pitwall's 32 F1 terms under the existing `# Pitwall (Formula 1 TUI)` header in `.claude/.portability-deny.txt`. **Must precede any C2-C11 commit that mentions an F1 term**, or the portability hook will block the edit. |
| C2 | `docs(reference): restore F1+dev content in tech-stack.md` | Replay F1 facts and Pitwall software-dev customizations from snapshot into `.claude/reference/tech-stack.md` (additive against B1's blueprint version). |
| C3 | `docs(reference): restore F1+dev content in frontend-stack.md` | Same pattern for `frontend-stack.md`. |
| C4 | `docs(reference): restore F1+dev content in project-architecture.md` | Same pattern. |
| C5 | `docs(reference): restore F1+dev content in glossary.md` | Same pattern. |
| C6 | `docs(reference): restore F1+dev content in external-resources.md` | Same pattern. |
| C7 | `docs(reference): restore F1+dev content in mcp-servers.md` | Same pattern. |
| C8 | `docs(reference): restore F1+dev content in claude-platform-capabilities.md` | Same pattern. |
| C9 | `docs(routing): restore Pitwall identity in CLAUDE.md` | Re-add Pitwall's "What This Repo Is" section to CLAUDE.md (additive against B1). |
| C10 | `docs(routing): restore Pitwall framing in CONTEXT.md` | Same pattern. |
| C11 | `docs(routing): restore Pitwall framing in README.md` | Same pattern. |
| C12 | `docs(routing): restore Pitwall framing in START-HERE.md` | Same pattern. |
| C13 | `chore(scaffold): reconcile settings.json with Pitwall customizations` | Diff snapshot `pitwall-pre-resync/.claude/settings.json` against current state; replay any Pitwall-specific MCP entries / hook profile choices. If snapshot equals blueprint's, this commit is a no-op and can be dropped. |
| C14 | `chore(scaffold): reconcile settings.local.json with Pitwall customizations` | Same pattern as C13. |
| C15 | `chore(scaffold): reconcile MCP-SETUP.md with Pitwall customizations` | Replay Pitwall-specific MCP setup notes (if any) into the new MCP-SETUP.md. |
| C16 | `chore(scaffold): reconcile .gitignore with Pitwall patterns` | Pitwall's `.gitignore` has F1-specific patterns: `data/*.db`, `data/*.sqlite`, `data/*.sqlite3`, `data/*.db-journal`, `faceoff/`. Add these back to the now-blueprint-versioned `.gitignore`. Confirm `node_modules/` is present (likely already in blueprint's version). |

**Phase D — finalize and cleanup:**

| # | Commit | Description |
|---|---|---|
| D1 | `chore(scaffold): adopt ECC submodule` | `git submodule add https://github.com/affaan-m/everything-claude-code.git external/ecc`. Confirm `.gitmodules` written and `external/ecc/` populated. Pin the submodule to the SHA that was current in blueprint at the time of B1 — get it from blueprint's `.git/modules/external/ecc/HEAD` or `git submodule status` in blueprint. Done in Phase D rather than B1 because `git submodule add` is a git-aware operation that has to be its own commit, not part of an `rsync`. |
| D2 | `chore(scaffold): post-replay registry rebuild` | Run `npm run rebuild-registry`. Commit any registry changes that result from C1–C15's content edits (the registry indexes `.claude/` content). If the rebuild produces no diff, this commit is a no-op and can be dropped. |
| D3 | `chore(migration): remove .migration-scratch/` | Delete the scratch dir and revert the `.gitignore` entry. Final state: only the intentional changes remain. |

Total: **2 + 1 + 16 + 3 = 22 commits** (one more than the original draft after adding the explicit `.gitignore` reconciliation in C16; structure now is one wholesale-overlay commit plus 16 purely additive replays, instead of 11 additive + 8 replace-and-replay).

### 5.4. Verification gate

Before opening the PR, run the success-criteria checks (Section 4) in order. Each is pass/fail. A failure means fix-in-place on the branch and re-run. Document the verification results in the PR body.

### 5.5. PR + merge

- `git push -u origin chore/blueprint-resync`.
- `gh pr create` with title `chore: resync scaffold with workspace-blueprint`.
- Body lists each phase's commits, the verification results, and an explicit "merge commit, do not squash" note for the merger.
- User reviews + merges with merge commit. Per-step history lands on main as 22 reviewable commits.

### 5.6. Rollback

- **Mid-merge** (any commit fails or verification fails): branch is throwaway. `git checkout main && git branch -D chore/blueprint-resync`. Main is untouched.
- **Post-merge** (defect discovered after merge): `git revert -m 1 <merge-sha>`. Single atomic revert restores main to pre-resync state. F1 and dev content restorable from the revert's parent.

## 6. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| F1 content silently dropped by `rsync` overlay in B1 | High | `rsync` without `--delete` is **default-keep** for dest-only files — Pitwall-exclusive dirs survive automatically. Snapshot in A1 is the second safety net. Verification gates 7–10 in Section 4 confirm exact preservation. |
| Pitwall software-dev customizations lost (non-F1 but project-specific) inside shared files | High | Snapshot + checklist (`pitwall-overlay.md`) has a dedicated "software-dev customizations" section. C2–C15 replays clear it explicitly. |
| Portability hook blocks a C2–C12 commit because an F1 term lands before deny-list update | Medium | C1 (deny-list restore) is sequenced FIRST in Phase C precisely for this reason. If a portability failure occurs in C2–C12, re-inspect deny list before debugging the content. |
| Registry stale after F1 replays (registry indexes `.claude/` content) | Medium | D2 rebuilds the registry post-replay and commits any diff. Verification gates 2–3 in Section 4 confirm registry validity. |
| `rsync` accidentally includes blueprint-local cruft (`.serena/`, `.remember/`, `external/ecc/.git`) | Medium | B1 command excludes `.git`, `node_modules`, `external/ecc`, `.serena`, `.remember` explicitly. Dry-run with `rsync -avn` first; eyeball the file list before committing. |
| ECC submodule URL or content changes upstream during merge | Low | Pin submodule to a specific SHA in D1; capture SHA from blueprint at B1 time; document in PR body. |
| `npm install` introduces a vulnerability or large transitive tree | Low | Adopting blueprint's already-pinned `package-lock.json` verbatim. Inspect post-install; if surprising, halt B1 (don't commit). |
| Hook semantics changed in blueprint and break Pitwall's current iteration state | Medium | No iteration in-flight (`build/workflows/` has only empty placeholders, removed in A2). Run all 5 hooks against synthetic edits as part of verification gate. |
| Blueprint's `tests/` collides with Pitwall test layout | Low | `tests/` enters via B1 wholesale-overlay. Pre-B1 dry-run inspection: if blueprint's `tests/` would clobber a Pitwall file, halt and reassess (Pitwall currently has no `tests/` so risk is theoretical). |
| Routing/registry script depends on a Node version Pitwall doesn't have | Low | Adopt blueprint's `package.json` engines field as-is; verify `npm install` and `bootstrap.sh` run on local node before committing B1. |

## 7. Out of scope (explicit deferrals)

- Adopting any blueprint workflow currently mid-iteration in blueprint (e.g., the ECC bridge plan). Pitwall takes the *output* (registry, scripts, ROUTING.md) but not blueprint's open work.
- Rewriting Pitwall's existing v0.1 season-tracker plan to use new skills.
- Tuning the behavior of the adopted GitHub Actions workflows. The workflows themselves are adopted in B11; tightening or extending them is a follow-up.
- Migrating `docs/explorations/` format if blueprint's has diverged — if a collision is detected during B10, defer the format-migration to a separate iteration; the goal of this iteration is structural sync, not content reformatting.

## 8. Open questions

None at design time. Three were raised and resolved during brainstorming + adversary review:

- **Merge commit vs squash on PR**: merge commit. Per-step audit trail goes on main.
- **Commit granularity**: 22 commits as listed. No combining.
- **Wholesale-overlay vs file-by-file replace+replay**: wholesale-overlay (B1 single commit) chosen after adversary review. Eliminates the per-file lossy intermediate state of the original spec while keeping the same end-state, the same git history, and the same verification gates.

## 9. Process

Authored via `superpowers:brainstorming`. Next step per skill flow: invoke `superpowers:writing-plans` to produce the executable implementation plan in `docs/superpowers/plans/2026-05-12-blueprint-resync-plan.md`.

