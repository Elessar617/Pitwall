# Pitwall — Development Log

> **High-level project progress tracker.** Updated when iterations start, gate, or land. For per-iteration spec/plan detail, see `docs/superpowers/{specs,plans}/`. For development *principles*, see `docs/development-philosophy.md`. For the inherited scaffold history, see `docs/development-log.md`.

---

## Current state (as of 2026-05-12)

- **Branch:** `chore/blueprint-resync` (in-flight iteration 1; will return to `main` after merge)
- **Most recent merge:** *(none yet on Pitwall; iteration 1 will be the first PR)*
- **In-flight iteration:** Iteration 1 — resync scaffold with `workspace-blueprint`
- **Cycle count (out of 5):** 1/5
- **Blockers:** none (one architectural conflict surfaced and resolved mid-iteration; documented in iteration history below)

## Verification gate status (current iteration)

Filled in during Phase F verification. Pass/Fail/N/A per gate per the 16 success criteria in [`docs/superpowers/specs/2026-05-12-blueprint-resync-design.md`](docs/superpowers/specs/2026-05-12-blueprint-resync-design.md) Section 4.

| Gate | Pass / Fail / N/A | Last checked |
|---|---|---|
| 1. Bootstrap script (`./scripts/bootstrap.sh` exits 0) | Pass | 2026-05-12 |
| 2. Registry rebuild succeeds | Pass | 2026-05-12 |
| 3. ROUTING.md → registry resolution clean (all 7 routing files validated) | Pass | 2026-05-12 |
| 4. All 5 hooks parse cleanly (`bash -n`) | Pass | 2026-05-12 |
| 5. Portability hook rejects synthetic F1-term-in-rules edit (exit=1) | Pass | 2026-05-12 |
| 6. TDD hook rejects new-code-without-test commit (exit=1) | Pass | 2026-05-12 |
| 7. `src/pitwall/` untouched (0 lines diff vs main) | Pass | 2026-05-12 |
| 8. `data/` content untouched | Pass | 2026-05-13 |
| 9. `lab/01-openf1-feed-eval/` untouched (0 lines diff vs main) | Pass | 2026-05-12 |
| 10. `shared/` untouched (0 lines diff vs main) | Pass | 2026-05-12 |
| 11. F1 reference content present (grep verification: 8 hits) | Pass | 2026-05-12 |
| 12. Portability preserved (0 F1 hits in rules/non-vendored skills) | Pass | 2026-05-12 |
| 13. F1 replay checklist 100% cleared (16/16 ticked before scratch deletion) | Pass | 2026-05-12 |
| 14. Pitwall dev customizations preserved (`_mcpServersNote` + 16 `claude mcp add` refs) | Pass | 2026-05-12 |
| 15. Commit history is one logical change per commit (27 total branch commits; see notes) | Pass-with-note | 2026-05-13 |
| 16. No mega-commits except B1 (intentional wholesale overlay) | Pass | 2026-05-12 |

**Notes on gates:**

- **Gate 8 ("data/ untouched"):** reviewer re-check on 2026-05-13 caught an accidental tracked empty `data/telemetry.db` plus the missing `data/*.db` ignore rules. The tracked empty DB was removed and the runtime-cache ignore patterns were restored, so `data/` now matches `main` again except for the intentionally tracked `.gitkeep`.
- **Gate 15 ("22 commits"):** actual branch count is 27 from `main` at readiness. The count includes 4 planning/spec commits before implementation plus the reviewer corrective commit after Phase F. This differs from the original 22-commit implementation estimate, but the audit trail is still one logical change per commit and the only intentionally large commit remains B1, the wholesale overlay.

---

## Iteration history (newest first)

### Iteration 1: Resync scaffold with workspace-blueprint
- **Status:** in-progress (all 16 verification gates passed after reviewer re-check; ready for push + PR)
- **Branch:** `chore/blueprint-resync`
- **Spec:** [`docs/superpowers/specs/2026-05-12-blueprint-resync-design.md`](docs/superpowers/specs/2026-05-12-blueprint-resync-design.md) (commit `4763e7e`)
- **Adversary review:** [`docs/superpowers/specs/2026-05-12-blueprint-resync-adversary-review.md`](docs/superpowers/specs/2026-05-12-blueprint-resync-adversary-review.md) (commit `9fd3ef8`)
- **Plan:** [`docs/superpowers/plans/2026-05-12-blueprint-resync-plan.md`](docs/superpowers/plans/2026-05-12-blueprint-resync-plan.md) (commit `14ba2d4`)
- **PR:** *(URL after `gh pr create` in Phase F)*
- **Started:** 2026-05-12
- **Merged:** *(date)*
- **Commits in branch:** 27 at PR-open readiness
- **Cycles consumed:** 1/5 (no review-N.md / adversary-N.md cycle was used; this is a planner-driven iteration, not a `build/workflows/` iteration)
- **What landed (Phases A–E):**
  - Phase A: branch + snapshot + remove empty workflow placeholders (3 commits)
  - Phase B: wholesale `rsync -avc` overlay of `workspace-blueprint` onto Pitwall (1 commit, 91 files changed)
  - Phase C1–C8: F1 deny terms + 7 reference file F1/dev content replays (8 commits)
  - Phase C9–C12: 4 top-level doc identity replays (CLAUDE.md, CONTEXT.md, README.md, START-HERE.md)
  - Phase C13–C15: settings.json hook adoption, MCP-SETUP.md reconciliation (2 commits; settings.local.json was a no-op)
  - Phase C16: `.gitignore` reconciliation (no-op — maintainer's curated version already covered everything)
  - Phase D1: adopt ECC submodule pinned at `894ee039` (1 commit)
  - **Mid-iteration fix-up** (`ffdb14a`): the original C13 decision to remove `mcpServers` from `settings.json` conflicted with the new routing/registry rebuilder, which uses that field as its canonical MCP source for routing-file validation. Restored the `mcpServers` block and expanded `_mcpServersNote` to document both consumers. Surfaced by the Phase D implementer when `bootstrap.sh` failed validation.
  - Phase D2: registry rebuild (no-op — registry was already up-to-date after the fix-up).
  - Phase D3: scratch directory deleted (working-tree-only; `.gitignore` entry preserved for future migrations).
  - Phase E: this `DEVELOPMENT.md` plus `docs/development-philosophy.md` (2 commits).
  - **Reviewer readiness fix-up:** restored `data/*.db` ignore rules, removed accidental tracked empty `data/telemetry.db`, adapted the inherited source-of-truth test to Pitwall's tracked scaffold docs, and refreshed stale hook/skill-count docs.
- **What did NOT land (deferred):**
  - Wiring new skills (`brainstorming`, `writing-plans`, `systematic-debugging`, `karpathy-guidelines`) into Pitwall's iteration workflow conventions.
  - GitHub Actions behavior tuning (the workflows were adopted via rsync; behavior tuning is a follow-up).
  - `docs/explorations/` format migration (deferred per spec Section 7).
  - First Pitwall product iteration (the v0.1 season tracker plan exists at `docs/superpowers/plans/2026-05-11-pitwall-v01-season-tracker.md` but no `build/workflows/NN-slug/` started yet).

### Iteration 0: Initial scaffold
- **Status:** merged
- **Commit:** `ce97dd9` (`chore: initial scaffold from workspace-blueprint`) + 4 follow-ups: `dd7d0f3` (customize for Pitwall identity), `ab3b834` (seed planning + openf1 lab spike), `64207c9` (consolidated Pitwall v0.1→v1.0 design spec), `7c58a34` (v0.1 season tracker plan).
- **What landed:** Initial Pitwall scaffold from `workspace-blueprint`, Pitwall identity customization, planning seed including the OpenF1 lab spike (`lab/01-openf1-feed-eval/`), consolidated Pitwall design spec (v0.1 → v1.0), and the v0.1 season tracker implementation plan.

---

## Active follow-ups

*(Lightweight backlog. Promote each item to its own `build/workflows/NN-<slug>/` iteration when prioritized.)*

- [ ] Wire `brainstorming` / `writing-plans` / `systematic-debugging` / `karpathy-guidelines` skills into Pitwall's iteration workflow conventions (which skill an implementer reaches for first in each iteration type).
- [ ] Tune `.github/workflows/` for Pitwall-specific CI (Python tests, lint, type check on `src/pitwall/`).
- [ ] Start `build/workflows/01-<slug>/` for the v0.1 season tracker per the existing plan.
- [ ] Re-validate Pitwall's "Claude Code ignores `mcpServers` in `settings.json`" finding on a future Claude Code release; if Claude Code starts honoring the field again, simplify the `_mcpServersNote` accordingly.

---

## How to update this file

- After every PR merge, add an entry under "Iteration history" with the merged commits, what landed, what didn't.
- During an active iteration, keep "Verification gate status" current (re-run gates after each cycle, mark pass/fail).
- "Active follow-ups" is the lightweight backlog — promote items to formal iterations when ready.
- Don't put detail here that belongs in a spec or plan — link to those instead.
