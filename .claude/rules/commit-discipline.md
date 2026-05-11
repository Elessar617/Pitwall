# Rule: Commit discipline

**One logical change per commit. Conventional Commits format. Never bypass hooks.**

**Why:** Each commit is a unit of revertibility. A commit that mixes a feature, a refactor, and a typo fix can't be cleanly reverted if any one of them turns out wrong. Conventional Commits make the changelog generation deterministic.

**How to apply:**
- Format: `<type>(<scope>): <imperative summary under 72 chars>` where `<type>` is one of `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`, `revert`. `<scope>` is optional but useful for monorepos.
- One logical change per commit. If the diff has two distinct verbs ("add X AND fix Y"), it's two commits.
- Body (after a blank line) explains *why* if the why is non-obvious. Reference issue/PR numbers if applicable.
- **Never** `--no-verify`. If a hook fails, the hook is reporting a real problem; fix it. The hook is the rule's enforcement mechanism — bypassing it is bypassing the rule.
- **Never** `--amend` a commit that has been pushed to a shared branch. Amend only locally before pushing.
- **Never** force-push to `main` or any protected branch. Force-pushing to a personal branch you own (e.g., `feature/foo`) before opening a PR is fine.
- **Never** include sensitive files: `.env`, credentials, API keys, large binaries, OS metadata (`.DS_Store`, `Thumbs.db`). Use `.gitignore`.
- Stage explicit paths (`git add path/to/file`) rather than `git add -A` or `git add .` — the latter sweeps in unintended files.
