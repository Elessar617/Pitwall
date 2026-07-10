# AGENTS.md — Cross-IDE Preamble

> This file is read by Codex, OpenCode, and other harnesses that respect the AGENTS.md convention. Claude Code reads CLAUDE.md (same routing instructions).

## Per-task routing protocol

Before responding to a user prompt, agents in this repo MUST:

<!-- regen:start PROCEDURE_BODY -->
1. Read `ROUTING.md` at repo root.
2. Match the user prompt against Step 1 of ROUTING.md to identify the task type.
3. Read the corresponding branch file under `.claude/routing/<branch>.md`.
4. Resolve named items via `.claude/registry/*.json` (catalogs of available agents, skills, commands, MCPs).
5. Use only the narrowed inventory unless the user requests something explicitly outside it.
<!-- regen:end PROCEDURE_BODY -->

<!-- regen:start RULES_DIGEST -->
## Rules digest (all 9 native rules bind every agent, including non-Claude sub-LLMs)
- **code-quality** — Linter and formatter must pass before any deliverable moves to `build/workflows/*/04-output/`.
- **commit-discipline** — One logical change per commit. Conventional Commits format. Never bypass hooks.
- **evidence-discipline** — Gate evidence is machine-captured, complete, and the last act before a validation freeze. A notes file missing a contracted item is a blocking review finding without adjudication.
- **memory-discipline** — MCP memory and Serena memory surfaces are stable knowledge stores, not session scratchpads. Writes require justification; reads should verify currency before relying on them.
- **nasa-power-of-10** — Apply the relevant subset of Gerard Holzmann's "Power of 10" rules for safety-critical code. Reason about applicability per-task rather than applying universally.
- **portability-discipline** — Files in `.claude/rules/` and `.claude/skills/` must stay domain-agnostic. Project-specific facts live only in `.claude/reference/`. Enforced by `enforce-portability.sh`.
- **review-discipline** — Reviewer + adversary subagents both run before any iteration moves to `build/workflows/*/04-output/`. After 5 failed cycles, the orchestrator halts.
- **testing-discipline** — Test files are written BEFORE the implementation files they cover. Enforced by `pre-commit-tdd.sh`.
- **unix-philosophy** — Make each program do one thing well. Make programs compose via plain-text interfaces. Prefer small, focused tools over monoliths.
<!-- regen:end RULES_DIGEST -->

## Cache

If a small cache exists at `.claude/routing/.current.json`, prefer it for mid-task chatter ("yes", "ok", "explain more"). Invalidate the cache and re-traverse when the prompt contains a transition phrase ("now let's...", "actually...", "switch to...") or when the file scope changes substantially.

## Fallback

If ROUTING.md or `.claude/registry/` is missing, fall back to CONTEXT.md for workspace routing and use only the workspace-blueprint native inventory (4 agents, 10 skills, native rules).

## Repo chassis

The blueprint's 3-layer routing (CLAUDE.md -> CONTEXT.md -> workspace CLAUDE.md) is preserved. ROUTING.md is a parallel decision tree that narrows the inventory for the current task; CONTEXT.md answers "which workspace to work in".

## Model / CLI routing (which brain runs which job)

The steps above narrow *what* (skills, agents, MCPs). A second, orthogonal question is *which LLM family* runs a given pipeline role. If `.claude/reference/model-routing.md` exists, it is the source of truth for that mapping; consult it before delegating cross-family work. Summary of the per-role default on this repo:

| Pipeline role | Runs as | Delegates to | Invocation |
|---|---|---|---|
| Orchestrator / Planner | host session | — | the session you are in |
| Implementer | Codex 5.5/xhigh via `scripts/ask.mjs` | host verifies/integrates | `node scripts/ask.mjs codex "Implement this cycle from SPEC.md. Follow TDD and report files touched."` |
| Reviewer | host session | `codex review` only when Codex was not the writer | review locally; optional non-writer Codex second pass |
| Adversary | host session | Claude/Fable/Opus for Codex-authored diffs; `codex` only for non-Codex diffs | pipe a Codex-authored diff into `node scripts/ask.mjs claude "<prompt>"` |

Rules of thumb (full matrix + caveats in `model-routing.md`): **codex** = default implementation engine (`gpt-5.5`, xhigh); **claude** = taste, prose, orchestration, Claude/Fable/Opus adversarial review of Codex-authored diffs, and final integration judgment. The wrapper `scripts/ask.mjs` normalizes the flag shape for both supported models (`--dry-run` previews the argv without spawning). Every cross-family call is a real token spend and is **fail-open**: if the sub-CLI is unavailable (auth/network/rate-limit, or a host data-boundary policy blocks piping the diff out), record one line (`cross-family probe: unavailable (<reason>)`) and proceed with in-family analysis — never block the cycle on it. The commands are pre-authorized in `.claude/settings.json -> permissions.allow` (`node scripts/ask.mjs:*`, `codex exec:*`, `codex review:*`); a host may still apply its own egress policy on top.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

<!-- universal-standards:start -->
## Coding standards
Before coding or reviewing, read `.standards/standards-core.md` and the applicable section
of `.standards/language-mappings.md`. This repository is pinned by
`.standards/adoption.json`. Waivers live in `.standards/waivers.json`; inline references use
`std-waiver: <WAIVER-ID>`.
<!-- universal-standards:end -->
