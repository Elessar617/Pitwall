# Rule: Code quality

**Linter and formatter must pass before any deliverable moves to `build/workflows/*/04-output/`.**

**Why:** A linter catch in `04-output` review is a wasted cycle. The reviewer agent's verdict is meaningless if the diff has style issues drowning out real findings.

**How to apply:**
- Implementer runs the project's lint + format commands as the last step before declaring `02-implement/` work done. Document the project's commands in `.claude/reference/tech-stack.md`.
- Type checking (where the language supports it) is mandatory. Untyped code in a typed codebase is a regression.
- No leftover `console.log`, `print`, `dbg!`, `byebug`, or equivalent debug statements in committed code. The reviewer agent flags any it finds as a critical issue.
- Imports must be sorted/grouped per the project's convention (or the formatter's default).
- Dead code (unused imports, unreachable branches, commented-out blocks) gets removed, not preserved "in case we need it." Git history is the safety net.
