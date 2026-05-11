---
name: spike-protocol
description: Use when starting an exploratory iteration in lab/. Drives the PREFLIGHT → prototype → VERIFY → REPORT shape. Output is a learning, not shipped code.
---

# Spike Protocol

A spike is a time-boxed experiment whose output is a *decision*, not a deliverable. Code written in a spike is throwaway by default — promoted to `src/` only by going through `spec/` and `build/`.

## The shape

Every spike iteration is a folder under `lab/NN-<slug>/` (copy from `lab/00-template/`). It contains, in order:

1. **`PREFLIGHT.md`** — written before any code. Hypothesis + prior art + success/failure criteria + time box.
2. **`prototype/`** — the code. Throwaway. No production patterns required (no tests, no error handling, no logging) unless they're part of what you're testing.
3. **`VERIFY.md`** — written after running the prototype. Tests performed, findings, surprises, limitations.
4. **`REPORT.md`** — the decision. Pursue, modify, or abandon.

## Discipline

### Write PREFLIGHT first
Define success and failure criteria BEFORE writing the prototype. Otherwise you'll rationalize whatever the prototype produces as a "result." Use Web Search MCP to canvas prior art.

### Honor the time box
A spike that runs over its time box is a different kind of work. Stop, write the REPORT with what you have, and decide explicitly whether the spike continues with a new (longer) time box or transitions into spec/build.

### The prototype is not the deliverable
If the spike's outcome is "Pursue," the prototype's role is over. Write a `spec/rfcs/` document or `spec/briefs/` entry, then start a fresh `build/workflows/NN-<slug>/` iteration. Do NOT promote the prototype code directly to `src/` — it will carry the throwaway code's compromises into production.

### Abandoned spikes are valuable
If REPORT outcome is "Abandon," write a `docs/explorations/NN-<slug>.md` so the next person investigating the same question doesn't repeat the work. State what was tried, what didn't work, and *why* — the why is the load-bearing part.

## When NOT to use this skill

- The work is "build feature X" — that's `build/`, not `lab/`. Even if you don't know exactly how, the planner agent's job is to figure out how.
- The work is a bug investigation — use `bug-investigation` skill, drives `build/`.
- The work is a refactor — use `refactor-protocol` skill, drives `build/`.
- You already know the answer — that's a spec, not a spike.
