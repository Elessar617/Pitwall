---
name: tdd-loop
description: Use when implementing any feature, bug fix, or refactor in the build/ pipeline. Enforces test-first discipline as a tight red→green→refactor cycle. Mandatory for the implementer agent (per testing-discipline rule).
---

# TDD Loop

The unit of TDD work is a single behavior, not a single function. One behavior = one cycle = ideally one commit.

## The cycle

1. **Red.** Write the smallest test that captures the next unimplemented behavior. Name the test for the behavior, not the implementation: `test_user_can_log_in_with_valid_credentials`, not `test_login_function`.
2. **Run the test. Confirm it fails for the right reason.** A test that fails because of a syntax error elsewhere is not a red. The failure must be the *assertion* failing or the *function being missing*.
3. **Green.** Write the minimum code that makes the test pass. Resist the urge to anticipate the next test. The next test will tell you what's needed.
4. **Run all tests. Confirm everything passes.**
5. **Refactor.** With the safety net of passing tests, clean up: extract names, remove duplication, tighten signatures. Do NOT change behavior. Re-run tests after each substantive edit.
6. **Commit.** One commit captures the red+green+refactor for one behavior.

## Per-stage discipline

- **Red:** if the test passes immediately, the test is wrong (testing the wrong thing or already-existing behavior). Stop and fix the test.
- **Green:** if making the test pass requires touching files outside the obvious scope, the spec or design is wrong. Stop and revisit.
- **Refactor:** if a refactor breaks a different test, the refactor changed behavior. Revert the refactor; either keep the duplication or update the test (separately).

## When to break the cycle

- **Spike work** (lab/): TDD often unhelpful for throwaway prototypes. Use the spike-protocol skill instead.
- **Pure data migrations / config changes**: write the validation step (an assertion that the migration produced the expected state), not a unit test.
- **External-system integration**: write a contract test against a fake first; integration test against the real system later, separately.

## Anti-patterns

- Writing five tests then five implementations. The cycle is one-and-one.
- Mocking the layer under test. Mock external boundaries; real-implement what you're verifying.
- "Add tests later" — no. The pre-commit-tdd.sh hook enforces test files in the same diff as code files.
- Commenting out a failing test to "fix later." Delete it or fix it; do not leave it as silent debt.
