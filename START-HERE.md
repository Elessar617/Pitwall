# Start Here

A 5-minute orientation to this repo. Skip if you've worked here before.

## What this repo is

An agent-native scaffold for software development. Two roles:

1. **A working lab** — numbered iterations (`lab/01-...`, `build/workflows/01-...`) for spikes, features, bug fixes, and refactors. The repo accumulates these over time.
2. **A canonical scaffold** — the directory layout and markdown templates are domain-agnostic and can be copied into other repos as a starter.

## How the structure works

Three-layer routing keeps token usage tight:

1. **`CLAUDE.md`** is always loaded. It's THE MAP — every directory, every convention.
2. **`CONTEXT.md`** is the router. "What's your task → which workspace + what to load."
3. **Each workspace's `CONTEXT.md`** has the per-task load budget.

Then the agent infrastructure:

- **`.claude/rules/`** — 7 always-loaded constraints (TDD mandatory, conventional commits, portability, etc.)
- **`.claude/skills/`** — 14 procedures (6 project-specific, 4 office-doc generation, 4 routing-vendored)
- **`.claude/agents/`** — 4 subagent specs (planner, implementer, reviewer, adversary)
- **`.claude/hooks/`** — 4 bash hooks that enforce rules by construction
- **`.claude/settings.json`** — wires hooks, MCP servers, plugins, permissions

## How work flows

```
Have an open question? → lab/NN-<slug>/  (spike)
Have a decision to record? → spec/adrs/  (ADR)
Have a proposal? → spec/rfcs/  (RFC)
Have a small task? → spec/briefs/  (brief)

When ready to build:
spec/ artifact OR lab/REPORT.md (Pursue)
   → build/workflows/NN-<slug>/  (4 stages, 4 agents)
   → src/  (the code itself)
   → ship/  (release notes, docs, deploy)
```

The four-agent loop in `build/` is documented in `docs/orchestrator-process.md`.

## What to do FIRST after cloning (or forking)

If you're using this repo AS your project (not just as a scaffold):

1. **Run `.claude/MCP-SETUP.md` setup** — install the two recommended plugins, set up the GitHub PAT.
2. **Fill in `.claude/reference/`:**
   - `project-architecture.md` — describe what your project is and how it's organized
   - `tech-stack.md` — languages, frameworks, lint/test/build commands
   - `glossary.md` — domain terms agents need to know
   - `frontend-stack.md` — only if you have a frontend (defaults provided)
3. **Edit `.claude/.portability-deny.txt`** — add project-specific terms (vendor names, internal endpoints) so the portability hook catches drift.
4. **Replace `<!-- REPLACE -->` markers** in `CLAUDE.md`, `CONTEXT.md`, `START-HERE.md`, `README.md`.

If you're using this scaffold to bootstrap a NEW repo:

```bash
# Option A: full clone (lab + scaffolding)
git clone <this-repo> my-new-project
rm -rf my-new-project/.git my-new-project/lab/[1-9]* my-new-project/spec/{rfcs,adrs,briefs}/* my-new-project/build/workflows/[1-9]*
git init my-new-project

# Option B: scaffolding only (recommended)
rsync -av \
  --exclude='lab/[1-9]*' \
  --exclude='build/workflows/[1-9]*' \
  --exclude='spec/rfcs/*' --exclude='spec/adrs/*' --exclude='spec/briefs/*' \
  --exclude='docs/explorations/*' \
  --exclude='docs/superpowers/specs/*' --exclude='docs/superpowers/plans/*' \
  --exclude='.git' \
  workspace-blueprint/ my-new-project/

cd my-new-project
git init
# Then follow the "FIRST after cloning" steps above
```

## Where to learn more

- **Project state, journey, and current capabilities:** `docs/development-log.md`
- **Inventory of skills, agents, commands, and MCPs (by task type):** `SKILLS.md` at repo root
- **Claude Code basics:** `.claude/reference/claude-platform-capabilities.md`
- **Local-only maintainer reference notes:** ignored when present

## Where to find things FAST

- "I want to plan a feature" → `CONTEXT.md` task table → `spec/CONTEXT.md`
- "I want to implement a feature" → `build/CONTEXT.md`
- "I want to investigate something" → `lab/CONTEXT.md`
- "I want to ship a release" → `ship/CONTEXT.md`
- "How does the agent loop work?" → `docs/orchestrator-process.md`
- "How do I configure an MCP?" → `.claude/MCP-SETUP.md`
