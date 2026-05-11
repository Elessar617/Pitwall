---
name: refactor-protocol
description: Use when undertaking a refactor, framework upgrade, or migration that changes structure without changing behavior. Enforces blast-radius analysis and behavior-equivalence proof.
---

# Refactor Protocol

Refactors flow through the same `build/` pipeline as features. The 01-spec/SPEC.md for a refactor differs in one way: it MUST contain a behavior-equivalence proof plan.

## The protocol

### 1. Plan (in 01-spec/SPEC.md)

Document:
- **What changes structurally:** files / modules / interfaces touched
- **What does NOT change:** the observable behavior (inputs → outputs, side effects, error cases)
- **Blast radius:** every caller of every function whose signature is changing. Use the codebase grep, not memory.
- **Migration shape:**
  - **In-place:** structure changes, no parallel implementations. Acceptable for small refactors with localized blast radius.
  - **Strangler:** new implementation in parallel, callers migrated incrementally, old removed last. Required for large refactors.
- **Rollback plan:** if the refactor introduces a regression discovered after merge, what's the revert procedure?

### 2. Behavior-equivalence proof

Before the refactor, capture the behavior:
- **Snapshot tests** of current outputs for a wide input set, OR
- **Property-based tests** that hold for both old and new implementations, OR
- **Replay tests** of recorded production traffic, OR
- **For large refactors**: implement both old and new behind a flag, run both on every call, compare outputs, log mismatches. Remove flag only after zero mismatches over a sufficient sample.

The reviewer agent verifies the proof exists BEFORE allowing implementation cycles.

### 3. Implement (incremental)

The implementer agent works in slices, each one a green-tests checkpoint:
- Each slice: make the change, all tests still pass, commit
- Slices that don't fit this shape mean the strangler pattern was needed

### 4. Validate

The reviewer agent compares behavior pre- and post-refactor using the proof from step 2. The adversary agent specifically probes the boundaries between old and new code (the migration seam is where regressions hide).

### 5. Cleanup

After the new implementation has been live and quiet for the agreed window, the old code is removed in a separate commit. The implementer does NOT delete old code in the same commit as the new code lands — it makes the diff unreviewable.

## Anti-patterns

- "Just a refactor" with no SPEC.md and no behavior-equivalence plan. There is no such thing as "just a refactor" in a non-trivial codebase.
- Renaming a public API as part of a refactor. That's a breaking change disguised as a refactor.
- Mixing refactor commits with feature commits. The diff becomes unreviewable. One commit type per commit.
- Deleting the parallel-implementation flag before the proof window closes.
