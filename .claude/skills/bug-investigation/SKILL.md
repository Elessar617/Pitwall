---
name: bug-investigation
description: Use when starting work on a reported bug or unexpected behavior. Enforces reproduce-before-fix and root-cause-before-patch. Drives a build/ iteration whose 01-spec/ is the diagnosis, not a feature plan.
---

# Bug Investigation

Bug fix work uses the same `build/` pipeline as feature work, but the SPEC.md in `01-spec/` is shaped differently — it documents diagnosis instead of design.

## The phases

### 1. Reproduce
Write a failing test that reproduces the reported behavior. **Until you can write this test, you do not understand the bug.** If you can't reproduce it locally, the spec phase isn't done; either the report is missing information (ask) or the bug is environmental (different SPEC).

The reproduction test is the single most valuable artifact in a bug investigation. It becomes the regression test once the bug is fixed.

### 2. Diagnose
Find the root cause, not the trigger. The trigger is what the user did; the root cause is the code-level reason that input produces wrong output. State both.

Common confusions:
- "Validation didn't catch the bad input" — that's a missing-validation bug AND a separate root cause for whatever the bad input then broke.
- "The function returned null" — what made it return null is the root cause, not the null itself.

Document the diagnosis in the iteration's `01-spec/SPEC.md`:
- **Trigger:** how to reproduce (link to the test)
- **Symptom:** what the user / system observed
- **Root cause:** the code-level reason (file:line)
- **Why prior tests didn't catch it:** what's missing from coverage

### 3. Fix
The implementer agent writes the minimum change that makes the reproduction test pass. Then the reviewer agent verifies the fix matches the diagnosis and adversary explores adjacent failure modes.

### 4. Regression test
The reproduction test from Phase 1 IS the regression test. It must remain in the test suite forever. The reviewer flags any attempt to delete it.

## Anti-patterns

- "Fixing" a bug by patching the symptom (catching the exception, defaulting the null) without understanding why the bad state arose.
- Closing a bug as "cannot reproduce" without asking the reporter for the missing context. Cannot-reproduce is a spec failure, not a fix.
- Deleting the reproduction test after the fix lands. The test prevents recurrence.
- Bundling the bug fix with unrelated cleanup. Fix in one commit; cleanup in another.
