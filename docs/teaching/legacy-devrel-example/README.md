# Legacy: Acme DevRel Example

This directory preserves the original Acme DevRel template that lived at the repo root before the 2026-05-10 software-development redesign. It is kept here as a teaching reference: a worked example of the same 3-layer routing pattern applied to a *content* workflow (writing → production → community) rather than a *software* workflow (spec → lab → build → ship).

## What's here

- `writing-room/` — content authoring workspace (voice, drafts, finals)
- `production/` — content build pipeline (briefs → specs → builds → output)
- `community/` — content distribution hub (newsletters, social, events)

## Why preserve it

The patterns in these directories are domain-agnostic even though the content is DevRel-specific. They demonstrate:

- **Pipeline pattern** (production) — sequential stages with handoffs
- **Multi-format hub pattern** (community) — single input, many outputs
- **Workspace silos** — agents loading only the docs they need per task

The current `spec/`, `lab/`, `build/`, `ship/` workspaces apply the same patterns to software work. Read these for an alternate-domain illustration.

## Do NOT

- Treat any path here as authoritative for the current repo (use the new top-level workspaces instead)
- Copy these CONTEXT.md files into a new repo without rewriting for software work
