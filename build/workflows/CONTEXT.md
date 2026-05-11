# Workflows — The Build Pipeline

## What This Folder Is

The four-stage gated pipeline. Each iteration is `NN-<slug>/` with stages 01 → 02 → 03 → 04. The four-agent loop (planner → implementer ↔ reviewer ↔ adversary) runs over these stages.

```
01-spec/  →  02-implement/  →  03-validate/  →  04-output/
 (plan)        (build)            (review)        (done)
```

---

## Stage Routing

| Your Task | Input | Also Load | Output | Agent |
|-----------|-------|-----------|--------|-------|
| Plan iteration | Source artifact from `../../spec/` | `../.claude/agents/planner-agent.md`, `../.claude/reference/{project-architecture,tech-stack}.md`, `../.claude/rules/` | `01-spec/SPEC.md` | planner (one-shot) |
| Implement cycle | `01-spec/SPEC.md`, latest `03-validate/{review,adversary}-N.md` if any | `../.claude/skills/tdd-loop/SKILL.md`, `../.claude/rules/` (all 5), `../.claude/reference/tech-stack.md` | code in `../../src/`; `02-implement/notes-N.md` | implementer (cycle) |
| Review cycle | `01-spec/SPEC.md`, the diff | `../.claude/agents/reviewer-agent.md`, `../.claude/rules/` | `03-validate/review-N.md` | reviewer (cycle, parallel) |
| Adversary cycle | `01-spec/SPEC.md`, the diff | `../.claude/agents/adversary-agent.md` | `03-validate/adversary-N.md` | adversary (cycle, parallel) |
| Promote to output | latest `review-N.md` (verdict=pass) AND latest `adversary-N.md` (findings ∈ {none, minor}) | `01-spec/SPEC.md` (acceptance evidence) | `04-output/OUTPUT.md` | orchestrator |

---

## Stage Details

### 01-spec/

Planner agent's output. ONE file per iteration: `SPEC.md`. Re-planning produces a new SPEC (versioned in its header), not an in-place edit.

### 02-implement/

Implementer's working notes per cycle: `notes-1.md`, `notes-2.md`, etc. **The actual code lives in `src/` (or `shared/`), NOT here.** This folder is process; that folder is artifact.

### 03-validate/

Per-cycle reviewer + adversary reports: `review-1.md` + `adversary-1.md`, `review-2.md` + `adversary-2.md`, etc. Both run in parallel each cycle (no shared context within a cycle). Hook `block-cycle-overrun.sh` blocks at 5 cycles.

### 04-output/

The signed-off deliverable. Created only after the orchestrator confirms the latest cycle's reviewer and adversary both clear. Hook `block-output-without-signoff.sh` enforces this.

---

## Pipeline Rules

1. **Forward flow.** Stages 01 → 02 → 03 → 04. No skipping.
2. **Each agent loads only what it needs.** See routing table.
3. **Cycle counter increments per `review-N.md`.** Max 5 (hook-enforced).
4. **Code goes to `src/`, not `02-implement/`.** Reviewer flags violations.
5. **Sign-off is binary per cycle.** Pass + clean → 04-output. Anything else → next cycle.
