# Start Here

A 5-minute orientation for new contributors to **Pitwall**.

## What this repo is

**Pitwall** is a terminal-UI companion for Formula 1: live timing + real-time track-position map during sessions, a season tracker for schedule / standings / results, and a strategy mini-game played alongside the actual race. See [`README.md`](README.md) for the public-facing overview.

It's built on the **workspace-blueprint scaffold**, an agent-native template that organizes development into four workspaces (`spec/`, `lab/`, `build/`, `ship/`) and a four-agent build loop (planner → implementer ↔ reviewer ↔ adversary).

If you want to use the same scaffold for a different project, see [`docs/teaching/bootstrap.md`](docs/teaching/bootstrap.md).

## How the structure works

Three-layer routing keeps token usage tight:

1. **[`CLAUDE.md`](CLAUDE.md)** is always loaded. It's THE MAP — every directory, every convention.
2. **[`CONTEXT.md`](CONTEXT.md)** is the router. "What's your task → which workspace + what to load."
3. **Each workspace's `CONTEXT.md`** has the per-task load budget.

Then the agent infrastructure:

- **`.claude/rules/`** — 7 always-loaded constraints (TDD mandatory, conventional commits, portability, etc.)
- **`.claude/skills/`** — 14 procedures (6 project-specific, 4 office-doc generation, 4 routing-vendored)
- **`.claude/agents/`** — 4 subagent specs (planner, implementer, reviewer, adversary)
- **`.claude/hooks/`** — 4 bash hooks that enforce rules by construction
- **`.claude/settings.json`** — wires hooks, MCP servers, plugins, permissions
- **`.claude/reference/`** — F1 + Pitwall facts agents look up on demand

## How work flows

```
Have an open question? → lab/NN-<slug>/  (spike)
Have a decision to record? → spec/adrs/  (ADR)
Have a proposal? → spec/rfcs/  (RFC)
Have a small task? → spec/briefs/  (brief)

When ready to build:
spec/ artifact OR lab/REPORT.md (Pursue)
   → build/workflows/NN-<slug>/  (4 stages, 4 agents)
   → src/pitwall/  (the code itself)
   → ship/  (release notes, docs, deploy)
```

The four-agent loop in `build/` is documented in [`docs/orchestrator-process.md`](docs/orchestrator-process.md).

## What to do FIRST after cloning

If you're contributing to Pitwall:

```bash
git clone https://github.com/Elessar617/Pitwall.git pitwall
cd pitwall
./scripts/bootstrap.sh   # clones ECC submodule, builds .claude/registry/

# Install the Claude Code plugins this repo expects (user-scope, one-time).
# See .claude/MCP-SETUP.md for the full list and the GitHub PAT step.
# obra/superpowers and affaan-m/everything-claude-code are expected —
# confirm with `claude plugin list`.

# Python project setup (once pyproject.toml lands):
uv sync
uv run pitwall

# Seed local data caches (FastF1 + Jolpica) on first run; subsequent
# runs read from data/*.db SQLite caches under data/.
```

Open Claude Code in this directory and the agent infrastructure boots automatically (rules in `.claude/rules/` are loaded on every turn). Codex, Cursor, OpenCode, and Gemini CLI also work — each IDE's preamble points the agent at `ROUTING.md` for auto-narrowing.

If you're using Pitwall's bootstrap process for a NEW project (not contributing to Pitwall), see [`docs/teaching/bootstrap.md`](docs/teaching/bootstrap.md) for the recipe. The short version:

```bash
# Option A: full clone (lab + scaffolding)
git clone https://github.com/Elessar617/Pitwall.git my-new-project
rm -rf my-new-project/.git my-new-project/lab/[1-9]* my-new-project/spec/{rfcs,adrs,briefs}/* my-new-project/build/workflows/[1-9]*
git init my-new-project

# Option B: scaffolding only (recommended)
rsync -av \
  --exclude='lab/[1-9]*' \
  --exclude='build/workflows/[1-9]*' \
  --exclude='spec/rfcs/*' --exclude='spec/adrs/*' --exclude='spec/briefs/*' \
  --exclude='docs/explorations/*' \
  --exclude='docs/superpowers/specs/*' --exclude='docs/superpowers/plans/*' \
  --exclude='data/' --exclude='faceoff/' \
  --exclude='.git' \
  pitwall/ my-new-project/

cd my-new-project
git init
# Then: fill in .claude/reference/, edit .claude/.portability-deny.txt,
# replace Pitwall-specific framing in CLAUDE.md / CONTEXT.md / README.md / START-HERE.md
```

## Where to learn more

- **Project state, journey, and current capabilities:** [`docs/development-log.md`](docs/development-log.md)
- **Inventory of skills, agents, commands, and MCPs (by task type):** [`SKILLS.md`](SKILLS.md) at repo root
- **Claude Code basics:** [`.claude/reference/claude-platform-capabilities.md`](.claude/reference/claude-platform-capabilities.md)
- **How to adapt this template to another project:** [`docs/teaching/how-to-adapt.md`](docs/teaching/how-to-adapt.md)
- **Anatomy of a `CONTEXT.md`:** [`docs/teaching/context-md-anatomy.md`](docs/teaching/context-md-anatomy.md)
- **Skill integration patterns:** [`docs/teaching/skill-integration-patterns.md`](docs/teaching/skill-integration-patterns.md)
- **Common mistakes:** [`docs/teaching/common-mistakes.md`](docs/teaching/common-mistakes.md)
- **Bootstrap the scaffold for a new project:** [`docs/teaching/bootstrap.md`](docs/teaching/bootstrap.md)
- **Local-only maintainer reference notes:** ignored when present

## Where to find things FAST

- "I want to plan a feature" → `CONTEXT.md` task table → `spec/CONTEXT.md`
- "I want to implement a feature" → `build/CONTEXT.md`
- "I want to investigate something (spike)" → `lab/CONTEXT.md`
- "I want to ship a release" → `ship/CONTEXT.md`
- "How does the agent loop work?" → `docs/orchestrator-process.md`
- "How do I configure an MCP?" → `.claude/MCP-SETUP.md`
- "How does Pitwall actually work?" → `.claude/reference/project-architecture.md`
- "What's the tech stack?" → `.claude/reference/tech-stack.md`
- "F1 terminology I don't know?" → `.claude/reference/glossary.md`
