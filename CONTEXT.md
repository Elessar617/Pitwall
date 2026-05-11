# Workspace Blueprint — Task Router

> **Layer 2: THE ROUTER.** Routes you to the right workspace based on what you're doing. The Clief Notes §4.1 decision sequence is embedded below.

## What This Is

This file does ONE job: route to the right workspace + tell you what to load. Detailed instructions live in workspace `CONTEXT.md` files; the always-loaded map is `CLAUDE.md`.

---

## The Decision Sequence (Clief Notes §4.1)

When starting a task, ask in order:

1. **Need persistent project context?** Yes → CLAUDE.md is auto-loaded; consult `.claude/reference/project-architecture.md` if needed. No → proceed.
2. **Need external data?** Yes → use the configured MCP servers (`filesystem`, `git`, `fetch`, `github`); see `.claude/reference/mcp-servers.md` for more. No → proceed.
3. **Repeatable process?** Yes → use a skill from `.claude/skills/` (10 available). No → prompt directly.
4. **What's the output format?**
   - File (`.docx`, `.pptx`, `.xlsx`, `.pdf`) → `.claude/skills/{docx,pptx,xlsx,pdf}/`
   - Code → goes in `src/` (work flows through `build/`)
   - Learning / decision → goes in `lab/REPORT.md` or `spec/`
   - Release artifact → `ship/`
5. **Need deep reasoning?** Yes → ask Claude to think extended. No → standard.

---

## Task Routing

| Your Task | Go Here | Also Load |
|-----------|---------|-----------|
| **Author an RFC** | `spec/CONTEXT.md` | `.claude/skills/spec-authoring/SKILL.md`, `.claude/reference/project-architecture.md` |
| **Author an ADR** | `spec/CONTEXT.md` | `.claude/skills/spec-authoring/SKILL.md`, existing `spec/adrs/` for next number |
| **Write a brief** | `spec/CONTEXT.md` | `.claude/skills/spec-authoring/SKILL.md` only |
| **Investigate a question (spike)** | `lab/CONTEXT.md` | `lab/00-template/`, `.claude/skills/spike-protocol/SKILL.md` |
| **Run a data-analysis spike** | `lab/CONTEXT.md` | + `.claude/skills/data-analysis/SKILL.md` |
| **Implement a feature** | `build/CONTEXT.md`, `build/workflows/CONTEXT.md` | `.claude/agents/{planner,implementer,reviewer,adversary}-agent.md` (in pipeline order), `.claude/skills/tdd-loop/SKILL.md`, `.claude/rules/` (all 5) |
| **Fix a bug** | `build/CONTEXT.md` | + `.claude/skills/bug-investigation/SKILL.md` |
| **Refactor / migrate** | `build/CONTEXT.md` | + `.claude/skills/refactor-protocol/SKILL.md` |
| **Write user-facing docs** | `ship/CONTEXT.md` | `.claude/reference/tech-stack.md`, the relevant `04-output/OUTPUT.md` |
| **Generate a release artifact** (`.docx`, `.pdf`, etc.) | `ship/CONTEXT.md` | `.claude/skills/{docx,pdf,pptx,xlsx}/SKILL.md` (whichever applies) |
| **Author release notes** | `ship/CONTEXT.md` | `ship/changelog/`, recent `04-output/OUTPUT.md` files |
| **Bootstrap THIS scaffold into another repo** | `START-HERE.md` | `.claude/MCP-SETUP.md` |

---

## Workspace Summary

| Workspace | Purpose | Lifecycle Output |
|-----------|---------|------------------|
| `spec/` | Pre-build artifacts | RFCs / ADRs / briefs that feed `build/` |
| `lab/` | Numbered exploratory iterations | `REPORT.md` (Pursue → spec/ → build/, or Abandon → docs/explorations/) |
| `build/` | Production pipeline (4 stages × 4 agents) | Code in `src/` + `04-output/OUTPUT.md` |
| `ship/` | Release artifacts | Release notes, user-facing docs, deploy configs |

Each workspace's CONTEXT.md has the full per-task load table.

---

## Cross-Workspace Flow

```
spec/  ─┐
        ├─▶ build/  ─▶ src/  ─▶ ship/
lab/  ──┘     │
              ▼
       docs/explorations/  (post-mortems)
```

---

## Where to Find Things

- **The map:** `CLAUDE.md` (always loaded)
- **The agents:** `.claude/agents/`
- **The skills:** `.claude/skills/`
- **The hooks (enforcement):** `.claude/hooks/`
- **The settings (wiring):** `.claude/settings.json`
- **Project-specific reference (consumer fills in):** `.claude/reference/`
- **External resource catalog:** `.claude/reference/{mcp-servers,external-resources}.md`
- **End-to-end process:** `docs/iteration-process.md`, `docs/orchestrator-process.md`
- **How to adapt this scaffold:** `docs/teaching/`
- **The Clief Notes source PDFs:** `docs/teaching/clief-notes/`
