# Lab

## What This Workspace Is

Numbered exploratory iterations. The output of work here is a *learning*, not shipped code. Spikes, library evaluations, performance investigations, "is X feasible?" questions all live here as `NN-<slug>/` folders.

---

## What to Load

| Task | Load These | Skip These |
|------|-----------|------------|
| Start a new spike | `00-template/`, `../.claude/skills/spike-protocol/SKILL.md` | other workspaces' CONTEXT.md |
| Continue an in-flight spike | the iteration's `PREFLIGHT.md` and `prototype/` files | other iteration folders |
| Promote a spike outcome | the iteration's `REPORT.md`, `../spec/CONTEXT.md` (for the destination format) | `prototype/` (it's done) |
| Run a data-heavy analysis spike | `../.claude/skills/spike-protocol/SKILL.md`, `../.claude/skills/data-analysis/SKILL.md` | code-execution-irrelevant skills |

---

## Folder Structure

```
lab/
├─ CONTEXT.md       ← you are here
├─ 00-template/     ← copy this to start a new iteration
│  ├─ PREFLIGHT.md
│  ├─ prototype/
│  ├─ VERIFY.md
│  └─ REPORT.md
└─ NN-<slug>/       ← e.g., 01-graphql-eval/
```

---

## The Process

1. Copy `00-template/` to `NN-<slug>/` (next sequential number).
2. Fill in `PREFLIGHT.md` BEFORE writing prototype code. Define success and failure criteria up front.
3. Build the prototype in `prototype/`. Throwaway code; no production patterns required.
4. Fill in `VERIFY.md` with what was actually tested.
5. Fill in `REPORT.md` with the outcome (Pursue / Modify / Abandon).
6. Honor the time box from PREFLIGHT. Spikes that overrun their box become explicit decisions, not pushed-through work.

Outcomes:
- **Pursue** → write a `spec/` artifact, then start `build/workflows/NN-<slug>/`.
- **Modify** → next lab iteration with revised hypothesis.
- **Abandon** → write `docs/explorations/NN-<slug>.md` to preserve the learning.

---

## Skills & Tools

| Skill / Tool | When | Purpose |
|-------------|------|---------|
| `/spike-protocol` | Driving any iteration here | PREFLIGHT → prototype → VERIFY → REPORT shape |
| `/data-analysis` | Spikes that involve computing something from data | Trigger phrasing for code execution |
| Web Search MCP | PREFLIGHT phase | Prior art and current state of the question |
| Context7 MCP | PREFLIGHT phase | Up-to-date docs for libraries being evaluated |

---

## What NOT to Do

- Don't promote prototype code directly to `src/`. Promote the *learning* via `spec/` → `build/`.
- Don't skip PREFLIGHT. A spike without success/failure criteria has no defined outcome.
- Don't run unboxed. If your time box is exceeded, write the REPORT with what you have and decide explicitly whether the spike continues with a new (longer) box.
- Don't load `build/` or `ship/` here — those are downstream workspaces.
