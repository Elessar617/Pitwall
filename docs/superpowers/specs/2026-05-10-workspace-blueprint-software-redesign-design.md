# Workspace Blueprint — Software Development Redesign

**Status:** Proposed
**Author:** Claude (Opus 4.7) with Gardner Wilson
**Date:** 2026-05-10
**Supersedes:** the existing Acme DevRel template content in this repo

---

## 1. Purpose

Transform `workspace-blueprint` from a domain-specific (Acme DevRel) template into a **general-purpose, agent-native scaffold for software development work**. The redesigned repo serves two roles simultaneously:

1. **An active lab** — numbered iterations live here for ongoing software experiments, features, bug investigations, and refactors.
2. **The canonical scaffolding source** — its directory layout and markdown templates are domain-agnostic enough to copy into other repos.

The redesign borrows structurally from [adam-s/alphadidactic](https://github.com/adam-s/alphadidactic) (multi-agent gated pipeline, numbered iterations, `.claude/{rules,skills,agents,reference,hooks}` instruction set, "instructions evolve through failure") while keeping the existing blueprint's strongest pattern: **3-layer routing** (`CLAUDE.md` → `CONTEXT.md` → workspace `CONTEXT.md`) for token discipline.

It also incorporates two ideas from the Clief Notes Skills Field Manual: the **60/30/10 framework** (60% deterministic code, 30% rules/templates, 10% AI judgment) and the **§4.1 decision sequence** for routing.

## 2. Goals & Non-Goals

### Goals
- Support four work types end-to-end: **feature builds, exploratory spikes, bug investigations, refactors/migrations**.
- Provide a portable scaffolding (the whole repo IS the template) that can be copied into other software projects with minimal editing.
- Wire a multi-agent loop (planner / implementer / reviewer / adversary) into the build pipeline.
- Enforce critical disciplines (TDD, cycle-overrun, output gating, portability) by **construction (hooks)**, not just instruction.
- Preserve token discipline: every loaded file earns its load.

### Non-Goals
- A full bootstrap CLI (deferred to a follow-up iteration).
- Project-specific code or domain logic (those live in consumer repos).
- Replacing the user's global `~/.claude/` skills, hooks, or agents.

## 3. Architecture Overview

### 3.1 Directory Tree

```
workspace-blueprint/
├─ CLAUDE.md                     ← Layer 1: always-loaded MAP
├─ CONTEXT.md                    ← Layer 2: top-level ROUTER (embeds §4.1 decision seq.)
├─ START-HERE.md                 ← onboarding (rewritten for software-dev)
├─ README.md                     ← public-facing repo description
│
├─ .claude/                      ← cross-cutting agent infrastructure
│  ├─ rules/                     ← always-loaded constraints (LEAN — total <40KB)
│  │  ├─ code-quality.md
│  │  ├─ testing-discipline.md
│  │  ├─ commit-discipline.md
│  │  ├─ review-discipline.md
│  │  └─ portability-discipline.md
│  ├─ skills/                    ← on-demand procedures (folder-per-skill)
│  │  ├─ tdd-loop/SKILL.md             ← project-specific
│  │  ├─ bug-investigation/SKILL.md    ← project-specific
│  │  ├─ refactor-protocol/SKILL.md    ← project-specific
│  │  ├─ spike-protocol/SKILL.md       ← project-specific
│  │  ├─ spec-authoring/SKILL.md       ← project-specific
│  │  ├─ data-analysis/SKILL.md        ← project-specific
│  │  ├─ docx/SKILL.md                 ← from anthropics/skills (Word docs)
│  │  ├─ pptx/SKILL.md                 ← from anthropics/skills (PowerPoint)
│  │  ├─ xlsx/SKILL.md                 ← from anthropics/skills (Excel)
│  │  └─ pdf/SKILL.md                  ← from anthropics/skills (PDF)
│  ├─ agents/                    ← four subagent specs
│  │  ├─ planner-agent.md
│  │  ├─ implementer-agent.md
│  │  ├─ reviewer-agent.md
│  │  └─ adversary-agent.md
│  ├─ reference/                 ← looked up on demand (consumer-specific)
│  │  ├─ project-architecture.md       ← <!-- REPLACE -->
│  │  ├─ tech-stack.md                 ← <!-- REPLACE -->
│  │  ├─ glossary.md                   ← <!-- REPLACE -->
│  │  ├─ frontend-stack.md             ← <!-- REPLACE -->
│  │  ├─ iteration-pattern.md          ← portable
│  │  ├─ claude-platform-capabilities.md  ← from Clief Notes §1, §5
│  │  ├─ mcp-servers.md                ← curated catalog from Clief Notes §2.3
│  │  ├─ external-resources.md         ← from Clief Notes §2.1, §2.2, §2.6
│  │  └─ skills-system.md              ← from claude-office-skills-ref/skills-system.md (how skills work)
│  ├─ hooks/                     ← four bash hooks, on by default
│  │  ├─ pre-commit-tdd.sh
│  │  ├─ block-cycle-overrun.sh
│  │  ├─ block-output-without-signoff.sh
│  │  └─ enforce-portability.sh
│  ├─ settings.json              ← wires hooks, enabled plugins, MCP servers
│  ├─ .portability-deny.txt      ← deny list for portability hook
│  └─ MCP-SETUP.md               ← how to install plugins + obtain credentials
│
├─ spec/                         ← WORKSPACE: pre-build artifacts
│  ├─ CONTEXT.md
│  ├─ rfcs/                      ← larger design docs
│  ├─ adrs/                      ← Architecture Decision Records (numbered, immutable)
│  └─ briefs/                    ← lightweight task briefs
│
├─ lab/                          ← WORKSPACE: numbered exploratory iterations
│  ├─ CONTEXT.md
│  ├─ 00-template/               ← copy this to start a new spike
│  │  ├─ PREFLIGHT.md
│  │  ├─ prototype/.gitkeep
│  │  ├─ VERIFY.md
│  │  └─ REPORT.md
│  └─ NN-slug/                   ← e.g., 01-graphql-eval
│
├─ build/                        ← WORKSPACE: production pipeline
│  ├─ CONTEXT.md
│  └─ workflows/
│     ├─ CONTEXT.md              ← pipeline routing
│     ├─ 00-template/            ← copy to start an iteration
│     ├─ 01-spec/                ← planner agent's output
│     ├─ 02-implement/           ← implementer's working notes (NOT code — code goes to src/)
│     ├─ 03-validate/            ← reviewer + adversary write here (review-N.md, adversary-N.md)
│     └─ 04-output/              ← finished, signed-off deliverables
│
├─ ship/                         ← WORKSPACE: release artifacts
│  ├─ CONTEXT.md
│  ├─ docs/                      ← user-facing docs
│  ├─ changelog/                 ← release notes per version
│  └─ deploy/                    ← deploy scripts/configs
│
├─ shared/                       ← reusable infrastructure (the 60% layer)
│  └─ README.md
│
├─ src/                          ← long-lived production source code
│  └─ README.md
│
├─ docs/                         ← meta docs about THIS repo
│  ├─ explorations/              ← numbered post-mortems
│  ├─ iteration-process.md       ← how an iteration runs end-to-end
│  ├─ orchestrator-process.md    ← how the agent loop is orchestrated
│  ├─ teaching/
│  │  ├─ how-to-adapt.md
│  │  ├─ skill-integration-patterns.md
│  │  ├─ context-md-anatomy.md
│  │  ├─ common-mistakes.md
│  │  ├─ legacy-devrel-example/  ← old writing-room/, production/, community/
│  │  └─ clief-notes/
│  │     ├─ skills_field_manual.pdf
│  │     ├─ resource_index.pdf
│  │     └─ inventory.md
│  └─ superpowers/specs/         ← this design and future specs
│
└─ scripts/                      ← repo utilities
   └─ README.md
```

### 3.2 The 60/30/10 Mapping (Clief Notes framework applied)

| Layer | What | Where in repo |
|---|---|---|
| **60% Deterministic code** | Architectural constraints that make bug-classes impossible by construction | `shared/`, `src/`, `.claude/hooks/` |
| **30% Rules / templates** | Always-loaded discipline + on-demand procedures + reusable scaffolds | `.claude/rules/`, `.claude/skills/`, all `CONTEXT.md` files, `lab/00-template/`, `build/workflows/00-template/` |
| **10% AI judgment** | Where agents actually reason | `.claude/agents/` (planner, implementer, reviewer, adversary), `spec/rfcs/` authoring |

This mapping is the architectural defense against agent drift. The more we push down into the 60% layer (hooks, shared code, fixed templates), the less rides on instruction obedience.

## 4. Workspaces

Each workspace owns a phase of dev work. Each has a `CONTEXT.md` that enforces a "What to Load / Skip These" budget.

### 4.1 `spec/` — Pre-build artifacts
- **Purpose:** Where ideas become formal proposals before a build kicks off.
- **Subdirs:** `rfcs/` (mutable until accepted), `adrs/` (numbered, immutable), `briefs/` (lightweight).
- **Inputs:** human-typed, or a `lab/` iteration that's been promoted.
- **Outputs:** an accepted artifact referenced from `build/workflows/NN/01-spec/`.

### 4.2 `lab/` — Numbered exploratory iterations
- **Purpose:** Throwaway experiments that produce *learnings*, not shipped code.
- **Iteration shape** (template at `lab/00-template/`): `PREFLIGHT.md` + `prototype/` + `VERIFY.md` + `REPORT.md`.
- **Naming:** `NN-slug/` with dash separator (e.g., `01-graphql-eval`).
- **Inputs:** an open question.
- **Outputs:** a `REPORT.md` that either feeds `spec/` or sits in `docs/explorations/` as a learning.

### 4.3 `build/` — Production pipeline
- **Purpose:** Four-stage gated pipeline. **All production code work flows through here** — features, bugs, refactors all use the same shape; only `01-spec/` contents differ.
- **Stages:** `01-spec/` (planner output) → `02-implement/` (implementer's process notes — **code lands in `src/`, not here**) → `03-validate/` (reviewer + adversary findings) → `04-output/` (signed-off deliverable).
- **Iteration shape:** `build/workflows/NN-slug/{01..04}/`.
- **Inputs:** an accepted `spec/` artifact or a promoted `lab/` exploration.
- **Outputs:** merged code in `src/` + a `04-output/` artifact + (optionally) a `ship/` entry.

### 4.4 `ship/` — Release artifacts
- **Purpose:** Everything user-facing about a release. Different cadence from `build/` (per release, not per iteration).
- **Subdirs:** `docs/`, `changelog/`, `deploy/`.
- **Inputs:** completed `build/04-output/` artifacts.
- **Outputs:** what gets published.

### 4.5 Cross-workspace flow

```
        spec/        lab/
          │           │
          └─────┬─────┘
                ▼
              build/  (planner → implement ↔ review ↔ adversary → output)
                │
                ├──► src/        (the code itself)
                │
                ▼
              ship/  (release notes, docs, deploy)
                │
                ▼
        docs/explorations/  (post-mortems for what was learned)
```

## 5. The Agent Loop

### 5.1 Roles

| Agent | Spec file | Reads | Writes | Lifecycle |
|---|---|---|---|---|
| **Planner** | `.claude/agents/planner-agent.md` | source artifact, `.claude/reference/` | `build/workflows/NN/01-spec/SPEC.md` | One-shot. Re-planning = re-invoking with new inputs. |
| **Implementer** | `.claude/agents/implementer-agent.md` | `01-spec/SPEC.md`, latest review/adversary findings, `.claude/skills/tdd-loop/` | code in `src/`, notes in `02-implement/notes-N.md` | Cycle role. |
| **Reviewer** | `.claude/agents/reviewer-agent.md` | `01-spec/SPEC.md` (the contract), `src/` diff, `.claude/rules/` | `03-validate/review-N.md` (verdict + findings) | Cycle role. |
| **Adversary** | `.claude/agents/adversary-agent.md` | `01-spec/SPEC.md`, `src/` diff, attack patterns | `03-validate/adversary-N.md` (broken tests, edge cases) | Cycle role. |

All four are **true subagents**, dispatched via the `Agent` tool with isolated context windows. The reviewer never sees the implementer's reasoning; that isolation is what makes their verdict honest.

### 5.2 Lifecycle

**Phase 1 (one-shot):**

```
brief / RFC / ADR ──▶ PLANNER ──▶ build/workflows/NN/01-spec/SPEC.md  ──▶ exit
```

**Phase 2 (loop until acceptance):**

```
                ┌────────────────────────────────────────┐
                │                                        │
                ▼                                        │
        IMPLEMENTER  writes src/, notes 02-implement/    │
                │                                        │
                ▼                                        │
        REVIEWER     spec compliance + quality           │
                │                                        │
       passes   │   fails ──▶ back to implementer ──────▶│
                ▼                                        │
        ADVERSARY    edge cases + attacks                │
                │                                        │
       clean    │   finds issue ──▶ back to implementer ─┘
                ▼
        04-output/  (PR-ready)
```

### 5.3 Termination rules

The loop exits to `04-output/` when, on the same cycle:
1. Reviewer returns `verdict: pass`, AND
2. Adversary returns `findings: none` or `findings: minor (deferred)`.

After **5 failed cycles** (counted by `review-N.md` files), the orchestrator **halts and escalates to the human**. Don't silently keep cycling — likely the spec is wrong, not the implementation. Enforced by `block-cycle-overrun.sh` hook.

### 5.4 Orchestrator

The main Claude Code session is the orchestrator. It reads the spec artifact, dispatches subagents via `Agent`, reads their reports, and runs the cycle. The protocol lives at `docs/orchestrator-process.md` so a fresh session can pick it up.

## 6. `.claude/` Infrastructure

### 6.1 `rules/` — Always-loaded constraints
LEAN. Total budget: **<40KB across all files** (alphadidactic discipline). Each rule prevents a bug class.

| File | Enforces |
|---|---|
| `code-quality.md` | Linter/formatter pass before `04-output`. Type-checking mandatory. No leftover `console.log`/`print`. |
| `testing-discipline.md` | TDD mandatory (test file written before implementation, hook-enforced). No `skip`/`only` in committed tests. Coverage floor on changed code. |
| `commit-discipline.md` | Conventional Commits format. One logical change per commit. Never `--no-verify`. Never `--amend` once pushed. Never force-push to `main`. |
| `review-discipline.md` | Reviewer + adversary both required before `04-output`. After 5 failed cycles, escalate. |
| `portability-discipline.md` | Files in `.claude/rules/` and `.claude/skills/` must stay domain-agnostic. Project-specific facts go in `.claude/reference/`. Hook-enforced. |

### 6.2 `skills/` — On-demand procedures
**Folder-per-skill** convention (matches `anthropics/skills` format). Each folder has `SKILL.md` (required, with YAML frontmatter `name` + `description`) plus optional `REFERENCE.md`, `templates/`, `scripts/`.

**Project-specific (authored here):**

| Skill | Purpose |
|---|---|
| `tdd-loop/` | Red → green → refactor. Invoked by implementer (rule mandates). |
| `bug-investigation/` | Reproduce → diagnose root cause → fix → add regression test. |
| `refactor-protocol/` | Plan + blast-radius + staged migration + behavior-equivalence proof. |
| `spike-protocol/` | PREFLIGHT → prototype → VERIFY → REPORT. Drives `lab/` iterations. |
| `spec-authoring/` | How to write an RFC/ADR/brief that the planner can consume. |
| `data-analysis/` | Trigger phrasing for code execution (Clief §6): "tell Claude what you want to know, not what code to write." |

**Vendored from `anthropics/skills` (already present in this repo as `claude-office-skills-ref/`, moved during commit 2):**

| Skill | Purpose |
|---|---|
| `docx/` | Generate / edit Microsoft Word `.docx` documents. |
| `pptx/` | Generate / edit PowerPoint `.pptx` decks (includes `html2pptx` helper). |
| `xlsx/` | Generate / edit Excel `.xlsx` spreadsheets. |
| `pdf/` | Generate PDF documents (includes `FORMS.md` for fillable PDFs). |

These four are wired into `ship/CONTEXT.md` for release artifacts and into any workspace producing user-facing files.

### 6.3 `agents/` — Subagent specs
Four files matching §5.1.

### 6.4 `reference/` — Looked up on demand
Never auto-loaded. Two flavors of file:

**Portable (ship as-is):**
- `iteration-pattern.md` — the canonical shape of a `lab/` and `build/` iteration
- `claude-platform-capabilities.md` — Skills 1, 5 + decision sequence from Clief Notes
- `mcp-servers.md` — curated MCP server list from Clief Notes §2.3
- `external-resources.md` — official Anthropic + community + learning links from Clief Notes
- `office-skills/` — moved from existing `claude-office-skills-ref/`

**Placeholder (consumer fills in):**
- `project-architecture.md` — `<!-- REPLACE: describe the architecture -->`
- `tech-stack.md` — `<!-- REPLACE: list languages, frameworks, infra -->`
- `glossary.md` — `<!-- REPLACE: domain terms -->`
- `frontend-stack.md` — `<!-- REPLACE: chosen UI/component library, optional -->`

### 6.5 `hooks/` — Automation triggers
On by default in `.claude/settings.json`. Each is a bash script the user can disable via comment in settings.

| Hook | Trigger | Behavior |
|---|---|---|
| `pre-commit-tdd.sh` | `PreToolUse` on Bash with `git commit` | Blocks commit if changed code files have no corresponding test files in the same diff. |
| `block-cycle-overrun.sh` | `PreToolUse` on Edit/Write to `build/workflows/*/03-validate/` | Counts existing `review-N.md`; blocks at N=5 with escalation message. |
| `block-output-without-signoff.sh` | `PreToolUse` on Edit/Write to `build/workflows/*/04-output/` | Blocks unless latest `review-N.md` has `verdict: pass` AND latest `adversary-N.md` has `findings: none\|deferred`. |
| `enforce-portability.sh` | `PostToolUse` on Edit/Write to `.claude/rules/` or `.claude/skills/` | Greps content against `.claude/.portability-deny.txt`; fails if any project-specific terms hit. |

### 6.6 `settings.json` — Wiring
Wires the four hooks, lists enabled plugins (§6.7), declares configured MCP servers (§6.7). Sets default permissions for safe read commands (`git status/diff/log`, `npm test`, `pytest`, `ls`, etc.). Lives in version control. `settings.local.json` (gitignored) holds per-user overrides and any credentials not pulled from env vars.

### 6.7 Plugins & MCP Servers — Installable scope from Clief Resource Index

**Plugins** (Claude Code's plugin system installs these globally; `.claude/settings.json` enables them per-repo):

| Plugin | Source | Why included |
|---|---|---|
| `obra/superpowers` | github.com/obra/superpowers | 20+ battle-tested skills (TDD workflows, debugging, `/brainstorm`, `/write-plan`, `/execute-plan`). Significant overlap with our project skills — we keep our project versions but inherit the rest. By Jesse Vincent. |
| `affaan-m/everything-claude-code` | github.com/affaan-m/everything-claude-code | Hackathon winner. Production-grade Claude Code setup with security scanning, hooks, and config patterns we'll borrow for our own `.claude/hooks/`. |

**MCP servers — credential-free (configured in `settings.json` out of the box):**

| Server | Source | Purpose |
|---|---|---|
| `filesystem` | modelcontextprotocol/servers | Local FS access scoped to repo root. |
| `git` | modelcontextprotocol/servers | Git operations (separate from Bash `git` calls). |
| `fetch` | modelcontextprotocol/servers | Generic HTTP fetcher (no auth). |

**MCP servers — credential-required (placeholder env vars in `settings.json`, setup in `MCP-SETUP.md`):**

| Server | Source | Env vars | Mode |
|---|---|---|---|
| `github` | github/github-mcp-server | `${GITHUB_TOKEN}` | Read-only first; consumer enables write scopes by editing settings. |

**Rationale:** these defaults give the consumer repo a useful out-of-the-box agent (file/git/fetch + GitHub if they add a token + Anthropic office skills + Superpowers skills) without locking them into anything credential-heavy. Stripe, Slack, Notion, etc., are documented in `.claude/reference/mcp-servers.md` as add-ons.

### 6.8 `MCP-SETUP.md` — Consumer setup doc

Lives at `.claude/MCP-SETUP.md`. Covers, in order:
1. **Plugin installation** — `/plugin marketplace add anthropics/claude-plugins-official` then `/plugin install obra/superpowers` and `/plugin install affaan-m/everything-claude-code`.
2. **MCP credential setup** — env-var conventions for each credential-required server (currently just `GITHUB_TOKEN`); how to obtain each token (link to GitHub PAT settings); read-only vs write-scope guidance.
3. **Verifying the install** — `claude` CLI commands to confirm skills, plugins, and MCP servers are visible.
4. **Adding more MCP servers** — pointer to `.claude/reference/mcp-servers.md` catalog (curated lists from Clief Resource Index §2.3).

## 7. Portability Mechanism

### 7.1 The discipline

Every file in `.claude/rules/`, `.claude/skills/`, all workspace `CONTEXT.md` files, and root `CLAUDE.md`/`CONTEXT.md` is written **domain-agnostic** with `<!-- REPLACE: ... -->` placeholders for project-specific facts. Project-specific knowledge lives only in `.claude/reference/` (the one directory the consumer fully rewrites).

The `enforce-portability.sh` hook + `.claude/.portability-deny.txt` deny list mechanically prevent project-specific terms from leaking into the portable layers.

### 7.2 Bootstrap procedure (manual; script later)

```bash
# Option A: full clone (lab + scaffolding)
git clone <this-repo> my-new-project
rm -rf my-new-project/.git my-new-project/lab/[1-9]* my-new-project/spec/{rfcs,adrs}/*
git init my-new-project

# Option B: scaffolding only
rsync -av \
  --exclude='lab/[1-9]*' \
  --exclude='build/workflows/[1-9]*' \
  --exclude='spec/rfcs/*' --exclude='spec/adrs/*' --exclude='spec/briefs/*' \
  --exclude='docs/explorations/*' \
  --exclude='.git' \
  workspace-blueprint/ my-new-project/

# Either way, then:
cd my-new-project
# 1. Fill in .claude/reference/{project-architecture,tech-stack,glossary,frontend-stack}.md
# 2. Add project-specific terms to .claude/.portability-deny.txt
# 3. Replace <!-- REPLACE: ... --> markers in CLAUDE.md, CONTEXT.md, START-HERE.md, README.md
```

A `scripts/bootstrap.sh` codifying Option B is **deferred to a follow-up iteration**.

## 8. Migration Plan

### 8.1 File-by-file

| Current | New | Action |
|---|---|---|
| `CLAUDE.md` | `CLAUDE.md` | Rewrite — software-dev focused |
| `CONTEXT.md` | `CONTEXT.md` | Rewrite — embed Clief §4.1 decision sequence |
| `START-HERE.md` | `START-HERE.md` | Rewrite |
| `exmple.md` | — | Delete (1-line typo'd file) |
| `'New folder'` | — | Delete |
| `'New Text Document.txt'` | — | Delete |
| `writing-room/` | `docs/teaching/legacy-devrel-example/writing-room/` | Move (preserve as teaching reference) |
| `production/` | `docs/teaching/legacy-devrel-example/production/` | Move |
| `community/` | `docs/teaching/legacy-devrel-example/community/` | Move |
| `_examples/` | `docs/teaching/` | Move + rewrite contents for software-dev examples |
| `claude-office-skills-ref/public/{docx,pptx,xlsx,pdf}/` | `.claude/skills/{docx,pptx,xlsx,pdf}/` | Move (these become installed skills) |
| `claude-office-skills-ref/skills-system.md` | `.claude/reference/skills-system.md` | Move (background reference on how skills work) |
| `claude-office-skills-ref/{README.md,CLAUDE.md,package*.json,requirements.txt,html2pptx-local.cjs}` | `docs/teaching/office-skills-source/` | Move (provenance / original packaging context) |
| `clief_notes_*.pdf` | `docs/teaching/clief-notes/` | Move both |
| `docs/clief-notes-inventory.md` | `docs/teaching/clief-notes/inventory.md` | Move (already created in this branch) |

### 8.2 Created fresh
- `.claude/` and all five subdirectories with starter files
- `.claude/settings.json` (hooks + enabled plugins + configured MCP servers)
- `.claude/.portability-deny.txt` (initially empty placeholder list)
- `.claude/MCP-SETUP.md` (plugin install + MCP credential setup guide)
- `spec/`, `lab/`, `build/`, `ship/` workspaces with `CONTEXT.md` each
- `lab/00-template/` and `build/workflows/00-template/`
- `build/workflows/{01-spec,02-implement,03-validate,04-output}/` (empty, with `.gitkeep`)
- `shared/README.md`, `src/README.md`, `scripts/README.md`
- `docs/explorations/`, `docs/iteration-process.md`, `docs/orchestrator-process.md`
- `README.md` (public-facing, distinct from `START-HERE.md`)

### 8.3 Three-commit rollout

1. **Cleanup commit** — delete junk files (`exmple.md`, `'New folder'`, `'New Text Document.txt'`); move legacy DevRel workspaces (`writing-room/`, `production/`, `community/`) to `docs/teaching/legacy-devrel-example/`; move PDFs and inventory to `docs/teaching/clief-notes/`. **Leave `claude-office-skills-ref/` in place** for now; it moves in commit 2 when its destination exists.
2. **Scaffolding commit** — create the new directory tree: all four workspace `CONTEXT.md` files, `.claude/{rules,skills,agents,reference,hooks,settings.json,.portability-deny.txt,MCP-SETUP.md}`, workspace skeletons, templates, hooks. Decompose `claude-office-skills-ref/`: move `public/{docx,pptx,xlsx,pdf}/` into `.claude/skills/`, move `skills-system.md` into `.claude/reference/`, move provenance files (`README.md`, `CLAUDE.md`, `package*.json`) into `docs/teaching/office-skills-source/`, then remove the now-empty `claude-office-skills-ref/` directory. Populate `.claude/reference/{mcp-servers.md,external-resources.md}` from the Clief inventory. Wire the two plugins and four MCP servers in `.claude/settings.json`.
3. **Migration commit** — final `CLAUDE.md`, `CONTEXT.md`, `START-HERE.md`, `README.md` rewrites; rewrite the four `_examples/` files into `docs/teaching/` with software-dev examples; verify the `enforce-portability.sh` hook passes against the new `.claude/` content.

## 9. Risks & Open Items

### Known risks
- **Hook over-enforcement:** The four hooks could become annoying if they fire on legitimate work (e.g., the TDD hook on a docs-only commit). Mitigation: each hook checks file extensions / paths to scope itself; documented escape hatch is to comment the hook out in `settings.json`, not bypass with `--no-verify`.
- **Subagent token cost:** Running planner + implementer + reviewer + adversary on every iteration is more expensive than single-agent. Mitigation: documented in `docs/orchestrator-process.md` that orchestrator can collapse to single-agent for trivial work; loop is for non-trivial production iterations.
- **Portability false positives:** The deny-list grep could trigger on innocuous use of a project term. Mitigation: deny list is project-managed; users edit it as they go.

### Deferred (future iterations)
- `scripts/bootstrap.sh` — one-command consumer-repo setup
- Evaluating `obra/superpowers` plugin for overlap with our skills
- Evaluating `affaan-m/everything-claude-code` for hook patterns
- Configuring `github/github-mcp-server` as a default MCP

## 10. Acceptance Criteria

This redesign is complete when:
- [ ] Three commits land cleanly on `main`.
- [ ] All five `.claude/rules/` files exist and total <40KB.
- [ ] All four `.claude/agents/` specs exist with input/output/termination contracts.
- [ ] All ten `.claude/skills/` folders have a `SKILL.md` with YAML frontmatter (six project skills + four office skills from `anthropics/skills`).
- [ ] All four hooks exist and are wired in `.claude/settings.json`.
- [ ] `.claude/settings.json` enables both plugins (`obra/superpowers`, `affaan-m/everything-claude-code`) and configures the four MCP servers (filesystem, git, fetch credential-free; github with `${GITHUB_TOKEN}` placeholder).
- [ ] `.claude/MCP-SETUP.md` documents plugin install + MCP credential setup steps.
- [ ] `.claude/reference/mcp-servers.md` catalogs the curated MCP servers from Clief Resource Index §2.3 with one-line descriptions.
- [ ] `.claude/reference/external-resources.md` catalogs Clief Resource Index §2.1, §2.2, §2.6 entries.
- [ ] All four workspaces (`spec/`, `lab/`, `build/`, `ship/`) have a `CONTEXT.md` with the standard sections (What this is / What to load / Folder structure / Process / Skills & tools / What NOT to do).
- [ ] `lab/00-template/` and `build/workflows/00-template/` exist.
- [ ] Legacy DevRel content preserved at `docs/teaching/legacy-devrel-example/`.
- [ ] Clief Notes PDFs + inventory moved to `docs/teaching/clief-notes/`.
- [ ] Original `claude-office-skills-ref/` directory is fully decomposed and removed.
- [ ] `enforce-portability.sh` passes against the new `.claude/rules/` and `.claude/skills/` files.

---

*End of design.*
