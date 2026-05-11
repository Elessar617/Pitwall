# Spec

## What This Workspace Is

Where ideas become formal proposals before any build kicks off. Three artifact types live here, each with a different lifecycle: RFCs (mutable), ADRs (immutable, numbered, append-only), and briefs (lightweight one-pagers).

---

## What to Load

| Task | Load These | Skip These |
|------|-----------|------------|
| Author an RFC | `../.claude/skills/spec-authoring/SKILL.md`, `../.claude/reference/project-architecture.md` | other workspaces' CONTEXT.md |
| Author an ADR | `../.claude/skills/spec-authoring/SKILL.md`, existing `adrs/` for numbering | reference docs (ADRs are self-contained) |
| Author a brief | `../.claude/skills/spec-authoring/SKILL.md` only | everything else |
| Promote a `lab/NN/REPORT.md` to spec | the REPORT itself, `../.claude/skills/spec-authoring/SKILL.md` | the original PREFLIGHT (irrelevant once outcome decided) |

---

## Folder Structure

```
spec/
├─ CONTEXT.md      ← you are here
├─ rfcs/           ← <slug>.md, mutable until accepted
├─ adrs/           ← NNNN-<slug>.md, immutable once accepted
└─ briefs/         ← <slug>.md, one-page tasks
```

---

## The Process

- **RFC:** Draft → Discussion → Accepted | Rejected | Superseded. Discuss in PR comments before accepting.
- **ADR:** Numbered (zero-padded). Once accepted, never edited except to add a "Superseded by" link. Supersession creates a new ADR with the next number.
- **Brief:** Just write it. No status field. Briefs that grow beyond one page should be promoted to RFCs.

Outputs of this workspace become inputs to `build/workflows/NN-<slug>/01-spec/SPEC.md` (planner agent's first read).

---

## Skills & Tools

| Skill / Tool | When | Purpose |
|-------------|------|---------|
| `/spec-authoring` (`.claude/skills/spec-authoring/`) | Writing any of the three artifact types | Templates + structure for RFC, ADR, brief |
| Web Search MCP | Drafting RFCs | Prior art, existing solutions, current best practices |
| Context7 MCP | Drafting RFCs | Up-to-date library docs when proposing a tech change |

---

## What NOT to Do

- Don't author an RFC and a build at the same time. RFC discussion is a separate cycle from implementation.
- Don't edit accepted ADRs except to add supersession links.
- Don't put implementation details in any spec artifact — that's the planner agent's job (in `build/workflows/NN/01-spec/SPEC.md`).
- Don't load `build/`, `lab/`, or `ship/` while authoring here — different workspaces, different concerns.
