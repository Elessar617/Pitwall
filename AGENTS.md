# AGENTS.md — Cross-IDE Preamble

> This file is read by Codex, OpenCode, and other harnesses that respect the AGENTS.md convention. Claude Code reads CLAUDE.md (same routing instructions).

## Per-task routing protocol

Before responding to a user prompt, agents in this repo MUST:

1. Read `ROUTING.md` (the decision-tree entry file at repo root).
2. Match the user's prompt against Step 1 of ROUTING.md to identify the task type.
3. Read the corresponding branch file under `.claude/routing/<branch>.md`.
4. Resolve any named items via `.claude/registry/*.json` (catalogs of available agents, skills, commands, MCPs).
5. Use only the narrowed inventory unless the user requests something explicitly outside it.

## Cache

If a small cache exists at `.claude/routing/.current.json`, prefer it for mid-task chatter ("yes", "ok", "explain more"). Invalidate the cache and re-traverse when the prompt contains a transition phrase ("now let's...", "actually...", "switch to...") or when the file scope changes substantially.

## Fallback

If ROUTING.md or `.claude/registry/` is missing, fall back to CONTEXT.md for workspace routing and use only the workspace-blueprint native inventory (4 agents, 10 skills, native rules).

## Repo chassis

The blueprint's 3-layer routing (CLAUDE.md -> CONTEXT.md -> workspace CLAUDE.md) is preserved. ROUTING.md is a parallel decision tree that narrows the inventory for the current task; CONTEXT.md answers "which workspace to work in".
