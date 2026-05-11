# How to Adapt This Scaffold

Two adaptation paths: (a) use this repo AS your project, or (b) copy the scaffold into a new repo.

## Path A: Use this repo as your project

You've cloned `workspace-blueprint` and you want to start working in it.

1. **Install plugins + GitHub MCP** per `.claude/MCP-SETUP.md`.
2. **Fill in `.claude/reference/`:**
   - `project-architecture.md` — your codebase structure
   - `tech-stack.md` — your languages, frameworks, lint/test commands
   - `glossary.md` — your domain terms
   - `frontend-stack.md` — only if you have a frontend
3. **Edit `.claude/.portability-deny.txt`** — add your project-specific terms.
4. **Replace `<!-- REPLACE -->` markers** in `CLAUDE.md`, `CONTEXT.md`, `START-HERE.md`, `README.md`.
5. **Start your first iteration** — `lab/01-<slug>/` for an exploratory question, or `build/workflows/01-<slug>/` if you have an accepted brief in `spec/`.

## Path B: Bootstrap a new repo from this scaffold

You want to start a fresh repo using these patterns. Two sub-options:

### Full clone (lab + scaffolding)

```bash
git clone <this-repo> my-new-project
rm -rf my-new-project/.git my-new-project/lab/[1-9]* my-new-project/spec/{rfcs,adrs,briefs}/* my-new-project/build/workflows/[1-9]*
git init my-new-project
```

You inherit example iteration patterns and the docs/explorations history. Useful for learning by example.

### Scaffolding only (recommended for production)

```bash
rsync -av \
  --exclude='lab/[1-9]*' \
  --exclude='build/workflows/[1-9]*' \
  --exclude='spec/rfcs/*' --exclude='spec/adrs/*' --exclude='spec/briefs/*' \
  --exclude='docs/explorations/*' \
  --exclude='docs/superpowers/*' \
  --exclude='.git' \
  workspace-blueprint/ my-new-project/

cd my-new-project
git init
```

You get the empty scaffold with no example iterations. Then follow Path A steps 1–4.

## Common patterns by project type

The four workspaces (`spec`, `lab`, `build`, `ship`) work for most software projects. Some hints:

- **Library / SDK:** `lab/` for API-design spikes; `build/` for the actual library; `ship/changelog/` for semver releases; `ship/docs/` for the README and API docs.
- **Application:** `lab/` for feature-feasibility spikes; `build/` for features and bug fixes; `ship/deploy/` for infra; `ship/docs/` for user docs.
- **Internal tool:** `lab/` is small; `build/` does most of the work; `ship/` is mostly scripts and a one-page README.
- **Research project:** Heavy `lab/` use; `spec/rfcs/` for hypotheses; `build/` for the validated experimental harness; `docs/explorations/` accumulates findings.

## What to evolve over time

The scaffold ships with sensible defaults. Evolve based on what your project actually does:

- **Hooks too strict?** Each one is a single bash file in `.claude/hooks/`. Edit or comment out in `settings.json`.
- **Need more skills?** Add folders to `.claude/skills/`. Browse `obra/superpowers` and the `awesome-claude-skills` lists for ideas.
- **Need more MCP servers?** Add to `.claude/settings.json`; document creds in `MCP-SETUP.md`. Catalogs are in `.claude/reference/mcp-servers.md`.
- **Need stricter rules?** Add to `.claude/rules/` (mind the <40KB budget).

The scaffold is a starting point. Don't preserve patterns that don't fit your work.
