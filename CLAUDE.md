# Workspace Blueprint — Map

> **Always loaded.** This file is THE MAP. It shows every workspace, every key directory, every naming convention. It does NOT contain detailed instructions — those live in workspace `CONTEXT.md` files.

## What This Repo Is

An agent-native scaffold for software development work. Two roles:
1. **An active lab** — numbered iterations live here for ongoing software experiments, features, bug investigations, and refactors.
2. **The canonical scaffolding source** — the directory layout and markdown templates are domain-agnostic enough to copy into other repos. See `.claude/MCP-SETUP.md` and `START-HERE.md` for bootstrap.

The instruction layer (`CLAUDE.md`, `CONTEXT.md`, `.claude/`, all workspace `CONTEXT.md` files) is portable. Project-specific facts live only in `.claude/reference/`.

---

## Auto-routing

Before starting any task, agents consult `ROUTING.md` (the markdown decision tree) and the matching branch file under `.claude/routing/`. The tree narrows which agents, skills, commands, MCPs, and hook profile apply. Names resolve via `.claude/registry/*.json`. See spec at `docs/superpowers/specs/2026-05-11-ecc-bridge-and-routing-design.md`.

## Folder Structure

```
workspace-blueprint/
├─ CLAUDE.md             ← you are here (THE MAP, always loaded)
├─ CONTEXT.md            ← Layer 2: top-level ROUTER (read this for task routing)
├─ START-HERE.md         ← onboarding for humans new to this repo
├─ README.md             ← public-facing repo description
│
├─ .claude/              ← cross-cutting agent infrastructure
│  ├─ rules/             ← always-loaded constraints (LEAN, <40KB)
│  ├─ skills/            ← on-demand procedures (10 skills: 6 project + 4 office)
│  ├─ agents/            ← planner, implementer, reviewer, adversary specs
│  ├─ reference/         ← looked up on demand (project + portable references)
│  ├─ hooks/             ← four bash hooks enforcing rules by construction
│  ├─ settings.json      ← wires hooks, plugins, MCP servers
│  ├─ .portability-deny.txt   ← deny list for the portability hook
│  └─ MCP-SETUP.md       ← post-clone setup: plugins + GitHub PAT
│
├─ spec/                 ← WORKSPACE: pre-build artifacts (RFCs, ADRs, briefs)
├─ lab/                  ← WORKSPACE: numbered exploratory iterations (NN-slug/)
├─ build/                ← WORKSPACE: production pipeline (workflows/NN-slug/)
├─ ship/                 ← WORKSPACE: release artifacts (docs, changelog, deploy)
│
├─ shared/               ← reusable infrastructure (the 60% layer)
├─ src/                  ← long-lived production source code
├─ scripts/              ← repo utilities
│
└─ docs/                 ← meta docs about this repo's process
   ├─ explorations/      ← numbered post-mortems from completed iterations
   ├─ iteration-process.md, orchestrator-process.md
   └─ superpowers/{specs,plans}/  ← design specs and implementation plans
```

---

## Workspaces at a Glance

| Workspace | Purpose | Key file |
|---|---|---|
| `spec/` | Pre-build artifacts | `spec/CONTEXT.md` |
| `lab/` | Exploratory numbered iterations | `lab/CONTEXT.md`, `lab/00-template/` |
| `build/` | Production pipeline (4 stages, 4 agents) | `build/CONTEXT.md`, `build/workflows/CONTEXT.md` |
| `ship/` | Release artifacts | `ship/CONTEXT.md` |

For task routing (which workspace + which files to load), read `CONTEXT.md`.

---

## Cross-Workspace Flow

```
        spec/        lab/
          │           │
          └─────┬─────┘
                ▼
              build/    (planner → implementer ↔ reviewer ↔ adversary → output)
                │
                ├──▶ src/      (the code)
                ▼
              ship/    (release notes, docs, deploy)
                │
                ▼
        docs/explorations/  (post-mortems for what was learned)
```

---

## Naming Conventions

| Artifact | Pattern | Example |
|---|---|---|
| Lab iteration | `lab/NN-<slug>/` | `lab/03-graphql-eval/` |
| Build iteration | `build/workflows/NN-<slug>/` | `build/workflows/07-fix-login-loop/` |
| RFC | `spec/rfcs/<slug>.md` | `spec/rfcs/auth-overhaul.md` |
| ADR | `spec/adrs/NNNN-<slug>.md` | `spec/adrs/0003-use-postgres.md` |
| Brief | `spec/briefs/<slug>.md` | `spec/briefs/add-rate-limit.md` |
| Release notes | `ship/changelog/vX.Y.Z.md` | `ship/changelog/v0.2.0.md` |
| Exploration | `docs/explorations/NN-<slug>.md` | `docs/explorations/05-graphql-too-heavy.md` |

`NN` is zero-padded, `<slug>` is `kebab-case`. Numbers are append-only and never reused.

---

## The Four Agents (loop in `build/`)

| Agent | When | Spec |
|---|---|---|
| Planner | One-shot at iteration start; produces `01-spec/SPEC.md` | `.claude/agents/planner-agent.md` |
| Implementer | Each cycle; writes code to `src/`, notes to `02-implement/` | `.claude/agents/implementer-agent.md` |
| Reviewer | Each cycle (parallel with adversary); writes `review-N.md` | `.claude/agents/reviewer-agent.md` |
| Adversary | Each cycle (parallel with reviewer); writes `adversary-N.md` | `.claude/agents/adversary-agent.md` |

Cycle cap: 5 (hook-enforced). Sign-off required for `04-output/` (hook-enforced). Full protocol: `docs/orchestrator-process.md`.

---

## Skills, Plugins, MCPs

- **14 skills** in `.claude/skills/` — 6 project-specific (tdd-loop, bug-investigation, refactor-protocol, spike-protocol, spec-authoring, data-analysis) + 4 office (docx, pptx, xlsx, pdf vendored from `anthropics/skills`) + 4 routing-vendored (systematic-debugging, writing-plans, brainstorming, karpathy-guidelines — MIT-attributed in `.claude/skills/THIRD_PARTY_LICENSES.md`, refreshed via `npm run refresh-vendored`)
- **2 plugins** enabled: `obra/superpowers` and `affaan-m/everything-claude-code`
- **4 MCP servers** configured: `filesystem`, `git`, `fetch` (credential-free), `github` (placeholder env var)

Setup details: `.claude/MCP-SETUP.md`. Catalogs: `.claude/reference/{mcp-servers,external-resources}.md`. **Human-readable inventory of routing-referenced items**: `SKILLS.md` at repo root.

---

## Portability Discipline

This repo is the canonical scaffold for OTHER repos. Files in `.claude/rules/` and `.claude/skills/` (except vendored office skills) MUST stay domain-agnostic. Project-specific facts live ONLY in `.claude/reference/` (which the consumer rewrites). The `enforce-portability.sh` hook + `.claude/.portability-deny.txt` enforce this mechanically.

Bootstrap procedure for using this scaffold in another repo: see `START-HERE.md`.

---

## Token Management

Each workspace is siloed. Don't load everything.

- Working in `build/`? Load `build/CONTEXT.md`, `build/workflows/CONTEXT.md`, the iteration's spec, the relevant agent files, the relevant skills. Skip `spec/`, `lab/`, `ship/` CONTEXT.md.
- Working in `lab/`? Load `lab/CONTEXT.md` + `spike-protocol`. Skip everything else.
- The "What to Load / Skip These" tables in each workspace's CONTEXT.md are the token budget.
