# Ship

## What This Workspace Is

Release artifacts. Everything user-facing about a release lives here: docs that ship with the code, changelog/release notes, and deploy scripts/configs. Different cadence from `build/` — releases are per-version, not per-iteration.

---

## What to Load

| Task | Load These | Skip These |
|------|-----------|------------|
| Write user-facing docs | `docs/` subfolder, `../.claude/reference/tech-stack.md`, the relevant `build/workflows/NN/04-output/OUTPUT.md` | implementer notes, reviewer findings (those are internal) |
| Generate a `.docx`/`.pdf`/`.pptx` deliverable | the relevant `.claude/skills/{docx,pdf,pptx}/SKILL.md` | unrelated skills |
| Author release notes | `changelog/` subfolder, recent `04-output/OUTPUT.md` files since last release | iteration internals |
| Update deploy config | `deploy/` subfolder, `../.claude/reference/project-architecture.md` | docs/, changelog/ |

---

## Folder Structure

```
ship/
├─ CONTEXT.md
├─ docs/        ← user-facing docs (READMEs, tutorials, API docs)
├─ changelog/   ← release notes (vX.Y.Z.md)
└─ deploy/      ← deploy scripts, infra configs, environment specs
```

---

## The Process

- **Release notes** are append-only per version. Each version (`v0.2.0.md`, `v0.3.0.md`) summarizes what changed since the previous release, sourced from `04-output/OUTPUT.md` files.
- **User-facing docs** are kept in sync with the code as part of the iteration that changes the code (mention in SPEC.md). The reviewer flags doc drift as a finding.
- **Deploy configs** are versioned with the code; changes to deploy/ go through the same `build/` pipeline (with the iteration's spec describing the deploy change).
- **File deliverables** (PDFs, Word docs, slide decks) use the office skills in `.claude/skills/{docx,pdf,pptx,xlsx}/`.

---

## Skills & Tools

| Skill / Tool | When | Purpose |
|-------------|------|---------|
| `/docx` | Generating Word deliverables | From `anthropics/skills` |
| `/pptx` | Generating PowerPoint deliverables | From `anthropics/skills` (incl. `html2pptx` helper) |
| `/xlsx` | Generating Excel deliverables | From `anthropics/skills` |
| `/pdf` | Generating PDF deliverables (incl. fillable forms) | From `anthropics/skills` |
| `github` MCP | Tagging releases, opening release PRs | Direct GitHub integration |

---

## What NOT to Do

- Don't author user-facing docs that contradict the implementation. Reviewer flags doc-code drift.
- Don't release without an entry in `changelog/`. The release notes ARE the public face of the work.
- Don't put internal-only docs (architecture, contributor notes) here. Those go in `docs/` (top-level meta) or `.claude/reference/`.
- Don't load `build/` work-in-progress here. Use the `04-output/` artifacts as the source of truth for what shipped.
