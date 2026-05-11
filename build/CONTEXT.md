# Build

## What This Workspace Is

The production pipeline. **All production code work flows through here** — features, bug fixes, refactors. Each unit of work is a numbered iteration in `workflows/NN-<slug>/` with the four-stage shape (spec → implement → validate → output) and the four-agent loop (planner → implementer ↔ reviewer ↔ adversary).

---

## What to Load

| Task | Load These | Skip These |
|------|-----------|------------|
| Plan a new iteration | the source artifact from `../spec/`, `../.claude/agents/planner-agent.md`, `../.claude/reference/project-architecture.md`, `../.claude/reference/tech-stack.md` | implementer/reviewer/adversary agent files (planner doesn't need them) |
| Implement a cycle | the iteration's `01-spec/SPEC.md`, latest `03-validate/review-N.md` and `adversary-N.md` if any, `../.claude/skills/tdd-loop/SKILL.md`, `../.claude/rules/` (all 5) | other workspaces' CONTEXT.md |
| Review a cycle | `01-spec/SPEC.md`, the diff, `../.claude/rules/` (all 5), `../.claude/agents/reviewer-agent.md` | the implementer's notes (read those LAST, not first) |
| Adversary a cycle | `01-spec/SPEC.md` (especially Risks), the diff, `../.claude/agents/adversary-agent.md` | the reviewer's findings (you run in parallel, not series) |
| Promote to output | latest `review-N.md` (verdict=pass) AND latest `adversary-N.md` (findings ∈ {none, minor}) | implement-cycle artifacts |

---

## Folder Structure

```
build/
├─ CONTEXT.md
└─ workflows/
   ├─ CONTEXT.md          ← pipeline routing
   ├─ 00-template/        ← copy this to start an iteration
   └─ NN-<slug>/
      ├─ 01-spec/SPEC.md           ← planner output
      ├─ 02-implement/notes-N.md   ← implementer process notes (CODE goes to src/)
      ├─ 03-validate/
      │  ├─ review-N.md           ← reviewer per cycle
      │  └─ adversary-N.md        ← adversary per cycle
      └─ 04-output/OUTPUT.md       ← signed-off deliverable
```

See `workflows/CONTEXT.md` for stage-by-stage routing.

---

## The Process

The four-agent loop is documented in `../docs/orchestrator-process.md`. In brief:

1. **Plan once:** orchestrator dispatches planner agent → SPEC.md.
2. **Loop until acceptance** (max 5 cycles, hook-enforced):
   - Implementer agent writes code to `src/` and notes to `02-implement/`.
   - Reviewer agent reads diff + SPEC.md, writes verdict to `03-validate/review-N.md`.
   - Adversary agent reads diff + SPEC.md (in parallel with reviewer), writes findings to `03-validate/adversary-N.md`.
   - If verdict=pass AND findings∈{none,minor}: promote to `04-output/`. Otherwise: next cycle.

The hooks (`block-cycle-overrun.sh`, `block-output-without-signoff.sh`) enforce both the cycle cap and the sign-off gate.

---

## Skills & Tools

| Skill / Tool | When | Purpose |
|-------------|------|---------|
| `/tdd-loop` | Implementer agent, every cycle | Mandatory test-first discipline |
| `/bug-investigation` | When the iteration is a bug fix (drives the SPEC shape) | Reproduce → diagnose → fix → regression test |
| `/refactor-protocol` | When the iteration is a refactor (drives the SPEC shape) | Behavior-equivalence proof + staged migration |
| Context7 MCP | Spec + implement | Up-to-date library docs |
| `github` MCP | Output stage | Open PRs, link issues, post updates |

---

## What NOT to Do

- Don't write code in `02-implement/` — that's process notes only. Code goes to `src/`.
- Don't skip the reviewer or adversary. They're hook-enforced gates, not optional quality checks.
- Don't keep cycling past 5. After 5 failed cycles, the spec is wrong; escalate.
- Don't bundle multiple iterations into one folder. One folder = one SPEC.md = one logical change.
- Don't load `lab/` or `ship/` here — those are different lifecycle stages.
