# Iteration Process — End to End

How a unit of work travels from idea to shipped code in this repo.

## The two iteration types

- **Lab iteration** (`lab/NN-<slug>/`) — exploratory, output is a learning, not code.
- **Build iteration** (`build/workflows/NN-<slug>/`) — production, output is shipped code.

Both are numbered, both have a template (`00-template/` in each workspace), both are append-only.

## Lab iteration lifecycle

```
Open question
   │
   ▼
Copy lab/00-template/ → lab/NN-<slug>/
   │
   ▼
Author PREFLIGHT.md  (hypothesis, prior art, success/failure criteria, time box)
   │
   ▼
Build prototype/ within the time box
   │
   ▼
Write VERIFY.md  (what was tested, findings)
   │
   ▼
Write REPORT.md  (decision: Pursue | Modify | Abandon)
   │
   ├── Pursue   → write spec/ artifact → start build/workflows/NN-<slug>/
   ├── Modify   → next lab iteration with revised PREFLIGHT
   └── Abandon  → write docs/explorations/NN-<slug>.md (preserve learning)
```

## Build iteration lifecycle

```
spec/ artifact OR lab/NN/REPORT.md (Pursue)
   │
   ▼
Copy build/workflows/00-template/ → build/workflows/NN-<slug>/
   │
   ▼
Planner agent writes 01-spec/SPEC.md  (one-shot)
   │
   ▼
LOOP (max 5 cycles, hook-enforced):
   ├─ Implementer writes code → src/ + notes-N.md → 02-implement/
   ├─ Reviewer writes review-N.md → 03-validate/  (parallel with adversary)
   ├─ Adversary writes adversary-N.md → 03-validate/  (parallel with reviewer)
   └─ Orchestrator: pass + clean? exit. Otherwise: increment N, loop.
   │
   ▼ (only on pass + clean)
04-output/OUTPUT.md  (signed off, PR-ready)
   │
   ▼
ship/changelog/ entry; ship/docs/ updated; src/ merged
```

## Numbering rules

- `NN` is zero-padded (`01`, `02`, … `99`, `100+`).
- Numbers are repo-wide-unique within each workspace (`lab/01` and `build/workflows/01` are independent).
- `00-template/` is reserved.
- Numbers never reused. If `lab/03` is abandoned, `lab/04` is the next spike (not `lab/03-v2`).

## When to use what

- **Don't know if X is feasible** → `lab/`
- **Need a decision recorded** → `spec/adrs/`
- **Want to propose a change** → `spec/rfcs/`
- **Have a small task to assign** → `spec/briefs/`
- **Building, fixing, or refactoring production code** → `build/workflows/`
- **Cutting a release** → `ship/`
