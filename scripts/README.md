# scripts/

Repo-level utilities. Bash, Python, or whatever fits — these are the things you run, not the things you ship.

## What goes here

- Bootstrapping helpers (e.g., `bootstrap-new-repo.sh` if/when written — see Section 7.2 of the design spec for the manual procedure)
- One-off maintenance scripts
- Repo-level tooling that doesn't belong in `src/` or `shared/`

## What does NOT go here

- Build / lint / test runners — those are package.json/pyproject scripts in the language ecosystem
- Deploy scripts that ship — those go in `ship/deploy/`
- Hook scripts — those go in `.claude/hooks/`

## Conventions

- Scripts are `chmod +x` and start with a shebang (`#!/usr/bin/env bash`, `#!/usr/bin/env python3`, etc.)
- Each script has a header comment explaining purpose, inputs, outputs.
- `set -euo pipefail` for bash scripts.
- Scripts that take arguments document `--help` output.
