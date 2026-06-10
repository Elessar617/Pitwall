# src/

Long-lived production source code. The output of `build/workflows/NN/02-implement/` cycles lands here.

## Layout

The internal layout depends on the consumer project's tech stack. Document it in `.claude/reference/project-architecture.md` so agents know where to find what.

Common patterns (pick one or adapt):

- **Feature-first** (recommended for most new projects): `src/<feature-name>/{api,domain,infra,tests}/`
- **Layer-first**: `src/{api,domain,infra,tests}/<feature-name>/`
- **Single-package**: everything in `src/`, organized by module name

Whatever the layout, follow these rules:

- Tests live next to the code they test (`foo.py` ↔ `test_foo.py`, `Foo.ts` ↔ `Foo.test.ts`).
- No throwaway code — that goes in `lab/`.
- No code generated mid-implementation that isn't covered by tests — TDD is hook-enforced.

## What does NOT live here

- Process notes (those are in `build/workflows/NN/02-implement/notes-N.md`)
- Reusable infrastructure shared across modules (that's `shared/`)
- Build/deploy scripts (those are `scripts/` or `ship/deploy/`)
- Generated files committed by accident — add to `.gitignore`
