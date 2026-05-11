# Bootstrapping a new project from the workspace-blueprint scaffold

The Pitwall repo is a project built **on top of** the workspace-blueprint scaffold — an agent-native template designed to be portable. This document covers how to use the same scaffold for a different project, and how to fill in the project-specific layer when you do.

## Option A — Full clone (lab + scaffolding)

Use this if you want the historical iterations, explorations, and design specs to come along (for reference / learning).

```bash
git clone <pitwall-url> my-new-project
rm -rf my-new-project/.git
rm -rf my-new-project/lab/[1-9]*
rm -rf my-new-project/spec/{rfcs,adrs,briefs}/*
rm -rf my-new-project/build/workflows/[1-9]*
rm -rf my-new-project/docs/explorations/*
rm -rf my-new-project/docs/superpowers/specs/*
rm -rf my-new-project/docs/superpowers/plans/*
rm -rf my-new-project/src/pitwall          # remove Pitwall source code
rm -rf my-new-project/data                  # remove Pitwall runtime data
rm -rf my-new-project/faceoff               # remove the Pitwall reference repo
git init my-new-project
```

## Option B — Scaffolding only (recommended)

Use this when you want a clean slate without any prior iterations.

```bash
rsync -av \
  --exclude='lab/[1-9]*' \
  --exclude='build/workflows/[1-9]*' \
  --exclude='spec/rfcs/*' --exclude='spec/adrs/*' --exclude='spec/briefs/*' \
  --exclude='docs/explorations/*' \
  --exclude='docs/superpowers/specs/*' \
  --exclude='docs/superpowers/plans/*' \
  --exclude='src/pitwall/*' \
  --exclude='data/*' \
  --exclude='faceoff/' \
  --exclude='.git' \
  pitwall/ my-new-project/

cd my-new-project
git init
```

## What to do FIRST after cloning

1. **Run `.claude/MCP-SETUP.md` setup** — install the recommended plugins, set up the GitHub PAT.
2. **Fill in `.claude/reference/`** (these are loaded on demand by agents):
   - `project-architecture.md` — describe what your project is and how it's organized.
   - `tech-stack.md` — languages, frameworks, lint/test/build commands.
   - `glossary.md` — domain terms agents need to know.
   - `frontend-stack.md` — only if you have a frontend (Clief defaults provided, override for non-web stacks like a TUI).
3. **Edit `.claude/.portability-deny.txt`** — add project-specific terms (vendor names, internal endpoints, brand terms) so the portability hook catches drift into rules and skills. Pitwall's entries can serve as a template — remove them and add your own.
4. **Rewrite the top-level identity docs** — `CLAUDE.md`, `README.md`, `START-HERE.md`. Pitwall's versions are templates you can mirror.
5. **Verify `CONTEXT.md`** — its task-routing table is mostly domain-agnostic; usually no changes needed.

## What you SHOULDN'T touch

- `.claude/rules/*` — always-loaded constraints. Must stay domain-agnostic.
- `.claude/skills/*` — on-demand procedures. The non-vendored skills are also domain-agnostic.
- `.claude/agents/*` — planner/implementer/reviewer/adversary specs. Generic by design.
- `.claude/hooks/*` — mechanical enforcement.
- `build/workflows/00-template/`, `lab/00-template/` — iteration templates.

The portability hook (`.claude/hooks/enforce-portability.sh`) blocks any edit to `.claude/rules/` and `.claude/skills/` that contains a term from your `.portability-deny.txt`. This is intentional — it stops domain-specific facts from leaking into the portable layer.

## Why this structure exists

For the long-form rationale — three-layer routing, the four-agent loop, the §4.1 decision sequence from the Clief Notes — see:

- [`how-to-adapt.md`](how-to-adapt.md)
- [`context-md-anatomy.md`](context-md-anatomy.md)
- [`skill-integration-patterns.md`](skill-integration-patterns.md)
- [`common-mistakes.md`](common-mistakes.md)

For an alternate-domain example (DevRel content workflow) showing the same scaffold pointed at different work, see [`legacy-devrel-example/`](legacy-devrel-example/).
