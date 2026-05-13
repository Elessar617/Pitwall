# GEMINI.md — Gemini CLI preamble

You are working in the workspace-blueprint repository.

## Per-task routing protocol

Before responding to any prompt:

1. Read `ROUTING.md` at repo root.
2. Identify task type from Step 1 table.
3. Read the matching branch file under `.claude/routing/<branch>.md`.
4. Resolve named items via `.claude/registry/*.json`.
5. Use only the narrowed inventory.

Reuse `.claude/routing/.current.json` on mid-task chatter; re-traverse on transition phrases.

Fallback: if ROUTING.md is missing, use CONTEXT.md + workspace-blueprint native inventory only.
