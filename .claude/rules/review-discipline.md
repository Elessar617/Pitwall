# Rule: Review discipline (multi-agent gate)

**Reviewer + adversary subagents both run before any iteration moves to `build/workflows/*/04-output/`. After 5 failed cycles, the orchestrator halts.**

**Why:** The reviewer checks compliance with the spec. The adversary checks for things the spec did not anticipate. Both run because they fail differently: the reviewer catches "you did the wrong thing"; the adversary catches "you did the right thing in a way that breaks under conditions you didn't think about."

**How to apply:**
- The reviewer agent (`.claude/agents/reviewer-agent.md`) writes `03-validate/review-N.md` with frontmatter `verdict: pass | fail`.
- The adversary agent (`.claude/agents/adversary-agent.md`) writes `03-validate/adversary-N.md` with frontmatter `findings: none | minor | critical`.
- Promotion to `04-output/` requires, on the same cycle: `verdict: pass` AND `findings: none|minor` (deferred). Enforced by `block-output-without-signoff.sh`.
- A failing cycle (reviewer rejects OR adversary finds critical) goes back to the implementer with both reports as input.
- Cycle count: each new `review-N.md` is a new cycle. After **5** failed cycles, the orchestrator stops and escalates to the human. Enforced by `block-cycle-overrun.sh`. Do not silently keep cycling — at 5 cycles the spec is likely wrong.
- The reviewer and adversary are SEPARATE subagents with isolated contexts. The reviewer must not see the implementer's reasoning beyond what's in the diff and `02-implement/notes-N.md`. The adversary must not see the reviewer's findings (they review in parallel, not in series, on each cycle).
- Reviewer + adversary apply equally to features, bugs, and refactors that flow through `build/`. Lab spikes do not require this gate (the spike's `REPORT.md` is the equivalent).
