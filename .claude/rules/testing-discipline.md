# Rule: Testing discipline (TDD mandatory)

**Test files are written BEFORE the implementation files they cover. Enforced by `pre-commit-tdd.sh`.**

**Why:** Tests written after the code tend to validate what the code does, not what the spec required. TDD inverts that: the test encodes the spec, the code makes the test pass. The hook prevents the slip into "I'll add tests later."

**How to apply:**
- Each acceptance criterion in `01-spec/SPEC.md` maps to at least one test. The reviewer agent verifies this mapping.
- Test files live next to the code they test (`foo.py` ↔ `test_foo.py`, `Foo.ts` ↔ `Foo.test.ts`) unless the project convention says otherwise. Document the convention in `.claude/reference/tech-stack.md`.
- The TDD loop is documented in `.claude/skills/tdd-loop/`. Follow it: red → green → refactor, one micro-step per commit ideally.
- **No `skip` / `only` / `xit` / `it.todo` in committed tests.** The reviewer flags these as critical.
- **No mocking the layer under test.** Mock external boundaries (network, clock, filesystem when scoped) but not the code path you're trying to verify.
- Coverage is a floor, not a goal. The project's coverage threshold (in `.claude/reference/tech-stack.md`) is the minimum on changed code; no global coverage chasing.
- Performance-sensitive code gets a benchmark, not just a correctness test.
