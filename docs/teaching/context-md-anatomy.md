# Anatomy of a CONTEXT.md

Every workspace `CONTEXT.md` answers the same questions. This is the template + why each section exists.

## The template

```markdown
# <Workspace Name>

## What This Workspace Is
[1-2 sentences. What work happens here. Upstream / downstream.]

---

## What to Load
| Task | Load These | Skip These |
|------|-----------|------------|
| [task] | [files] | [files] |

---

## Folder Structure
[Small ASCII tree of THIS workspace only.]

---

## The Process
[How work happens. Sequential steps if it's a pipeline; loose principles if it's exploratory.]

---

## Skills & Tools
| Skill / Tool | When | Purpose |
|-------------|------|---------|
| [skill] | [trigger] | [what it does] |

---

## What NOT to Do
- [anti-pattern 1]
- [anti-pattern 2]
```

## Why each section exists

### "What This Workspace Is"
**Solves:** Agent doesn't know what kind of work to do here.
**Keep to:** 1-2 sentences. If you need a paragraph, you're explaining too much.

### "What to Load"
**Solves:** Agent loads everything or guesses wrong. **The "Skip These" column matters more than the "Load These" column.** Loading the right thing is good; NOT loading the wrong thing is critical (saves tokens, prevents distraction).

### "Folder Structure"
**Solves:** Agent puts files in the wrong place.
**Show:** Only THIS workspace's tree. The full tree is in `CLAUDE.md`.

### "The Process"
**Solves:** Agent doesn't know the workflow.
**Format:** Sequential numbered steps for pipeline workspaces (`build/`); loose principles for exploratory ones (`lab/`).

### "Skills & Tools"
**Solves:** Agent has tools but doesn't know when to use them.
**The "When" column is the key.** "Available" is not a trigger. "Before any draft moves to final" IS a trigger.

### "What NOT to Do"
**Solves:** Agent makes the same mistakes repeatedly.
**These are EARNED, not imagined.** Add anti-patterns when you see them happen, not in anticipation.

## Real examples

### Bad "What to Load" table
```
| Task | Load |
|------|------|
| Any task | All docs |
```
Defeats the purpose. Agent loads everything; tokens wasted.

### Good "What to Load" table
```
| Task | Load These | Skip These |
|------|-----------|------------|
| Implement cycle | SPEC.md, tdd-loop/, .claude/rules/ | other workspaces' CONTEXT.md |
| Review cycle | SPEC.md, the diff, .claude/rules/ | the implementer's notes (read those LAST) |
```
Each task gets exactly what it needs.

### Bad skills table
```
| Skill | Purpose |
|-------|---------|
| /tdd-loop | Test-first |
| /pdf | Make PDFs |
```
No trigger conditions; agent doesn't know WHEN.

### Good skills table
```
| Skill | When | Purpose |
|-------|------|---------|
| /tdd-loop | Implementer agent, every cycle | Mandatory test-first discipline |
| /pdf | Generating user-facing PDF deliverables | From anthropics/skills |
```
Clear triggers. Agent knows exactly when each tool is relevant.

## Size guidelines

| Quality | Line count | Sign |
|---------|-----------|------|
| Too thin | < 25 lines | Agent will lack critical context |
| Right size | 50–110 lines | Enough to route, not enough to overwhelm |
| Bloated | > 120 lines | Probably duplicating .claude/reference/ content |

If your CONTEXT.md grows past 120 lines, ask: "Is this routing instruction, or stable reference knowledge?" Stable knowledge → move to `.claude/reference/`. CONTEXT.md is routing + process, not encyclopedia.
