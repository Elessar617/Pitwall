---
name: spec-authoring
description: Use when authoring an RFC, ADR, or brief in spec/. Defines the shape each artifact must take so the planner agent can consume it cleanly into 01-spec/SPEC.md.
---

# Spec Authoring

Three flavors of artifact live in `spec/`. They have different purposes and different lifecycles.

## RFC (`spec/rfcs/<slug>.md`)

A proposal for a significant change that warrants discussion before commitment. Mutable until accepted.

**Structure:**
```
# RFC: <title>

**Status:** Draft | Discussion | Accepted | Rejected | Superseded by <link>
**Author:** <name>
**Date:** YYYY-MM-DD

## Summary
One paragraph: what this proposes, who it affects.

## Motivation
What problem this solves. Why now.

## Proposal
The concrete change. Concrete enough that an engineer could start work from this section alone.

## Alternatives considered
What you ruled out and why. (At least two alternatives, including "do nothing.")

## Open questions
What's deferred or unresolved.

## References
Prior art, related RFCs, supporting docs.
```

Use Web Search and Context7 MCP for prior art. An RFC without alternatives considered is a draft, not a proposal.

## ADR (`spec/adrs/NNNN-<slug>.md`)

An Architecture Decision Record. **Numbered (zero-padded), immutable once accepted, append-only.** When superseded, the new ADR references the old; the old ADR is updated only to add a "Superseded by" link.

**Structure:**
```
# NNNN. <decision title in past tense>

**Status:** Accepted | Superseded by NNNN
**Date:** YYYY-MM-DD

## Context
The forces at play. The problem being decided. (Not a story; a list of constraints.)

## Decision
The choice made. Stated as a single sentence if possible, then a paragraph elaborating.

## Consequences
What this enables, what this constrains, what it costs. Both positive and negative.
```

ADRs answer "why is the system this way?" months later when someone asks. Keep them short.

## Brief (`spec/briefs/<slug>.md`)

The lightest artifact. A one-page task description that's enough input for the planner agent to produce a SPEC.md. Use briefs for work that doesn't warrant an RFC or ADR.

**Structure:**
```
# Brief: <title>

**One-liner:** <single sentence describing the work>

## Context
A paragraph or two: where this came from, what it depends on.

## What "done" looks like
Bullet list of observable outcomes.

## Out of scope
What this brief explicitly does NOT cover.

## References
Links to related RFCs/ADRs/issues if any.
```

A brief should fit on one screen. If it doesn't, it's an RFC.

## How the planner consumes these

The planner agent's input is one of: an RFC (Accepted), an ADR (relevant section), a brief, or a `lab/NN/REPORT.md` with outcome "Pursue." It produces `build/workflows/NN-<slug>/01-spec/SPEC.md`. The clearer the source artifact, the cleaner the SPEC.

The planner does NOT modify the source artifact. If the planner finds the source insufficient, it asks the human (or returns a minimal SPEC stating what's missing).
