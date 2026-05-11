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

- **`.claude/rules/`** — 5 always-loaded constraints (TDD mandatory, conventional commits, portability, etc.)
- **`.claude/skills/`** — 10 procedures (6 project-specific, 4 office-doc generation)
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

```bash
git clone <pitwall-url> pitwall
cd pitwall

# Install the Claude Code plugins this repo expects (user-scope, one-time).
# See .claude/MCP-SETUP.md for the full list and the GitHub PAT step.
claude plugin marketplace add pydantic/skills          # adds ai (Pydantic-AI helper)
claude plugin install ai@pydantic-skills
# karpathy-skills/andrej-karpathy-skills, obra/superpowers, and
# affaan-m/everything-claude-code are also expected — confirm with `claude plugin list`.

# Python project setup (once pyproject.toml lands):
uv sync
uv run pitwall
```

Open Claude Code in this directory and the agent infrastructure boots automatically (rules in `.claude/rules/` are loaded on every turn).

## Where to learn more

- **Claude Code basics:** [`.claude/reference/claude-platform-capabilities.md`](.claude/reference/claude-platform-capabilities.md)
- **How to adapt this template to another project:** [`docs/teaching/how-to-adapt.md`](docs/teaching/how-to-adapt.md)
- **Anatomy of a `CONTEXT.md`:** [`docs/teaching/context-md-anatomy.md`](docs/teaching/context-md-anatomy.md)
- **Skill integration patterns:** [`docs/teaching/skill-integration-patterns.md`](docs/teaching/skill-integration-patterns.md)
- **Common mistakes:** [`docs/teaching/common-mistakes.md`](docs/teaching/common-mistakes.md)
- **Bootstrap the scaffold for a new project:** [`docs/teaching/bootstrap.md`](docs/teaching/bootstrap.md)

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
