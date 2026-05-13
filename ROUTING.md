# ROUTING.md — Auto-Selector Decision Tree

> **Agents: BEFORE starting any task, traverse this tree.** Each step narrows scope. Stop at the deepest matching leaf. Item names (e.g., `python-reviewer`) resolve to paths via `.claude/registry/*.json`. Cache the narrowing in `.claude/routing/.current.json`; reuse on mid-task chatter unless a transition signal fires.

## Step 1: Identify task type

| Signal in prompt or context             | Workspace | Branch file                          |
|------------------------------------------|-----------|--------------------------------------|
| "feature", "implement", "add"            | `build/`  | `.claude/routing/build.md`           |
| "fix", "bug", "broken"                   | `build/`  | `.claude/routing/bug.md`             |
| "refactor", "migrate", "rename"          | `build/`  | `.claude/routing/refactor.md`        |
| "investigate", "spike", "explore"        | `lab/`    | `.claude/routing/spike.md`           |
| "RFC", "ADR", "design", "spec", "brief"  | `spec/`   | `.claude/routing/spec-author.md`     |
| "release", "ship", "changelog"           | `ship/`   | `.claude/routing/ship.md`            |

## Task-transition signals (cache invalidation)

Re-traverse this tree (don't reuse cache) when ANY of these apply:

- Prompt contains a transition phrase: "now let's...", "switch to...", "actually...", "next, ...".
- File scope changes substantially: a different language detected, or files now in a different workspace.
- The operator types `/refresh-routing` (future-work feature; ignore for now).

Mid-task chatter ("yes", "explain more", "do that", "ok") preserves the cache.

## Fallback (no branch match)

If no row in Step 1 matches, load only:

- Native agents: `planner`, `implementer`, `reviewer`, `adversary`
- Native skills: `tdd-loop`
- All native rules
- Hook profile: `standard`
- No ECC content

This matches workspace-blueprint's pre-bridge behavior. Fail open.
