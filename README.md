# workspace-blueprint

An agent-native scaffold for software development with [Claude Code](https://github.com/anthropics/claude-code). Designed to serve simultaneously as a **working lab** (numbered iterations accumulate here) and as **portable scaffolding** (copy the structure into other repos).

## What's inside

- **Three-layer routing** (`CLAUDE.md` → `CONTEXT.md` → workspace `CONTEXT.md`) for tight token discipline
- **Four workspaces** mapped to phases of dev work: `spec/` (RFCs, ADRs, briefs), `lab/` (exploratory iterations), `build/` (production pipeline), `ship/` (release artifacts)
- **A four-agent loop** for the build pipeline: planner (one-shot) → implementer ↔ reviewer ↔ adversary (cycle, max 5)
- **`.claude/` infrastructure:**
  - 7 native rules enforcing TDD, conventional commits, review gates, portability, and engineering constraints
  - 14 skills (6 project-specific, 4 office vendored from `anthropics/skills`, 4 routing-vendored from harness plugins under MIT — see `SKILLS.md`)
  - 4 subagent specs
  - 4 bash hooks enforcing rules by construction (TDD, cycle cap, output sign-off, portability)
  - 4 configured MCP servers (`filesystem`, `git`, `fetch`, `github`)
  - Recommended plugins documented in `.claude/MCP-SETUP.md`; installed harness content is snapshotted in `.claude/registry/`

## Inspiration

Structurally inspired by [adam-s/alphadidactic](https://github.com/adam-s/alphadidactic). Adopts the multi-agent loop, numbered iterations, and `.claude/` instruction set patterns; preserves the existing 3-layer routing pattern from the original Acme DevRel template.

The scaffold is intentionally small at the always-loaded layer and pushes detailed guidance into task-specific files so agents load only the context they need.

## Getting started

See [`START-HERE.md`](START-HERE.md).

## Setup after cloning

See [`.claude/MCP-SETUP.md`](.claude/MCP-SETUP.md) for plugin installation and the GitHub MCP token setup.

## Bootstrapping a new repo from this scaffold

See the "If you're using this scaffold to bootstrap a NEW repo" section in [`START-HERE.md`](START-HERE.md).

## Cloning on a new machine

```bash
git clone --recursive git@github.com:Elessar617/workspace-blueprint.git
cd workspace-blueprint
./scripts/bootstrap.sh
```

This:
1. Clones the repo and the ECC submodule under `external/ecc/`.
2. Installs npm dependencies (`gray-matter`).
3. Builds registry JSONs under `.claude/registry/` from ECC + your Claude Code harness.
4. Validates that every name referenced in `ROUTING.md` resolves to a registry entry.

After bootstrap, open the repo in Claude Code, Codex, Cursor, OpenCode, or Gemini CLI — each IDE's preamble points the agent at `ROUTING.md` for auto-narrowing.

## Maintaining the bridge

- **Bump ECC:** `./scripts/update-ecc.sh` (review diff, then commit).
- **After installing/removing a Claude Code plugin:** `./scripts/refresh-harness.sh`.
- **Override hook strictness for a task:** `./scripts/with-profile.sh <profile> <command>` runs the command with `BLUEPRINT_HOOK_PROFILE` set in env. E.g. `./scripts/with-profile.sh minimal claude` for a spike-friendly Claude Code session. Or `export BLUEPRINT_HOOK_PROFILE=minimal` to set it for the rest of the shell. Profiles: `minimal` | `standard` | `strict`.

## Project status

This scaffold is itself the first iteration. Use it, evolve it, file issues for friction.

See [`docs/development-log.md`](docs/development-log.md) for project goal, journey, current state, and what's deferred.
