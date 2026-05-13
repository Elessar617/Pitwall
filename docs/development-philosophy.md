# Development Philosophy

> Principles that govern how we work in this repo. Most are already enforced by `.claude/rules/`, `.claude/hooks/`, or the four-agent loop. This file is the *explicit* statement of the *implicit* discipline, so a new contributor can read it once and operate consistently.

## Measure twice, cut once

**Write the spec before the code. Write the verification before doing the work.**

- Every iteration starts with a spec (`01-spec/SPEC.md` for `build/` iterations; `docs/superpowers/specs/` for cross-cutting designs). Implementers receive a spec; they do not invent one.
- Every spec has explicit, verifiable success criteria. "Make it work" is not a success criterion. "`./scripts/bootstrap.sh` exits 0" is.
- For destructive operations (migrations, deletions, force-pushes): **dry-run first, eyeball the output, then do it for real.** The blueprint resync used `rsync -avnc` (dry-run, checksum) to confirm exactly 20 overwrites before running `rsync -avc` for real.
- For replace-and-replay operations: **snapshot the pre-state into a scratch directory before the replace**, so the replay has a source of truth and the rollback path is mechanical.

## Reversibility over speed

**Prefer the action that's easy to undo.**

- Branch first, commit second. `git branch -D` an unmerged branch is reversible; reverting a merged commit is two more commits of churn.
- New commits over `--amend` on pushed commits. Amend only locally before pushing.
- Never `--no-verify`. The hook is telling you something real. If the hook is wrong, fix the hook.
- For changes affecting shared state (push, PR, gh actions): pause and confirm before executing.

## One logical change per commit

**Each commit is a unit of revertibility.**

- A commit that mixes a feature, a refactor, and a typo fix can't be cleanly reverted if any of the three turns out wrong.
- Conventional Commits format (`feat(scope): ...`, `fix: ...`, `chore: ...`) — see [`.claude/rules/commit-discipline.md`](../.claude/rules/commit-discipline.md).
- Per-file commits when reasonable. Per-concept commits when granularity would over-fragment.
- Mega-commits (e.g., the blueprint resync's wholesale-overlay commit B1) are allowed *only* when reviewing the diff is impractical anyway — and only when the spec calls them out as such.

## TDD where TDD applies; checklist where it doesn't

**Production code: tests first. Migrations and scaffolding: checklists first.**

- For application code in `src/pitwall/`: red → green → refactor. The `pre-commit-tdd.sh` hook enforces this. See [`.claude/rules/testing-discipline.md`](../.claude/rules/testing-discipline.md) and [`.claude/skills/tdd-loop/`](../.claude/skills/tdd-loop/).
- For migrations, scaffolding, and one-off operations: **write the verification gates before the operation. Tick them as they pass.** The blueprint resync used this pattern: 16 success criteria authored in the spec; the plan's verification phase walked through them one by one.
- For exploratory spikes in `lab/`: no test discipline required; the spike's `REPORT.md` is the deliverable. See [`.claude/skills/spike-protocol/`](../.claude/skills/spike-protocol/).
- For bug fixes: **write a failing test that reproduces the bug, *then* fix it.** See [`.claude/skills/bug-investigation/`](../.claude/skills/bug-investigation/).

## Reviewer + adversary on every build iteration

**Two failure modes, two reviewers.**

- The **reviewer** ([`.claude/agents/reviewer-agent.md`](../.claude/agents/reviewer-agent.md)) checks compliance with the spec — *"did you do the right thing?"*
- The **adversary** ([`.claude/agents/adversary-agent.md`](../.claude/agents/adversary-agent.md)) checks for things the spec didn't anticipate — *"did you do the right thing in a way that breaks under conditions you didn't think about?"*
- Both run on every cycle. After 5 failed cycles, the orchestrator halts and escalates — the spec is likely wrong. See [`.claude/rules/review-discipline.md`](../.claude/rules/review-discipline.md).
- This pattern applies to `build/workflows/NN-<slug>/` iterations. Cross-cutting designs (under `docs/superpowers/`) can use the pattern informally: pair a brainstorm-driven spec with an adversary review before writing the plan, as the blueprint resync iteration did.

## Portability discipline

**This scaffold is portable. Project-specific facts go in `.claude/reference/`, never in `.claude/rules/` or `.claude/skills/`.**

- New project-specific terms go in `.claude/.portability-deny.txt`. The `enforce-portability.sh` hook blocks edits that drag those terms into rules or skills.
- This rule exists so the scaffold can be lifted into the next project. It's not aesthetic — it's *load-bearing*. Bootstrap recipe in [`docs/teaching/bootstrap.md`](teaching/bootstrap.md).
- Pitwall's deny list contains 32 F1-domain terms (`fastf1`, `openf1`, `tyre compound`, `parc fermé`, etc.). New F1 terms get added to the deny list as they enter the codebase.

## Token discipline

**Each workspace is siloed. Don't load everything.**

- Working in `build/`? Load `build/CONTEXT.md`, the iteration's spec, the relevant agent files. Skip `spec/`, `lab/`, `ship/` CONTEXT.md.
- Working in `lab/`? Load `lab/CONTEXT.md` + the `spike-protocol` skill. Skip everything else.
- The "What to Load / Skip These" tables in each workspace's CONTEXT.md are the token budget.
- After the blueprint resync, automatic context narrowing is done via `ROUTING.md` + `.claude/routing/*.md` + the registry (`.claude/registry/*.json`). The `route-inject.sh` `UserPromptSubmit` hook surfaces relevant routing to the agent at task start.

## When to ask vs when to act

**Reversible local actions: act. Hard-to-reverse or shared-state actions: ask.**

- Freely: editing files, running tests, local commits on a feature branch.
- Ask first: pushing to remote, opening PRs, force-pushing, modifying CI, sending external messages, deleting branches, dropping data.
- "I once approved X" does not generalize to "always approve X" — match each action's scope to what was actually requested.

## Architectural decisions are durable; document them

**When you investigate something and discover a non-obvious fact, write it down where future-you will trip on it.**

- Pitwall's discovery that modern Claude Code silently ignores the `mcpServers` field in `.claude/settings.json` is captured in the `_mcpServersNote` field of `.claude/settings.json` itself — at the point of friction, not in a separate doc that nobody reads.
- The Phase D blueprint-resync conflict (between Pitwall's MCP architecture decision and the new routing-registry rebuilder) was resolved by the fix-up commit `ffdb14a`; the resolution is documented in the commit message AND in the expanded `_mcpServersNote` so the next person who reads `settings.json` understands the two consumers of `mcpServers`.

## What this file is NOT

- Not a checklist. Checklists are per-iteration, in the relevant plan.
- Not a substitute for the rules. The rules are the enforcement layer. This is the *narrative*.
- Not exhaustive. New principles get added here when a misstep would have been prevented by stating them. If the rule was already enforced by a hook, don't add it here.
