# shared/

Reusable infrastructure. Code that prevents bug-classes by construction, not by reminding the implementer to be careful.

## What lives here

- Helpers that multiple parts of `src/` depend on (utility functions, shared types, common protocols)
- Architectural constraints implemented as code (e.g., a `CursorEngine`-style pattern that makes look-ahead bugs impossible, or a typed envelope that makes error-shape inconsistency impossible)
- Test fixtures and harnesses shared across multiple test suites

## What does NOT live here

- Code specific to a single feature or module — that goes in `src/<module>/`
- Throwaway prototype code — that lives in `lab/NN/prototype/`
- Documentation about the architecture — that goes in `.claude/reference/project-architecture.md` (loaded on demand by agents)

## Discipline

When adding to `shared/`, ask: would TWO different parts of `src/` use this? If only one would, it belongs in that module, not here. The 60% layer (per the 60/30/10 framework) earns its place by being reused, not by being centralized.
