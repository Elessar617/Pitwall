# Orchestrator Process — Running the Build Loop

The orchestrator is the main Claude Code session in your terminal. It dispatches subagents (planner, implementer, reviewer, adversary) and runs the cycle. This document is the protocol — a fresh Claude session can pick it up here.

## When to engage the loop

- A `spec/` artifact is accepted AND a `build/workflows/NN-<slug>/` iteration has been created (with `00-template/` copied).
- For trivial work (one-line fixes, doc typos), the loop is overkill. Use single-agent for those — the loop is for non-trivial production iterations.

## Phase 1: Plan (one-shot)

1. **Identify the source artifact.** One of: `spec/rfcs/<slug>.md` (Accepted), `spec/adrs/<NNNN>-<slug>.md`, `spec/briefs/<slug>.md`, or `lab/NN-<slug>/REPORT.md` (Pursue).
2. **Dispatch the planner** via the `Agent` tool with `subagent_type: planner`. Pass the source artifact path and the iteration directory path.
3. **Verify** that `01-spec/SPEC.md` was created. If not, re-prompt the planner with the missing context. If it exists but is incomplete, treat it like the source-was-insufficient case and ask the human.
4. **Read the SPEC.md** yourself (the orchestrator) to know what's being built.

## Phase 2: Loop (max 5 cycles)

For cycle `N` (starting at 1):

### Step A: Implement

Dispatch the implementer (`subagent_type: implementer`). Pass:
- The iteration directory path
- The cycle number `N`
- The latest `review-(N-1).md` and `adversary-(N-1).md` if `N > 1`

The implementer writes code to `src/` and `02-implement/notes-N.md`, then commits per the commit-discipline rule.

### Step B: Validate (parallel)

Dispatch the reviewer AND adversary in parallel (single message with two `Agent` tool uses). Each receives:
- The iteration directory path
- The cycle number `N`
- The git diff for this cycle (typically `git diff <base-ref>..HEAD`; choose `base-ref` as the commit before this cycle's implementer commits)

Wait for both reports.

### Step C: Decide

Read `03-validate/review-N.md` frontmatter `verdict` and `03-validate/adversary-N.md` frontmatter `findings`.

| review.verdict | adversary.findings | Action |
|---|---|---|
| pass | none | Promote to 04-output |
| pass | minor | Promote to 04-output (defer minors to follow-up issues) |
| pass | critical | Next cycle (implementer addresses critical findings) |
| fail | * | Next cycle (implementer addresses review findings) |

### Step D: Cycle counter

If next cycle: `N += 1`. If `N > 5`, the `block-cycle-overrun.sh` hook will block your next write to `03-validate/`. Stop and escalate to the human:
- Write `04-output/ESCALATION.md` describing the cycles that ran and the unresolved findings.
- Likely action: re-engage the planner with revised inputs and start a NEW iteration directory (`build/workflows/<NN+1>-<slug>-v2/`).

## Phase 3: Output

When the loop exits to 04-output:

1. Dispatch a final pass (this can be the orchestrator itself, no subagent needed) to write `04-output/OUTPUT.md` with summary, commit/PR link, acceptance evidence, cycle count, and follow-ups.
2. Verify the output write was not blocked by `block-output-without-signoff.sh`. If it was, your sign-off detection in Step C was wrong; recheck.
3. Open a PR (manual or via `github` MCP) if the consumer repo's workflow uses PRs.
4. Update `ship/changelog/` if this is a release-worthy change.

## When to collapse the loop

For trivial iterations (one-line fixes, docs-only changes), the four-agent loop is overhead. The orchestrator can:
- Skip the planner if the brief is already SPEC-shaped enough to drop straight into `01-spec/SPEC.md`.
- Combine implementer + reviewer in one session if the diff is genuinely small (one file, < 50 lines).
- Skip the adversary if the change has no behavioral surface area (e.g., a typo fix).

These are exceptions, not defaults. The hooks still enforce the gates — you can't promote to `04-output/` without sign-off files in `03-validate/`. For collapsed cycles, write minimal `review-1.md` and `adversary-1.md` documenting the collapse rationale.

## Multiple iterations in flight

The orchestrator can run multiple iterations sequentially in one session, but NOT in parallel — subagent dispatch is shared session state, and interleaving cycles produces unreviewable history. Finish one iteration's loop before starting another.
