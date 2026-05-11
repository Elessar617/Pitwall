# Common Mistakes (and How to Fix Them)

Earned mistakes from running this scaffold. Add to this list when you see a new pattern.

## 1. One giant `CLAUDE.md`

**What happens:** You put everything — full architecture, full conventions, full standards — into `CLAUDE.md` because it's "always loaded."

**Why it breaks:** `CLAUDE.md` is loaded in EVERY conversation. If it's 500 lines, you've burned tokens on iteration-process details when the agent is reviewing a one-line change.

**Fix:** `CLAUDE.md` = map only. Folder structure, naming conventions, cross-workspace flow, agent roles at a glance. Everything else lives in workspace `CONTEXT.md` files and `.claude/`.

## 2. No "Skip These" column

**What happens:** Your "What to Load" table tells agents what to read, but not what to ignore.

**Why it breaks:** Without explicit skip instructions, a thorough agent loads related-looking files "just in case." Wasted context, potential distraction.

**Fix:** Add the "Skip These" column. Be explicit about what's NOT needed for each task.

## 3. Skills listed but not triggered

**What happens:** You list skills in `CLAUDE.md` but never wire them into specific workflow moments.

**Why it breaks:** The agent knows `/tdd-loop` exists but doesn't know when to invoke it. It either invokes randomly or never.

**Fix:** Wire skills into `CONTEXT.md` routing tables with explicit trigger conditions. "Implementer agent, every cycle" is a trigger. "Available" is not.

## 4. Code in `02-implement/` instead of `src/`

**What happens:** The implementer agent writes the actual code under `build/workflows/NN/02-implement/` because the iteration is "scoped" there.

**Why it breaks:** Code that ships needs to live where the build/lint/deploy tools find it (`src/`). Splitting "process notes" from "shipped code" is the whole reason for the two-folder pattern.

**Fix:** Code goes to `src/`, period. `02-implement/notes-N.md` records what was done; `src/` IS what was done. The reviewer flags any code that ended up in `02-implement/`.

## 5. Project-specific terms leaking into `.claude/rules/` or `.claude/skills/`

**What happens:** Someone writes "Use Stripe webhooks for billing events" in `.claude/skills/data-analysis/SKILL.md`.

**Why it breaks:** When the scaffold is copied to a non-Stripe project, that skill becomes confusing or wrong.

**Fix:** The `enforce-portability.sh` hook catches this if `stripe` is in `.claude/.portability-deny.txt`. Add project-specific terms to that file as you encounter them. Move project-specific facts to `.claude/reference/` (which the consumer rewrites).

## 6. Skipping the reviewer or adversary

**What happens:** Implementer finishes a cycle and you (the orchestrator) decide it looks good and skip straight to `04-output/`.

**Why it breaks:** The hooks block you (`block-output-without-signoff.sh`), so you'll hit the wall. More importantly, the reviewer + adversary catch what you don't think to check.

**Fix:** Always run both, even for small iterations. For trivial work, the cycle is fast — but it's not optional.

## 7. Cycling past 5

**What happens:** Cycle 5 fails. You think "one more try" and start cycle 6.

**Why it breaks:** The hook blocks you (`block-cycle-overrun.sh`). Beyond that — at 5 cycles, the spec is wrong, not the implementation. More cycles won't fix that.

**Fix:** When the cycle cap is hit, stop. Write `04-output/ESCALATION.md`. Re-engage the planner with revised inputs. Open a NEW iteration.

## 8. Building the perfect structure before doing any work

**What happens:** You spend a week tuning `.claude/rules/`, perfecting every CONTEXT.md, before running a single iteration.

**Why it breaks:** You don't know what your project actually needs until you've run through the loop a few times. Pre-built rules will be wrong; pre-configured skills will be unused.

**Fix:** Run a few iterations first. Note what goes wrong. Then evolve the scaffold based on real friction, not anticipated friction.

## 9. Mixing iteration types in one folder

**What happens:** `lab/03-graphql-eval/` outgrows the spike shape and you start adding tests, CI configs, production code.

**Why it breaks:** `lab/` is throwaway. Code there isn't reachable from `src/` and won't be deployed. You're building a feature in the wrong workspace.

**Fix:** When a spike's outcome is "Pursue," CLOSE the lab iteration (write the REPORT), open a `spec/` artifact, then start a fresh `build/workflows/NN-<slug>/`. The prototype code stays in `lab/` as historical reference.

## 10. Editing accepted ADRs

**What happens:** A decision recorded in `spec/adrs/0003-use-postgres.md` turned out wrong. You edit the ADR.

**Why it breaks:** ADRs are append-only by convention. Editing erases history of what was decided when. Future readers won't understand why the codebase has Postgres-shaped seams if the ADR pretends Mongo was always the choice.

**Fix:** Write a NEW ADR (`0007-switch-to-mongo.md`) that supersedes the old one. Update the old ADR's status to "Superseded by 0007" and add a link. Never touch the rest of its body.
