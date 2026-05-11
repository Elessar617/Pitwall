# Iteration Pattern

This file documents the canonical shape of a numbered iteration in this repo. Two iteration types exist: `lab/` (exploratory) and `build/workflows/` (production). They share a numbering convention and an outcome-orientation; their internal structure differs.

## Numbering

- Format: `NN-<slug>/` where `NN` is zero-padded (`01`, `02`, … `99`, `100`+).
- `00-template/` is reserved for the iteration template itself; copy from there to start a new iteration.
- The slug is `kebab-case`, descriptive in 2–5 words: `01-graphql-eval`, `07-fix-login-loop`.
- Iterations are append-only: `02` doesn't replace `01`, even if it supersedes it. Both stay in the tree as historical record.

## `lab/NN-<slug>/` — exploratory iteration

Files (copy from `lab/00-template/`):

| File | Purpose | Written when |
|---|---|---|
| `PREFLIGHT.md` | Hypothesis + prior art + success/failure criteria + time box | BEFORE any prototype code |
| `prototype/` | Throwaway code | DURING the spike |
| `VERIFY.md` | Tests performed, findings, surprises, limitations | AFTER prototype runs |
| `REPORT.md` | Decision: pursue, modify, abandon | AFTER VERIFY |

Outcomes:
- **Pursue** → write a `spec/` artifact, then start `build/workflows/NN-<slug>/`.
- **Modify** → next lab iteration with revised hypothesis.
- **Abandon** → write `docs/explorations/NN-<slug>.md` to preserve the learning.

## `build/workflows/NN-<slug>/` — production iteration

Stages (copy from `build/workflows/00-template/`):

| Stage | Folder | Owner | Output file pattern |
|---|---|---|---|
| 01 — Spec | `01-spec/` | planner agent (one-shot) | `SPEC.md` |
| 02 — Implement | `02-implement/` | implementer agent (cycle) | `notes-<cycle>.md` (code goes to `src/`) |
| 03 — Validate | `03-validate/` | reviewer + adversary agents (parallel each cycle) | `review-<cycle>.md`, `adversary-<cycle>.md` |
| 04 — Output | `04-output/` | orchestrator (after sign-off) | `OUTPUT.md` |

Cycle cap: 5 (enforced by `block-cycle-overrun.sh`). After 5 failed cycles, escalate.
Sign-off: latest `review-N.md` verdict=pass AND latest `adversary-N.md` findings in {none, minor (deferred)}. Enforced by `block-output-without-signoff.sh`.

## Cross-iteration handoff

```
spec/<artifact>            ─┐
                            ├─▶ build/workflows/NN-<slug>/   (production)
lab/NN-<slug>/REPORT.md ────┘     │
   (Pursue outcome)              ├─▶ src/  (the code)
                                  ├─▶ ship/  (release artifacts)
                                  └─▶ docs/explorations/NN-<slug>.md  (post-mortem)

lab/NN-<slug>/REPORT.md  ──▶ docs/explorations/NN-<slug>.md  (Abandon outcome)
```

## What goes where (decision tree)

- **Question I want to answer** → `lab/`
- **Decision I want to record** → `spec/adrs/`
- **Proposal I want to discuss** → `spec/rfcs/`
- **Small task to assign** → `spec/briefs/`
- **Production code change** → `build/workflows/` (sourced from one of the above)
- **Release artifacts** → `ship/`
- **Reusable infrastructure** → `shared/`
- **The actual production code** → `src/`
