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
15. `git log main..chore/blueprint-resync --oneline` shows 21 commits — one logical change per commit; no mega-commits.
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

Each item below is exactly one commit. Type prefixes follow `.claude/rules/commit-discipline.md`. Order is additive-first, then replace-and-replay, so each commit reviews cleanly in isolation.

**Phase A — pre-flight (no scaffold changes yet):**

| # | Commit | Description |
|---|---|---|
| A1 | `chore(migration): snapshot pre-resync state` | Add `.migration-scratch/pitwall-pre-resync/` + `pitwall-overlay.md`. Add `.migration-scratch/` to `.gitignore` (rule says: this dir is temporary, will be deleted in final commit). |

**Phase B — additive (no existing Pitwall file touched):**

| # | Commit | Description |
|---|---|---|
| B1 | `chore(scaffold): remove empty build/workflows placeholders` | Delete `build/workflows/{01-spec,02-implement,03-validate,04-output}/` (all `.gitkeep`-only). Iterations get created on demand under `NN-slug/`. |
| B2 | `chore(scaffold): add routing+registry from blueprint` | Copy `ROUTING.md`, `SKILLS.md`, `.claude/routing/`, `.claude/registry/`, `.claude/hooks/route-inject.sh`. |
| B3 | `chore(scaffold): add multi-IDE preambles from blueprint` | Copy `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `.agents/`, `.codex/`, `.superpowers/`. |
| B4 | `chore(scaffold): add new skills from blueprint` | Copy `.claude/skills/{brainstorming,karpathy-guidelines,systematic-debugging,writing-plans}/` + `THIRD_PARTY_LICENSES.md`. |
| B5 | `chore(scaffold): add new rules from blueprint` | Copy `.claude/rules/{nasa-power-of-10.md,unix-philosophy.md}`. |
| B6 | `chore(scaffold): add npm tooling from blueprint` | Copy `package.json`, `package-lock.json`. Add `node_modules/` to `.gitignore` (Pitwall's `.gitignore` does not currently exclude it). Run `npm install` locally; do NOT commit `node_modules/`. |
| B7 | `chore(scaffold): add helper scripts from blueprint` | Copy `scripts/{bootstrap.sh,rebuild-registry.mjs,refresh-harness.sh,refresh-vendored.mjs,route.mjs,update-ecc.sh,with-profile.sh,lib/}`. Confirm executable bits. |
| B8 | `chore(scaffold): adopt ECC submodule` | `git submodule add https://github.com/affaan-m/everything-claude-code.git external/ecc`. Confirm `.gitmodules` written and `external/ecc/` populated. |
| B9 | `chore(scaffold): add tests/ scaffolding from blueprint` | Copy `tests/`. **Pre-copy check:** inspect for F1-collision (file names, content). If any file collides with Pitwall content, halt and reassess. |
| B10 | `chore(scaffold): add blueprint living docs` | Copy `docs/development-log.md`, `docs/audit/`, `docs/limitations-and-deferred.md`. **Pre-copy:** confirm no collision with `docs/teaching/bootstrap.md` or any existing Pitwall doc. |
| B11 | `chore(ci): add .github/workflows from blueprint` | Copy `.github/workflows/`. **Pre-copy:** inspect each workflow file for blueprint-specific assumptions (paths, branch names). Adjust only what is mechanically wrong; otherwise adopt verbatim and defer behavior tuning to a follow-up. |

**Phase C — replace + replay (Pitwall files touched, blueprint wins, F1/dev info replayed):**

| # | Commit | Description |
|---|---|---|
| C1 | `chore(scaffold): adopt blueprint versions of 4 hooks` | Overwrite `.claude/hooks/{block-cycle-overrun,block-output-without-signoff,enforce-portability,pre-commit-tdd}.sh`. Hooks are portable; no replay needed. |
| C2 | `chore(scaffold): adopt blueprint settings.json` | Overwrite `.claude/settings.json` + `.claude/settings.local.json`. Replay Pitwall-specific MCP configs (from snapshot) inline in the same commit. |
| C3 | `chore(scaffold): adopt blueprint MCP-SETUP.md` | Overwrite `.claude/MCP-SETUP.md`. Replay Pitwall-specific MCP setup notes inline. |
| C4 | `chore(reference): adopt blueprint reference structure` | Overwrite all 7 differing `.claude/reference/*.md` with blueprint's versions. **This commit intentionally loses F1 + dev content; C5 restores it.** Reviewer sees a clean "structure adopted" diff. |
| C5 | `docs(reference): replay F1 + dev content onto reference files` | Add back every checklist item from `.migration-scratch/pitwall-overlay.md` into the corresponding `.claude/reference/*.md`. Tick each item as it lands. Verify checklist 100% cleared before committing. |
| C6 | `chore(portability): restore F1 deny terms` | Overwrite `.claude/.portability-deny.txt` with blueprint's base, then re-add Pitwall's 32 F1 terms under the existing `# Pitwall (Formula 1 TUI)` header. |
| C7 | `docs(routing): adopt blueprint CLAUDE.md/CONTEXT.md/README.md/START-HERE.md` | Overwrite. Like C4: intentionally loses Pitwall identity; C8 restores it. |
| C8 | `docs(routing): replay Pitwall identity onto top-level docs` | Re-add Pitwall's "What This Repo Is" section to CLAUDE.md; F1 framing to README.md; etc. Verify checklist cleared. |

**Phase D — cleanup:**

| # | Commit | Description |
|---|---|---|
| D1 | `chore(migration): remove .migration-scratch/` | Delete the scratch dir and revert the `.gitignore` entry. Final state: only the intentional changes remain. |

Total: **21 commits** (1 + 11 + 8 + 1).

### 5.4. Verification gate

Before opening the PR, run the success-criteria checks (Section 4) in order. Each is pass/fail. A failure means fix-in-place on the branch and re-run. Document the verification results in the PR body.

### 5.5. PR + merge

- `git push -u origin chore/blueprint-resync`.
- `gh pr create` with title `chore: resync scaffold with workspace-blueprint`.
- Body lists each phase's commits, the verification results, and an explicit "merge commit, do not squash" note for the merger.
- User reviews + merges with merge commit. Per-step history lands on main as 20 reviewable commits.

### 5.6. Rollback

- **Mid-merge** (any commit fails or verification fails): branch is throwaway. `git checkout main && git branch -D chore/blueprint-resync`. Main is untouched.
- **Post-merge** (defect discovered after merge): `git revert -m 1 <merge-sha>`. Single atomic revert restores main to pre-resync state. F1 and dev content restorable from the revert's parent.

## 6. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| F1 content lost during C4/C7 overwrites | High | Pre-flight snapshot (5.2). C5/C8 replay commits cleared against the explicit checklist. |
| Pitwall software-dev customizations lost (non-F1 but project-specific) | High | Same snapshot; checklist has a dedicated "software-dev customizations" section. |
| ECC submodule URL or content changes upstream during merge | Low | Pin submodule to a specific SHA in commit B8; document SHA in PR body. |
| `npm install` introduces a vulnerability or large transitive tree | Low | We're adopting blueprint's already-pinned `package-lock.json` verbatim. Inspect post-install; if surprising, halt B6. |
| Hook semantics changed in blueprint and break Pitwall's current iteration state | Medium | No iteration is currently in-flight (build/workflows has only empty placeholders). Run all 5 hooks against a synthetic edit as part of verification gate. |
| Blueprint's `tests/` collides with Pitwall test layout | Low | Pre-copy inspection in B9. If collision, halt and reassess scope. |
| Routing/registry script depends on a Node version Pitwall doesn't have | Low | Adopt blueprint's `package.json` engines field as-is; verify `bootstrap.sh` runs on local node. |

## 7. Out of scope (explicit deferrals)

- Adopting any blueprint workflow currently mid-iteration in blueprint (e.g., the ECC bridge plan). Pitwall takes the *output* (registry, scripts, ROUTING.md) but not blueprint's open work.
- Rewriting Pitwall's existing v0.1 season-tracker plan to use new skills.
- Tuning the behavior of the adopted GitHub Actions workflows. The workflows themselves are adopted in B11; tightening or extending them is a follow-up.
- Migrating `docs/explorations/` format if blueprint's has diverged — if a collision is detected during B10, defer the format-migration to a separate iteration; the goal of this iteration is structural sync, not content reformatting.

## 8. Open questions

None at design time. Two were raised and resolved during brainstorming:

- **Merge commit vs squash on PR**: merge commit. Per-step audit trail goes on main.
- **Commit granularity**: 20 commits as listed. No combining.

## 9. Process

Authored via `superpowers:brainstorming`. Next step per skill flow: invoke `superpowers:writing-plans` to produce the executable implementation plan in `docs/superpowers/plans/2026-05-12-blueprint-resync-plan.md`.

