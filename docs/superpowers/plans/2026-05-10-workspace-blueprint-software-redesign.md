# Workspace Blueprint Software Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform `workspace-blueprint` from the Acme DevRel template into a general-purpose, agent-native scaffold for software development with `spec/lab/build/ship` workspaces, a four-agent loop (planner / implementer / reviewer / adversary), `.claude/{rules,skills,agents,reference,hooks}` infrastructure, vendored Anthropic office skills, two enabled plugins, and four configured MCP servers.

**Architecture:** Three-layer routing (`CLAUDE.md` map → `CONTEXT.md` router → workspace `CONTEXT.md`) wraps an alphadidactic-style `.claude/` instruction set. Numbered iterations live in `lab/` (exploratory) and `build/workflows/` (production pipeline). Code goes to `src/` regardless of which workspace produced it. Hooks enforce TDD, cycle limits, output gating, and portability by construction.

**Tech Stack:** Markdown for all documentation (CommonMark). Bash for hooks. JSON for `.claude/settings.json`. The repo itself contains no executable application code yet; `src/` and `shared/` start empty with READMEs explaining their purpose.

**Source spec:** `docs/superpowers/specs/2026-05-10-workspace-blueprint-software-redesign-design.md`
**Source inventory:** `docs/clief-notes-inventory.md`

**Working directory for all paths in this plan:** `/Users/gardnerwilson/workspace/workspace-blueprint/` (referenced as `$REPO` below). All `git` commands run from any directory inside the repo's git tree.

**Critical git note:** The git repository root is at `/Users/gardnerwilson/workspace/`, NOT at `$REPO`. The repo contains many unrelated dirty files (deleted static_site files, untracked subprojects). **Always stage explicit paths under `workspace-blueprint/`. Never use `git add -A`, `git add .`, or `git add workspace-blueprint/` (recursive).** Stage individual files only.

---

## Pre-flight: Verify Baseline

### Task 0: Verify clean baseline before starting

**Files:** none modified.

- [ ] **Step 1: Confirm the design spec and inventory are committed**

Run:
```bash
git log --oneline -3
```
Expected output should include the two recent commits:
```
923cb3a Expand redesign spec scope to install Clief Resource Index items
61af5c3 Add design spec and Clief Notes inventory for workspace-blueprint redesign
```

If those commits are not present, STOP and ask the user — the spec/inventory may not have been committed yet.

- [ ] **Step 2: Confirm the workspace-blueprint dir contents**

Run:
```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/
```
Expected entries (some are unrelated dirty state, leave them alone):
- `CLAUDE.md`, `CONTEXT.md`, `START-HERE.md`, `exmple.md`
- `_examples/`, `claude-office-skills-ref/`, `community/`, `docs/`, `production/`, `writing-room/`
- `clief_notes_skills_field_manual_v1.pdf`, `clief_notes_resource_index_v1.pdf`
- `'New folder'/`, `'New Text Document.txt'`

- [ ] **Step 3: Confirm we know the git repo root**

Run:
```bash
git rev-parse --show-toplevel
```
Expected: `/Users/gardnerwilson/workspace`

This confirms staging must use paths relative to that root (e.g., `workspace-blueprint/CLAUDE.md`, not `CLAUDE.md`).

---

## COMMIT 1 — Cleanup

The cleanup commit removes junk and moves legacy DevRel + Clief artifacts into their teaching homes. Leaves `claude-office-skills-ref/` in place — it gets decomposed in Commit 2 when its destinations exist.

### Task 1: Delete junk files

**Files:**
- Delete: `$REPO/exmple.md`
- Delete: `$REPO/'New folder'/` (empty directory)
- Delete: `$REPO/'New Text Document.txt'`

- [ ] **Step 1: Verify the files exist and are safe to delete**

Run:
```bash
ls -la /Users/gardnerwilson/workspace/workspace-blueprint/exmple.md /Users/gardnerwilson/workspace/workspace-blueprint/'New Text Document.txt' && ls -la /Users/gardnerwilson/workspace/workspace-blueprint/'New folder'/
```
Expected: `exmple.md` is 0–1 lines (empty), `'New Text Document.txt'` exists, `'New folder'` is empty or near-empty. If any has unexpected content, STOP and show the user before deleting.

- [ ] **Step 2: Delete the three items**

Run:
```bash
rm /Users/gardnerwilson/workspace/workspace-blueprint/exmple.md
rm /Users/gardnerwilson/workspace/workspace-blueprint/'New Text Document.txt'
rmdir /Users/gardnerwilson/workspace/workspace-blueprint/'New folder'
```

- [ ] **Step 3: Verify they are gone**

Run:
```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/exmple.md 2>&1 | head -1
```
Expected: `ls: /Users/.../exmple.md: No such file or directory`.

### Task 2: Move legacy DevRel workspaces to docs/teaching/

**Files:**
- Create: `$REPO/docs/teaching/legacy-devrel-example/` (directory)
- Move: `$REPO/writing-room/` → `$REPO/docs/teaching/legacy-devrel-example/writing-room/`
- Move: `$REPO/production/` → `$REPO/docs/teaching/legacy-devrel-example/production/`
- Move: `$REPO/community/` → `$REPO/docs/teaching/legacy-devrel-example/community/`

- [ ] **Step 1: Create the destination directory**

Run:
```bash
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/legacy-devrel-example
```

- [ ] **Step 2: Move each legacy workspace**

Run:
```bash
mv /Users/gardnerwilson/workspace/workspace-blueprint/writing-room /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/legacy-devrel-example/
mv /Users/gardnerwilson/workspace/workspace-blueprint/production /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/legacy-devrel-example/
mv /Users/gardnerwilson/workspace/workspace-blueprint/community /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/legacy-devrel-example/
```

- [ ] **Step 3: Verify the move**

Run:
```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/legacy-devrel-example/
```
Expected: `community  production  writing-room`

Run:
```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/ | grep -E '^(writing-room|production|community)$' || echo "GONE"
```
Expected: `GONE`

- [ ] **Step 4: Write the README explaining what this directory is**

Create `$REPO/docs/teaching/legacy-devrel-example/README.md`:

```markdown
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
```

### Task 3: Move Clief Notes PDFs and inventory to docs/teaching/clief-notes/

**Files:**
- Create: `$REPO/docs/teaching/clief-notes/` (directory)
- Move: `$REPO/clief_notes_skills_field_manual_v1.pdf` → `$REPO/docs/teaching/clief-notes/skills_field_manual.pdf`
- Move: `$REPO/clief_notes_resource_index_v1.pdf` → `$REPO/docs/teaching/clief-notes/resource_index.pdf`
- Move: `$REPO/docs/clief-notes-inventory.md` → `$REPO/docs/teaching/clief-notes/inventory.md`

- [ ] **Step 1: Create the destination**

Run:
```bash
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/clief-notes
```

- [ ] **Step 2: Move the two PDFs (renaming to drop version suffix)**

Run:
```bash
mv /Users/gardnerwilson/workspace/workspace-blueprint/clief_notes_skills_field_manual_v1.pdf /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/clief-notes/skills_field_manual.pdf
mv /Users/gardnerwilson/workspace/workspace-blueprint/clief_notes_resource_index_v1.pdf /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/clief-notes/resource_index.pdf
```

- [ ] **Step 3: Move the inventory markdown**

Use `git mv` so git tracks the move (the inventory was already committed in commit `61af5c3`):
```bash
git mv workspace-blueprint/docs/clief-notes-inventory.md workspace-blueprint/docs/teaching/clief-notes/inventory.md
```

- [ ] **Step 4: Verify**

Run:
```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/clief-notes/
```
Expected: `inventory.md  resource_index.pdf  skills_field_manual.pdf`

Run:
```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/clief_notes_*.pdf 2>&1 | head -1
```
Expected: `ls: /Users/.../clief_notes_*.pdf: No such file or directory`

- [ ] **Step 5: Update inventory's self-reference path**

Edit `$REPO/docs/teaching/clief-notes/inventory.md` — change the line `**Source files:** kept at the repo root for now; once the new structure lands, move both PDFs into \`docs/teaching/clief-notes/\`.` to:

```markdown
**Source files:** PDFs at `skills_field_manual.pdf` and `resource_index.pdf` in this same directory.
```

### Task 4: Stage and commit Commit 1

- [ ] **Step 1: Stage every changed/added/moved path explicitly**

`git mv` in Task 3 already staged the inventory move. Stage the rest:
```bash
git add workspace-blueprint/docs/teaching/legacy-devrel-example
git add workspace-blueprint/docs/teaching/clief-notes/skills_field_manual.pdf
git add workspace-blueprint/docs/teaching/clief-notes/resource_index.pdf
git add workspace-blueprint/docs/teaching/clief-notes/inventory.md
```

For the deletions (junk files + the three moved-from workspace dirs), `git mv` handled the inventory but the workspaces were moved with `mv`, not `git mv`. Stage those deletions + the new locations:
```bash
git add -u workspace-blueprint/writing-room workspace-blueprint/production workspace-blueprint/community workspace-blueprint/exmple.md 2>/dev/null || true
git add workspace-blueprint/docs/teaching/legacy-devrel-example/writing-room workspace-blueprint/docs/teaching/legacy-devrel-example/production workspace-blueprint/docs/teaching/legacy-devrel-example/community
```

(Note: `'New folder'` and `'New Text Document.txt'` were never tracked, so they don't need staging — `rm`/`rmdir` was sufficient.)

- [ ] **Step 2: Verify staged set is correct**

Run:
```bash
git status --short | grep workspace-blueprint
```
Expected output (order may vary):
```
A  workspace-blueprint/docs/teaching/clief-notes/inventory.md
A  workspace-blueprint/docs/teaching/clief-notes/resource_index.pdf
A  workspace-blueprint/docs/teaching/clief-notes/skills_field_manual.pdf
A  workspace-blueprint/docs/teaching/legacy-devrel-example/README.md
A  workspace-blueprint/docs/teaching/legacy-devrel-example/community/...  (multiple files)
A  workspace-blueprint/docs/teaching/legacy-devrel-example/production/...  (multiple files)
A  workspace-blueprint/docs/teaching/legacy-devrel-example/writing-room/...  (multiple files)
D  workspace-blueprint/clief_notes_resource_index_v1.pdf
D  workspace-blueprint/clief_notes_skills_field_manual_v1.pdf
D  workspace-blueprint/community/...  (if previously tracked)
D  workspace-blueprint/exmple.md  (if previously tracked)
D  workspace-blueprint/production/...  (if previously tracked)
D  workspace-blueprint/writing-room/...  (if previously tracked)
R  workspace-blueprint/docs/clief-notes-inventory.md -> workspace-blueprint/docs/teaching/clief-notes/inventory.md
```

If you see anything outside `workspace-blueprint/` staged (like `static_site/` or `.DS_Store` files), STOP and unstage those:
```bash
git reset HEAD <accidentally-staged-path>
```

Note: many of the legacy DevRel files (and the Clief PDFs) were never previously committed. They will appear as new (`A`) files in their new locations, with no corresponding `D` entries — that's expected.

- [ ] **Step 3: Commit**

Run:
```bash
git commit -m "$(cat <<'EOF'
Cleanup: remove junk, archive Acme DevRel template, organize Clief Notes

- Delete empty/junk files: exmple.md, 'New folder/', 'New Text Document.txt'
- Move writing-room/, production/, community/ (Acme DevRel template) to
  docs/teaching/legacy-devrel-example/ as a preserved teaching reference
- Move Clief Notes PDFs and inventory to docs/teaching/clief-notes/

claude-office-skills-ref/ left in place pending Commit 2 scaffolding.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: Verify commit landed**

Run:
```bash
git log --oneline -1
```
Expected: a new commit with the message above. Note its short hash for reference.

---

## COMMIT 2 — Scaffolding

This commit is the bulk of the work: create the new directory tree, every `.claude/` file, every workspace `CONTEXT.md`, all four hooks, the settings file, and decompose `claude-office-skills-ref/`. Tasks proceed structure-first (empty dirs and templates) → infrastructure (`.claude/`) → workspace docs.

### Task 5: Create top-level workspace directories

**Files:** directories only.

- [ ] **Step 1: Create the eight new top-level directories**

Run:
```bash
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/spec/{rfcs,adrs,briefs}
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/lab
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/build/workflows
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/ship/{docs,changelog,deploy}
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/shared
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/src
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/scripts
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/docs/explorations
```

- [ ] **Step 2: Add .gitkeep to every empty subdirectory git would otherwise ignore**

Run:
```bash
for d in spec/rfcs spec/adrs spec/briefs ship/docs ship/changelog ship/deploy docs/explorations; do
  touch /Users/gardnerwilson/workspace/workspace-blueprint/$d/.gitkeep
done
```

- [ ] **Step 3: Verify**

Run:
```bash
find /Users/gardnerwilson/workspace/workspace-blueprint -maxdepth 2 -type d ! -path '*/.*' | sort
```
Expected entries include:
```
/Users/gardnerwilson/workspace/workspace-blueprint
/Users/gardnerwilson/workspace/workspace-blueprint/build
/Users/gardnerwilson/workspace/workspace-blueprint/build/workflows
/Users/gardnerwilson/workspace/workspace-blueprint/docs
/Users/gardnerwilson/workspace/workspace-blueprint/docs/explorations
/Users/gardnerwilson/workspace/workspace-blueprint/lab
/Users/gardnerwilson/workspace/workspace-blueprint/scripts
/Users/gardnerwilson/workspace/workspace-blueprint/shared
/Users/gardnerwilson/workspace/workspace-blueprint/ship
/Users/gardnerwilson/workspace/workspace-blueprint/ship/changelog
/Users/gardnerwilson/workspace/workspace-blueprint/ship/deploy
/Users/gardnerwilson/workspace/workspace-blueprint/ship/docs
/Users/gardnerwilson/workspace/workspace-blueprint/spec
/Users/gardnerwilson/workspace/workspace-blueprint/spec/adrs
/Users/gardnerwilson/workspace/workspace-blueprint/spec/briefs
/Users/gardnerwilson/workspace/workspace-blueprint/spec/rfcs
/Users/gardnerwilson/workspace/workspace-blueprint/src
```

### Task 6: Create build/workflows/ stage skeleton

**Files:**
- Create: `$REPO/build/workflows/{01-spec,02-implement,03-validate,04-output}/.gitkeep`

- [ ] **Step 1: Create the four stage directories**

Run:
```bash
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/build/workflows/{01-spec,02-implement,03-validate,04-output}
for d in 01-spec 02-implement 03-validate 04-output; do
  touch /Users/gardnerwilson/workspace/workspace-blueprint/build/workflows/$d/.gitkeep
done
```

- [ ] **Step 2: Verify**

Run:
```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/build/workflows/
```
Expected: `01-spec  02-implement  03-validate  04-output`

### Task 7: Create lab/00-template/ template iteration

**Files:**
- Create: `$REPO/lab/00-template/PREFLIGHT.md`
- Create: `$REPO/lab/00-template/prototype/.gitkeep`
- Create: `$REPO/lab/00-template/VERIFY.md`
- Create: `$REPO/lab/00-template/REPORT.md`

- [ ] **Step 1: Create the template directory and prototype subdirectory**

Run:
```bash
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/lab/00-template/prototype
touch /Users/gardnerwilson/workspace/workspace-blueprint/lab/00-template/prototype/.gitkeep
```

- [ ] **Step 2: Write `lab/00-template/PREFLIGHT.md`**

```markdown
# PREFLIGHT — <iteration slug>

> Copy this folder to `lab/NN-<your-slug>/` and fill in. PREFLIGHT is your hypothesis-and-research document. Complete it BEFORE writing any prototype code.

## Hypothesis

<!-- What do you expect to find / build / prove? Single sentence if possible. -->

## Why this matters

<!-- One paragraph: what decision or downstream work depends on the answer? -->

## Prior art

<!-- What existing solutions / docs / papers / repos already address this?
List 2–5 with a one-line note on each. Use Web Search MCP if needed. -->

- [ ] Searched for existing libraries / patterns
- [ ] Reviewed relevant docs (link below)
- [ ] Identified the closest existing implementation

**Notes:**

<!-- Bullet list of findings -->

## Approach

<!-- How will you test the hypothesis? Bullet steps, not full code. -->

## Success criteria

<!-- What evidence convinces you the hypothesis is TRUE? -->

## Failure criteria

<!-- What evidence convinces you the hypothesis is FALSE?
This must be defined BEFORE writing the prototype, or you will rationalize. -->

## Time box

<!-- Walk away after: <hours/days>. Spikes that exceed their box become decisions to make, not work to push through. -->
```

- [ ] **Step 3: Write `lab/00-template/VERIFY.md`**

```markdown
# VERIFY — <iteration slug>

> Filled in AFTER the prototype runs. Records what was actually tested and what the data shows.

## What was actually built

<!-- Brief description. Link to prototype/ files. -->

## Tests performed

| Test | Input | Expected | Actual | Pass/Fail |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## Findings

<!-- What did the data show? Be specific. -->

## Surprises

<!-- Anything that didn't match expectations, in either direction. -->

## Limitations

<!-- What this experiment did NOT test. Important for the REPORT decision. -->
```

- [ ] **Step 4: Write `lab/00-template/REPORT.md`**

```markdown
# REPORT — <iteration slug>

> The decision document. Written after VERIFY. Pick exactly one outcome.

## Outcome

- [ ] **Pursue** — promote to `spec/` (RFC or brief). Why:
- [ ] **Modify** — revise the hypothesis and re-run. What changes:
- [ ] **Abandon** — not viable. Why:

## Evidence supporting the outcome

<!-- Reference VERIFY.md sections that justify the choice -->

## Open questions

<!-- Anything left unanswered, even if the outcome is "Pursue" -->

## Follow-ups

<!-- If "Pursue": draft the spec/brief title here.
     If "Modify": draft the next iteration's PREFLIGHT hypothesis.
     If "Abandon": consider writing a docs/explorations/NN-<slug>.md so the
     next person looking at this question doesn't repeat the work. -->

## Time spent

<!-- Wall-clock hours. Useful for calibrating future time boxes. -->
```

- [ ] **Step 5: Verify**

Run:
```bash
find /Users/gardnerwilson/workspace/workspace-blueprint/lab/00-template -type f | sort
```
Expected:
```
/Users/gardnerwilson/workspace/workspace-blueprint/lab/00-template/PREFLIGHT.md
/Users/gardnerwilson/workspace/workspace-blueprint/lab/00-template/REPORT.md
/Users/gardnerwilson/workspace/workspace-blueprint/lab/00-template/VERIFY.md
/Users/gardnerwilson/workspace/workspace-blueprint/lab/00-template/prototype/.gitkeep
```

### Task 8: Create build/workflows/00-template/ template iteration

**Files:**
- Create: `$REPO/build/workflows/00-template/01-spec/SPEC.md`
- Create: `$REPO/build/workflows/00-template/02-implement/notes-1.md`
- Create: `$REPO/build/workflows/00-template/03-validate/{review-N.md.template,adversary-N.md.template}`
- Create: `$REPO/build/workflows/00-template/04-output/OUTPUT.md`

- [ ] **Step 1: Create the directory tree**

Run:
```bash
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/build/workflows/00-template/{01-spec,02-implement,03-validate,04-output}
```

- [ ] **Step 2: Write `01-spec/SPEC.md`**

```markdown
# SPEC — <iteration slug>

> Output of the planner agent. Written ONCE per iteration. Contract for the implementer / reviewer / adversary loop.
> Source: <link to spec/rfcs/, spec/adrs/, spec/briefs/, or lab/NN/REPORT.md>

## Scope

<!-- What is being built. Concrete and bounded. -->

## Acceptance criteria

<!-- Testable statements. The reviewer agent uses this list verbatim to decide pass/fail. -->

- [ ] ...
- [ ] ...

## File-level plan

<!-- Which files will be created or modified. Not full code. -->

| Path | Action | Notes |
|---|---|---|
| `src/...` | create / modify | ... |

## Test strategy

<!-- What tests prove the acceptance criteria. Required before implementer can begin. -->

## Risks

<!-- What could go wrong. The adversary agent will read this and try to extend it. -->

## Out of scope

<!-- Explicit non-goals to prevent scope creep. -->
```

- [ ] **Step 3: Write `02-implement/notes-1.md`**

```markdown
# Implementer notes — cycle 1

> Working notes only. Code lands in `src/`, NOT here. This file records: assumptions made, decisions taken, anything the reviewer should know that's not in the diff.

## Spec interpretation

<!-- How the implementer read the spec. Surface ambiguities here. -->

## Decisions

<!-- Choices made during implementation, with one-line rationale each. -->

## Assumptions

<!-- Things assumed without verification. The reviewer should challenge these. -->

## Open items

<!-- Anything the implementer chose to defer; flag for reviewer/adversary attention. -->

## Files touched

<!-- List src/ files modified in this cycle, not the full diff. -->
```

- [ ] **Step 4: Write `03-validate/review-N.md.template`**

```markdown
---
cycle: N
verdict: pass | fail
verdict-reason: <one line>
---

# Reviewer report — cycle N

## Spec compliance

For each acceptance criterion in `01-spec/SPEC.md`:

| # | Criterion | Met? | Evidence |
|---|---|---|---|
| 1 | ... | yes/no | <file:line or test name> |

## Code quality findings

<!-- Issues to fix before this can pass. Be specific: file:line, what to change, why. -->

- ...

## Notes

<!-- Anything else the implementer should know. Not blockers. -->
```

- [ ] **Step 5: Write `03-validate/adversary-N.md.template`**

```markdown
---
cycle: N
findings: none | minor | critical
findings-summary: <one line>
---

# Adversary report — cycle N

## Attack surface considered

<!-- What you tried to break: input ranges, concurrency, auth, perf cliffs, error paths. -->

- ...

## Tests written

<!-- Tests added that probe edge cases. Reference src/ test paths. -->

- ...

## Critical findings

<!-- Issues that BLOCK promotion to 04-output. Each must be reproducible. -->

- ...

## Minor findings (deferred)

<!-- Issues worth filing but not blocking. -->

- ...
```

- [ ] **Step 6: Write `04-output/OUTPUT.md`**

```markdown
# OUTPUT — <iteration slug>

> Created only after the loop terminates with reviewer pass + adversary clean (or deferred). Blocked by `block-output-without-signoff.sh` hook otherwise.

## Summary

<!-- One paragraph: what was built, why, what changed. PR description material. -->

## Final commit / PR

<!-- Link to merged commit, branch name, PR URL -->

## Acceptance evidence

<!-- For each criterion in 01-spec/SPEC.md, link to the test or artifact that proves it. -->

| Criterion | Evidence |
|---|---|
| 1. ... | ... |

## Cycles required

<!-- How many implementer→review→adversary cycles ran. If >2, briefly note why. -->

## Follow-ups

<!-- Deferred adversary findings, refactor opportunities, related spikes to consider.
Each gets a brief or RFC in spec/ or a spike in lab/. -->
```

- [ ] **Step 7: Verify**

Run:
```bash
find /Users/gardnerwilson/workspace/workspace-blueprint/build/workflows/00-template -type f | sort
```
Expected: 5 files (SPEC.md, notes-1.md, review-N.md.template, adversary-N.md.template, OUTPUT.md), one per stage subdirectory.

### Task 9: Create .claude/ subdirectory structure

**Files:** directories only (content in subsequent tasks).

- [ ] **Step 1: Create the .claude tree**

Run:
```bash
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/.claude/{rules,skills,agents,reference,hooks}
```

- [ ] **Step 2: Verify**

Run:
```bash
ls -la /Users/gardnerwilson/workspace/workspace-blueprint/.claude/
```
Expected entries: `agents/`, `hooks/`, `reference/`, `rules/`, `skills/`.

---

### Task 10: Write the five `.claude/rules/` files

**Files:**
- Create: `$REPO/.claude/rules/code-quality.md`
- Create: `$REPO/.claude/rules/testing-discipline.md`
- Create: `$REPO/.claude/rules/commit-discipline.md`
- Create: `$REPO/.claude/rules/review-discipline.md`
- Create: `$REPO/.claude/rules/portability-discipline.md`

Total content budget across these five files: **<40KB** (alphadidactic discipline). Verify after writing.

- [ ] **Step 1: Write `code-quality.md`**

```markdown
# Rule: Code quality

**Linter and formatter must pass before any deliverable moves to `build/workflows/*/04-output/`.**

**Why:** A linter catch in `04-output` review is a wasted cycle. The reviewer agent's verdict is meaningless if the diff has style issues drowning out real findings.

**How to apply:**
- Implementer runs the project's lint + format commands as the last step before declaring `02-implement/` work done. Document the project's commands in `.claude/reference/tech-stack.md`.
- Type checking (where the language supports it) is mandatory. Untyped code in a typed codebase is a regression.
- No leftover `console.log`, `print`, `dbg!`, `byebug`, or equivalent debug statements in committed code. The reviewer agent flags any it finds as a critical issue.
- Imports must be sorted/grouped per the project's convention (or the formatter's default).
- Dead code (unused imports, unreachable branches, commented-out blocks) gets removed, not preserved "in case we need it." Git history is the safety net.
```

- [ ] **Step 2: Write `testing-discipline.md`**

```markdown
# Rule: Testing discipline (TDD mandatory)

**Test files are written BEFORE the implementation files they cover. Enforced by `pre-commit-tdd.sh`.**

**Why:** Tests written after the code tend to validate what the code does, not what the spec required. TDD inverts that: the test encodes the spec, the code makes the test pass. The hook prevents the slip into "I'll add tests later."

**How to apply:**
- Each acceptance criterion in `01-spec/SPEC.md` maps to at least one test. The reviewer agent verifies this mapping.
- Test files live next to the code they test (`foo.py` ↔ `test_foo.py`, `Foo.ts` ↔ `Foo.test.ts`) unless the project convention says otherwise. Document the convention in `.claude/reference/tech-stack.md`.
- The TDD loop is documented in `.claude/skills/tdd-loop/`. Follow it: red → green → refactor, one micro-step per commit ideally.
- **No `skip` / `only` / `xit` / `it.todo` in committed tests.** The reviewer flags these as critical.
- **No mocking the layer under test.** Mock external boundaries (network, clock, filesystem when scoped) but not the code path you're trying to verify.
- Coverage is a floor, not a goal. The project's coverage threshold (in `.claude/reference/tech-stack.md`) is the minimum on changed code; no global coverage chasing.
- Performance-sensitive code gets a benchmark, not just a correctness test.
```

- [ ] **Step 3: Write `commit-discipline.md`**

```markdown
# Rule: Commit discipline

**One logical change per commit. Conventional Commits format. Never bypass hooks.**

**Why:** Each commit is a unit of revertibility. A commit that mixes a feature, a refactor, and a typo fix can't be cleanly reverted if any one of them turns out wrong. Conventional Commits make the changelog generation deterministic.

**How to apply:**
- Format: `<type>(<scope>): <imperative summary under 72 chars>` where `<type>` is one of `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`, `revert`. `<scope>` is optional but useful for monorepos.
- One logical change per commit. If the diff has two distinct verbs ("add X AND fix Y"), it's two commits.
- Body (after a blank line) explains *why* if the why is non-obvious. Reference issue/PR numbers if applicable.
- **Never** `--no-verify`. If a hook fails, the hook is reporting a real problem; fix it. The hook is the rule's enforcement mechanism — bypassing it is bypassing the rule.
- **Never** `--amend` a commit that has been pushed to a shared branch. Amend only locally before pushing.
- **Never** force-push to `main` or any protected branch. Force-pushing to a personal branch you own (e.g., `feature/foo`) before opening a PR is fine.
- **Never** include sensitive files: `.env`, credentials, API keys, large binaries, OS metadata (`.DS_Store`, `Thumbs.db`). Use `.gitignore`.
- Stage explicit paths (`git add path/to/file`) rather than `git add -A` or `git add .` — the latter sweeps in unintended files.
```

- [ ] **Step 4: Write `review-discipline.md`**

```markdown
# Rule: Review discipline (multi-agent gate)

**Reviewer + adversary subagents both run before any iteration moves to `build/workflows/*/04-output/`. After 5 failed cycles, the orchestrator halts.**

**Why:** The reviewer checks compliance with the spec. The adversary checks for things the spec did not anticipate. Both run because they fail differently: the reviewer catches "you did the wrong thing"; the adversary catches "you did the right thing in a way that breaks under conditions you didn't think about."

**How to apply:**
- The reviewer agent (`.claude/agents/reviewer-agent.md`) writes `03-validate/review-N.md` with frontmatter `verdict: pass | fail`.
- The adversary agent (`.claude/agents/adversary-agent.md`) writes `03-validate/adversary-N.md` with frontmatter `findings: none | minor | critical`.
- Promotion to `04-output/` requires, on the same cycle: `verdict: pass` AND `findings: none|minor` (deferred). Enforced by `block-output-without-signoff.sh`.
- A failing cycle (reviewer rejects OR adversary finds critical) goes back to the implementer with both reports as input.
- Cycle count: each new `review-N.md` is a new cycle. After **5** failed cycles, the orchestrator stops and escalates to the human. Enforced by `block-cycle-overrun.sh`. Do not silently keep cycling — at 5 cycles the spec is likely wrong.
- The reviewer and adversary are SEPARATE subagents with isolated contexts. The reviewer must not see the implementer's reasoning beyond what's in the diff and `02-implement/notes-N.md`. The adversary must not see the reviewer's findings (they review in parallel, not in series, on each cycle).
- Reviewer + adversary apply equally to features, bugs, and refactors that flow through `build/`. Lab spikes do not require this gate (the spike's `REPORT.md` is the equivalent).
```

- [ ] **Step 5: Write `portability-discipline.md`**

```markdown
# Rule: Portability discipline

**Files in `.claude/rules/` and `.claude/skills/` must stay domain-agnostic. Project-specific facts live only in `.claude/reference/`. Enforced by `enforce-portability.sh`.**

**Why:** The whole repo is the canonical scaffold for OTHER repos. If a project-specific term ("our database is Postgres", "we use Stripe for billing") leaks into a rule or skill, that file becomes useless when copied into a project where the assumption is false. The hook catches drift mechanically.

**How to apply:**
- Anything specific to THIS repo's project, OR specific to the consumer repo at the time of bootstrap (vendor names, table names, internal endpoints, brand terms, compliance requirements), goes in `.claude/reference/` — never in `rules/` or `skills/`.
- Add new project-specific terms to `.claude/.portability-deny.txt` (one per line, case-insensitive grep). The hook fails any Edit/Write to `rules/` or `skills/` whose new content contains a denied term.
- When writing a rule or skill, reach for generic phrasing: "the project's lint command" not "`npm run lint`"; "the typed-language coverage threshold" not "70% line coverage".
- If you need a project-specific example to illustrate a rule, link to a file under `.claude/reference/` or `docs/` rather than inlining it.
- The deny list is a per-consumer artifact: each repo using this scaffold edits `.portability-deny.txt` to add its own terms. The base list shipped from this repo contains only generic placeholders the consumer should replace.
- Office skills under `.claude/skills/{docx,pptx,xlsx,pdf}/` are vendored from `anthropics/skills` and are exempt from portability scanning by path (the hook excludes them) — they're already generic.
```

- [ ] **Step 6: Verify rules total under 40KB**

Run:
```bash
wc -c /Users/gardnerwilson/workspace/workspace-blueprint/.claude/rules/*.md | tail -1
```
Expected: a `total` line under 40000 (well under 40KB; these five files together are roughly 8–12KB).

---

### Task 11: Write the six project-specific `.claude/skills/` folders

**Files:**
- Create: `$REPO/.claude/skills/tdd-loop/SKILL.md`
- Create: `$REPO/.claude/skills/bug-investigation/SKILL.md`
- Create: `$REPO/.claude/skills/refactor-protocol/SKILL.md`
- Create: `$REPO/.claude/skills/spike-protocol/SKILL.md`
- Create: `$REPO/.claude/skills/spec-authoring/SKILL.md`
- Create: `$REPO/.claude/skills/data-analysis/SKILL.md`

- [ ] **Step 1: Create the six skill directories**

Run:
```bash
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/.claude/skills/{tdd-loop,bug-investigation,refactor-protocol,spike-protocol,spec-authoring,data-analysis}
```

- [ ] **Step 2: Write `tdd-loop/SKILL.md`**

```markdown
---
name: tdd-loop
description: Use when implementing any feature, bug fix, or refactor in the build/ pipeline. Enforces test-first discipline as a tight red→green→refactor cycle. Mandatory for the implementer agent (per testing-discipline rule).
---

# TDD Loop

The unit of TDD work is a single behavior, not a single function. One behavior = one cycle = ideally one commit.

## The cycle

1. **Red.** Write the smallest test that captures the next unimplemented behavior. Name the test for the behavior, not the implementation: `test_user_can_log_in_with_valid_credentials`, not `test_login_function`.
2. **Run the test. Confirm it fails for the right reason.** A test that fails because of a syntax error elsewhere is not a red. The failure must be the *assertion* failing or the *function being missing*.
3. **Green.** Write the minimum code that makes the test pass. Resist the urge to anticipate the next test. The next test will tell you what's needed.
4. **Run all tests. Confirm everything passes.**
5. **Refactor.** With the safety net of passing tests, clean up: extract names, remove duplication, tighten signatures. Do NOT change behavior. Re-run tests after each substantive edit.
6. **Commit.** One commit captures the red+green+refactor for one behavior.

## Per-stage discipline

- **Red:** if the test passes immediately, the test is wrong (testing the wrong thing or already-existing behavior). Stop and fix the test.
- **Green:** if making the test pass requires touching files outside the obvious scope, the spec or design is wrong. Stop and revisit.
- **Refactor:** if a refactor breaks a different test, the refactor changed behavior. Revert the refactor; either keep the duplication or update the test (separately).

## When to break the cycle

- **Spike work** (lab/): TDD often unhelpful for throwaway prototypes. Use the spike-protocol skill instead.
- **Pure data migrations / config changes**: write the validation step (an assertion that the migration produced the expected state), not a unit test.
- **External-system integration**: write a contract test against a fake first; integration test against the real system later, separately.

## Anti-patterns

- Writing five tests then five implementations. The cycle is one-and-one.
- Mocking the layer under test. Mock external boundaries; real-implement what you're verifying.
- "Add tests later" — no. The pre-commit-tdd.sh hook enforces test files in the same diff as code files.
- Commenting out a failing test to "fix later." Delete it or fix it; do not leave it as silent debt.
```

- [ ] **Step 3: Write `bug-investigation/SKILL.md`**

```markdown
---
name: bug-investigation
description: Use when starting work on a reported bug or unexpected behavior. Enforces reproduce-before-fix and root-cause-before-patch. Drives a build/ iteration whose 01-spec/ is the diagnosis, not a feature plan.
---

# Bug Investigation

Bug fix work uses the same `build/` pipeline as feature work, but the SPEC.md in `01-spec/` is shaped differently — it documents diagnosis instead of design.

## The phases

### 1. Reproduce
Write a failing test that reproduces the reported behavior. **Until you can write this test, you do not understand the bug.** If you can't reproduce it locally, the spec phase isn't done; either the report is missing information (ask) or the bug is environmental (different SPEC).

The reproduction test is the single most valuable artifact in a bug investigation. It becomes the regression test once the bug is fixed.

### 2. Diagnose
Find the root cause, not the trigger. The trigger is what the user did; the root cause is the code-level reason that input produces wrong output. State both.

Common confusions:
- "Validation didn't catch the bad input" — that's a missing-validation bug AND a separate root cause for whatever the bad input then broke.
- "The function returned null" — what made it return null is the root cause, not the null itself.

Document the diagnosis in the iteration's `01-spec/SPEC.md`:
- **Trigger:** how to reproduce (link to the test)
- **Symptom:** what the user / system observed
- **Root cause:** the code-level reason (file:line)
- **Why prior tests didn't catch it:** what's missing from coverage

### 3. Fix
The implementer agent writes the minimum change that makes the reproduction test pass. Then the reviewer agent verifies the fix matches the diagnosis and adversary explores adjacent failure modes.

### 4. Regression test
The reproduction test from Phase 1 IS the regression test. It must remain in the test suite forever. The reviewer flags any attempt to delete it.

## Anti-patterns

- "Fixing" a bug by patching the symptom (catching the exception, defaulting the null) without understanding why the bad state arose.
- Closing a bug as "cannot reproduce" without asking the reporter for the missing context. Cannot-reproduce is a spec failure, not a fix.
- Deleting the reproduction test after the fix lands. The test prevents recurrence.
- Bundling the bug fix with unrelated cleanup. Fix in one commit; cleanup in another.
```

- [ ] **Step 4: Write `refactor-protocol/SKILL.md`**

```markdown
---
name: refactor-protocol
description: Use when undertaking a refactor, framework upgrade, or migration that changes structure without changing behavior. Enforces blast-radius analysis and behavior-equivalence proof.
---

# Refactor Protocol

Refactors flow through the same `build/` pipeline as features. The 01-spec/SPEC.md for a refactor differs in one way: it MUST contain a behavior-equivalence proof plan.

## The protocol

### 1. Plan (in 01-spec/SPEC.md)

Document:
- **What changes structurally:** files / modules / interfaces touched
- **What does NOT change:** the observable behavior (inputs → outputs, side effects, error cases)
- **Blast radius:** every caller of every function whose signature is changing. Use the codebase grep, not memory.
- **Migration shape:**
  - **In-place:** structure changes, no parallel implementations. Acceptable for small refactors with localized blast radius.
  - **Strangler:** new implementation in parallel, callers migrated incrementally, old removed last. Required for large refactors.
- **Rollback plan:** if the refactor introduces a regression discovered after merge, what's the revert procedure?

### 2. Behavior-equivalence proof

Before the refactor, capture the behavior:
- **Snapshot tests** of current outputs for a wide input set, OR
- **Property-based tests** that hold for both old and new implementations, OR
- **Replay tests** of recorded production traffic, OR
- **For large refactors**: implement both old and new behind a flag, run both on every call, compare outputs, log mismatches. Remove flag only after zero mismatches over a sufficient sample.

The reviewer agent verifies the proof exists BEFORE allowing implementation cycles.

### 3. Implement (incremental)

The implementer agent works in slices, each one a green-tests checkpoint:
- Each slice: make the change, all tests still pass, commit
- Slices that don't fit this shape mean the strangler pattern was needed

### 4. Validate

The reviewer agent compares behavior pre- and post-refactor using the proof from step 2. The adversary agent specifically probes the boundaries between old and new code (the migration seam is where regressions hide).

### 5. Cleanup

After the new implementation has been live and quiet for the agreed window, the old code is removed in a separate commit. The implementer does NOT delete old code in the same commit as the new code lands — it makes the diff unreviewable.

## Anti-patterns

- "Just a refactor" with no SPEC.md and no behavior-equivalence plan. There is no such thing as "just a refactor" in a non-trivial codebase.
- Renaming a public API as part of a refactor. That's a breaking change disguised as a refactor.
- Mixing refactor commits with feature commits. The diff becomes unreviewable. One commit type per commit.
- Deleting the parallel-implementation flag before the proof window closes.
```

- [ ] **Step 5: Write `spike-protocol/SKILL.md`**

```markdown
---
name: spike-protocol
description: Use when starting an exploratory iteration in lab/. Drives the PREFLIGHT → prototype → VERIFY → REPORT shape. Output is a learning, not shipped code.
---

# Spike Protocol

A spike is a time-boxed experiment whose output is a *decision*, not a deliverable. Code written in a spike is throwaway by default — promoted to `src/` only by going through `spec/` and `build/`.

## The shape

Every spike iteration is a folder under `lab/NN-<slug>/` (copy from `lab/00-template/`). It contains, in order:

1. **`PREFLIGHT.md`** — written before any code. Hypothesis + prior art + success/failure criteria + time box.
2. **`prototype/`** — the code. Throwaway. No production patterns required (no tests, no error handling, no logging) unless they're part of what you're testing.
3. **`VERIFY.md`** — written after running the prototype. Tests performed, findings, surprises, limitations.
4. **`REPORT.md`** — the decision. Pursue, modify, or abandon.

## Discipline

### Write PREFLIGHT first
Define success and failure criteria BEFORE writing the prototype. Otherwise you'll rationalize whatever the prototype produces as a "result." Use Web Search MCP to canvas prior art.

### Honor the time box
A spike that runs over its time box is a different kind of work. Stop, write the REPORT with what you have, and decide explicitly whether the spike continues with a new (longer) time box or transitions into spec/build.

### The prototype is not the deliverable
If the spike's outcome is "Pursue," the prototype's role is over. Write a `spec/rfcs/` document or `spec/briefs/` entry, then start a fresh `build/workflows/NN-<slug>/` iteration. Do NOT promote the prototype code directly to `src/` — it will carry the throwaway code's compromises into production.

### Abandoned spikes are valuable
If REPORT outcome is "Abandon," write a `docs/explorations/NN-<slug>.md` so the next person investigating the same question doesn't repeat the work. State what was tried, what didn't work, and *why* — the why is the load-bearing part.

## When NOT to use this skill

- The work is "build feature X" — that's `build/`, not `lab/`. Even if you don't know exactly how, the planner agent's job is to figure out how.
- The work is a bug investigation — use `bug-investigation` skill, drives `build/`.
- The work is a refactor — use `refactor-protocol` skill, drives `build/`.
- You already know the answer — that's a spec, not a spike.
```

- [ ] **Step 6: Write `spec-authoring/SKILL.md`**

```markdown
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
```

- [ ] **Step 7: Write `data-analysis/SKILL.md`**

```markdown
---
name: data-analysis
description: Use when the work involves analyzing data, computing statistics, or producing visualizations from data files. Encodes the trigger phrasing for code-execution that yields better results.
---

# Data Analysis

Code execution (the Python sandbox in Claude.ai, or local execution via Claude Code) is the right tool for any computation that needs a real answer rather than a confident guess. The trigger phrasing matters.

## The phrasing rule

**Tell Claude what you want to know, not what code to write.**

Better: *"What's the average deal size by quarter from this spreadsheet?"*
Worse: *"Write a pandas script to calculate quarterly deal-size averages."*

Why: Claude knows several ways to compute the answer (pandas, numpy, raw Python, sqlite-in-memory). Letting Claude choose produces shorter, more reliable code. The "write a pandas script" framing forces a specific implementation path that may not be the best fit for the data.

## When to use

- Precise calculations (statistics, financial math, anything where rounding matters)
- Verification work (running the code rather than reasoning about it)
- Charts and visualizations from real data
- File processing (parsing CSVs, transforming JSON, batch-renaming images)
- Numeric checks during code review (does this benchmark actually show what the PR claims?)

## When to skip

- Conceptual questions ("should we use Postgres or MySQL?")
- Quick lookups that don't need real data
- Cases where the computation is simple enough to do mentally and the data is in front of you

## In `lab/` iterations

Data-heavy spikes often live entirely in code execution: load the data, compute, plot, decide. The prototype/ folder may have nothing more than a script (or a notebook export) and the VERIFY.md captures the numbers.

## In `build/` iterations

Code execution is for one-off questions during implementation, not for production code. Production data-processing code lives in `src/` and goes through TDD. If the implementer finds themselves running the same computation manually three times, that's a signal to lift it into `src/` with tests.
```

- [ ] **Step 8: Verify all six skills exist with frontmatter**

Run:
```bash
for s in tdd-loop bug-investigation refactor-protocol spike-protocol spec-authoring data-analysis; do
  f=/Users/gardnerwilson/workspace/workspace-blueprint/.claude/skills/$s/SKILL.md
  if [ ! -f "$f" ]; then echo "MISSING: $f"; continue; fi
  head -5 "$f" | grep -q '^name:' && echo "$s: OK" || echo "$s: NO FRONTMATTER"
done
```
Expected: all six print `OK`.

---

### Task 12: Decompose `claude-office-skills-ref/` into its three new homes

**Files moved:**
- `claude-office-skills-ref/public/{docx,pptx,xlsx,pdf}/` → `.claude/skills/{docx,pptx,xlsx,pdf}/`
- `claude-office-skills-ref/skills-system.md` → `.claude/reference/skills-system.md`
- `claude-office-skills-ref/{README.md,CLAUDE.md,package.json,package-lock.json,requirements.txt,html2pptx-local.cjs}` → `docs/teaching/office-skills-source/`

After the moves, `claude-office-skills-ref/` should be empty and is removed.

- [ ] **Step 1: Create the destinations**

Run:
```bash
mkdir -p /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/office-skills-source
```

(`.claude/skills/` and `.claude/reference/` already exist from Task 9.)

- [ ] **Step 2: Inspect what's tracked vs untracked**

Run:
```bash
git ls-files /Users/gardnerwilson/workspace/workspace-blueprint/claude-office-skills-ref/ | head -20 && echo "---" && git ls-files --others --exclude-standard /Users/gardnerwilson/workspace/workspace-blueprint/claude-office-skills-ref/ | head -20
```
This tells you which files are tracked (use `git mv`) vs untracked (use `mv` and stage as new).

- [ ] **Step 3: Move the four office skills (use `mv` not `git mv` if files are untracked; the prior step tells you)**

If tracked, run:
```bash
git mv workspace-blueprint/claude-office-skills-ref/public/docx workspace-blueprint/.claude/skills/docx
git mv workspace-blueprint/claude-office-skills-ref/public/pptx workspace-blueprint/.claude/skills/pptx
git mv workspace-blueprint/claude-office-skills-ref/public/xlsx workspace-blueprint/.claude/skills/xlsx
git mv workspace-blueprint/claude-office-skills-ref/public/pdf  workspace-blueprint/.claude/skills/pdf
```

If untracked, run:
```bash
mv /Users/gardnerwilson/workspace/workspace-blueprint/claude-office-skills-ref/public/docx /Users/gardnerwilson/workspace/workspace-blueprint/.claude/skills/docx
mv /Users/gardnerwilson/workspace/workspace-blueprint/claude-office-skills-ref/public/pptx /Users/gardnerwilson/workspace/workspace-blueprint/.claude/skills/pptx
mv /Users/gardnerwilson/workspace/workspace-blueprint/claude-office-skills-ref/public/xlsx /Users/gardnerwilson/workspace/workspace-blueprint/.claude/skills/xlsx
mv /Users/gardnerwilson/workspace/workspace-blueprint/claude-office-skills-ref/public/pdf  /Users/gardnerwilson/workspace/workspace-blueprint/.claude/skills/pdf
```

- [ ] **Step 4: Move `skills-system.md` to reference**

Tracked vs untracked logic same as above. If untracked:
```bash
mv /Users/gardnerwilson/workspace/workspace-blueprint/claude-office-skills-ref/skills-system.md /Users/gardnerwilson/workspace/workspace-blueprint/.claude/reference/skills-system.md
```

If tracked, use `git mv` with the same arguments.

- [ ] **Step 5: Move provenance files to `docs/teaching/office-skills-source/`**

```bash
for f in README.md CLAUDE.md package.json package-lock.json requirements.txt html2pptx-local.cjs; do
  src=/Users/gardnerwilson/workspace/workspace-blueprint/claude-office-skills-ref/$f
  dst=/Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/office-skills-source/$f
  if [ -f "$src" ]; then mv "$src" "$dst"; fi
done
```

- [ ] **Step 6: Verify `claude-office-skills-ref/` is now empty (or only `public/` empty shell)**

Run:
```bash
find /Users/gardnerwilson/workspace/workspace-blueprint/claude-office-skills-ref -type f
```
Expected: no output (no files left).

- [ ] **Step 7: Remove the empty directories**

Run:
```bash
rmdir /Users/gardnerwilson/workspace/workspace-blueprint/claude-office-skills-ref/public 2>/dev/null
rmdir /Users/gardnerwilson/workspace/workspace-blueprint/claude-office-skills-ref
```

If `rmdir` fails ("directory not empty"), there are unexpected files left. Investigate before forcing.

- [ ] **Step 8: Verify the three destinations**

Run:
```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/.claude/skills/
ls /Users/gardnerwilson/workspace/workspace-blueprint/.claude/reference/skills-system.md
ls /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/office-skills-source/
```
Expected:
- `.claude/skills/` contains `bug-investigation  data-analysis  docx  pdf  pptx  refactor-protocol  spec-authoring  spike-protocol  tdd-loop  xlsx`
- `.claude/reference/skills-system.md` exists (file path printed)
- `docs/teaching/office-skills-source/` contains the six provenance files (any subset that existed)

- [ ] **Step 9: Verify each office skill still has a SKILL.md after the move**

Run:
```bash
for s in docx pptx xlsx pdf; do
  f=/Users/gardnerwilson/workspace/workspace-blueprint/.claude/skills/$s/SKILL.md
  if [ -f "$f" ]; then echo "$s: OK"; else echo "$s: MISSING SKILL.md"; fi
done
```
Expected: all four print `OK`.

---

### Task 13: Write the four `.claude/agents/` specs

**Files:**
- Create: `$REPO/.claude/agents/planner-agent.md`
- Create: `$REPO/.claude/agents/implementer-agent.md`
- Create: `$REPO/.claude/agents/reviewer-agent.md`
- Create: `$REPO/.claude/agents/adversary-agent.md`

Each is a markdown file with YAML frontmatter (per Claude Code subagent format) followed by a system prompt.

- [ ] **Step 1: Write `planner-agent.md`**

```markdown
---
name: planner
description: One-shot agent that converts a spec/ source artifact (RFC, ADR, brief, or lab REPORT) into a buildable SPEC.md for an iteration in build/workflows/. Does NOT implement. Exits after producing SPEC.md.
tools: Read, Write, Edit, Bash, Grep, Glob
---

# Planner Agent

You are the planner. You read one source artifact and produce one SPEC.md. You do not write code, do not run tests, do not modify src/. After SPEC.md is written, you exit.

## Inputs

- One source artifact, given by the orchestrator. One of:
  - `spec/rfcs/<slug>.md` (Status: Accepted)
  - `spec/adrs/<NNNN>-<slug>.md`
  - `spec/briefs/<slug>.md`
  - `lab/<NN>-<slug>/REPORT.md` (Outcome: Pursue)
- The full `.claude/reference/` directory — read whatever is relevant (project-architecture.md, tech-stack.md, glossary.md).
- The `.claude/rules/` directory — your output must produce work that complies with these rules.

## Output

Exactly one file: `build/workflows/<NN>-<slug>/01-spec/SPEC.md`. The directory will be created by the orchestrator before invoking you.

## SPEC.md structure

```
# SPEC — <iteration slug>
> Source: <link to source artifact>

## Scope
<concrete, bounded statement of what's being built>

## Acceptance criteria
<numbered, testable statements>

## File-level plan
<table: path | action | notes>

## Test strategy
<how each acceptance criterion will be verified>

## Risks
<things that could go wrong; the adversary will read this>

## Out of scope
<explicit non-goals>
```

## Discipline

- **Acceptance criteria are testable.** "Login form looks good" is not testable. "Login form rejects passwords under 8 chars with message X" is.
- **File-level plan uses real paths.** Verify they exist (or specify they'll be created) by reading the codebase.
- **Test strategy maps 1:1 to acceptance criteria.** Each criterion gets at least one test.
- **Risks section is honest.** This isn't a sales pitch; it's a contract. The adversary agent reads this and tries to extend it.
- **Stay under the spec.** If the source artifact says X, do not add Y "while you're at it." Out-of-scope is your release valve.

## Re-planning

If new information requires the spec to change, the orchestrator re-invokes you with new inputs. You do not edit existing SPEC.md files in-place; you produce a new SPEC.md (with a version note in its header) and the orchestrator decides which one to use.

## Termination

After Write of SPEC.md succeeds, end your turn. Do not proceed into implementation. Do not invoke other agents.
```

- [ ] **Step 2: Write `implementer-agent.md`**

```markdown
---
name: implementer
description: Writes production code in src/ to satisfy a SPEC.md. Reads the SPEC and the latest reviewer + adversary findings each cycle. Code goes to src/; process notes to 02-implement/.
tools: Read, Write, Edit, Bash, Grep, Glob
---

# Implementer Agent

You write code that makes a SPEC.md's acceptance criteria pass. You follow TDD (`.claude/skills/tdd-loop/`). Your code lives in `src/` (and `shared/` if you're building reusable infrastructure). Your process notes live in `build/workflows/<NN>-<slug>/02-implement/notes-<cycle>.md`.

## Inputs

Each cycle, you read:
- `build/workflows/<NN>-<slug>/01-spec/SPEC.md` — the contract
- `build/workflows/<NN>-<slug>/03-validate/review-<latest>.md` — if it exists; the previous cycle's reviewer findings
- `build/workflows/<NN>-<slug>/03-validate/adversary-<latest>.md` — if it exists; the previous cycle's adversary findings
- `build/workflows/<NN>-<slug>/02-implement/notes-<previous>.md` — if it exists; your own prior cycle notes
- `.claude/skills/tdd-loop/SKILL.md` — mandatory invocation per testing-discipline rule
- `.claude/rules/` — all of them; you follow them
- `.claude/reference/tech-stack.md` and `.claude/reference/project-architecture.md` — for project-specific commands and patterns

## Output

- Code (and tests) in `src/` or `shared/`
- `build/workflows/<NN>-<slug>/02-implement/notes-<cycle>.md` — your decisions, assumptions, files touched
- A clean git state at end of cycle (commits per the commit-discipline rule)

## Discipline

- **TDD is non-negotiable.** Test first, then code. The pre-commit-tdd.sh hook enforces it.
- **Address every "fail" finding from the previous cycle.** If you disagree with a finding, document the disagreement in `notes-<cycle>.md`; do not silently ignore it. The reviewer will see this.
- **Adversary findings of `critical` are blockers.** `minor (deferred)` findings can be deferred if they don't compromise the SPEC's acceptance criteria.
- **Stay inside the spec's File-level plan.** If you need to touch a file the spec didn't list, that's a sign the spec is wrong; document this in `notes-<cycle>.md` so the planner can revise.
- **Code goes to `src/`. Process notes go to `02-implement/`.** Never the reverse.
- **Commit per the commit-discipline rule.** Conventional Commits, one logical change per commit.

## Termination

End your cycle when:
- All acceptance criteria from SPEC.md have implementation + tests, AND
- All previous-cycle blocker findings (review:fail or adversary:critical) are addressed, AND
- The local test suite passes, AND
- You've written `notes-<cycle>.md` and committed your changes.

You do NOT decide whether the iteration is "done." That's the reviewer + adversary's call. Hand back to the orchestrator.
```

- [ ] **Step 3: Write `reviewer-agent.md`**

```markdown
---
name: reviewer
description: Reviews the implementer's diff against the SPEC.md acceptance criteria and the .claude/rules/. Writes verdict + findings to 03-validate/review-N.md. Runs in parallel with the adversary each cycle.
tools: Read, Bash, Grep, Glob
---

# Reviewer Agent

You verify that the implementer's work satisfies the SPEC.md and complies with `.claude/rules/`. You do NOT write code. You do NOT run lengthy operations. You read the diff, you read the spec, you write a verdict.

## Inputs

- `build/workflows/<NN>-<slug>/01-spec/SPEC.md` — the contract you check against
- The git diff for this cycle (run `git diff` against the appropriate base; the orchestrator gives you the base ref)
- `build/workflows/<NN>-<slug>/02-implement/notes-<cycle>.md` — context for what the implementer did
- `.claude/rules/` — every rule applies; cite by filename
- `.claude/reference/project-architecture.md` and `.claude/reference/tech-stack.md` — for project conventions

You do NOT read the adversary's findings (they run in parallel; you don't influence each other within a cycle).

## Output

`build/workflows/<NN>-<slug>/03-validate/review-<cycle>.md` with this exact frontmatter:

```
---
cycle: <N>
verdict: pass | fail
verdict-reason: <one line>
---
```

Body:
- **Spec compliance table** — one row per acceptance criterion with met/not-met + evidence (file:line or test name)
- **Code quality findings** — issues to fix, ordered by severity. Each finding has file:line, what to change, why (cite the rule).
- **Notes** — non-blocking observations the implementer should know about.

## Discipline

- **`verdict: pass` means EVERY acceptance criterion is met AND no rule violations.** A single unmet criterion is `verdict: fail`. A single rule violation is `verdict: fail`.
- **Cite the rule when you flag.** "Linter would catch this (`.claude/rules/code-quality.md`)" not just "this is bad style."
- **Findings must be actionable.** Each finding tells the implementer exactly what to change. "Improve error handling" is not a finding; "Catch and re-raise as `XError` at `src/foo.py:42` per error-handling pattern" is.
- **You don't propose alternative designs.** That's the planner's job. If the design is wrong, your verdict is `fail` with `verdict-reason: design diverges from spec; planner needs to revise SPEC.md`.
- **You don't run the test suite.** That's the implementer's job (and the CI). You verify tests EXIST for each acceptance criterion and that they look like they would pass; the actual passing is the implementer's checkpoint.

## Termination

End your turn after writing `review-<cycle>.md`. The orchestrator decides what happens next based on your verdict + the adversary's findings.
```

- [ ] **Step 4: Write `adversary-agent.md`**

```markdown
---
name: adversary
description: Tries to break the implementer's work — finds edge cases, attack surfaces, performance cliffs, race conditions. Writes findings to 03-validate/adversary-N.md. Runs in parallel with the reviewer each cycle.
tools: Read, Bash, Grep, Glob, Edit, Write
---

# Adversary Agent

Your job is to find what's NOT in the spec — what the implementer didn't think about. You assume the SPEC.md is incomplete (it always is). You probe.

## Inputs

- `build/workflows/<NN>-<slug>/01-spec/SPEC.md` — the spec, especially its **Risks** section (extend it)
- The git diff for this cycle
- `build/workflows/<NN>-<slug>/02-implement/notes-<cycle>.md` — the implementer's assumptions (challenge them)
- `.claude/reference/` — read what's relevant for context (project-architecture.md, tech-stack.md)

You do NOT read the reviewer's findings (you run in parallel within a cycle).

## Output

`build/workflows/<NN>-<slug>/03-validate/adversary-<cycle>.md` with this exact frontmatter:

```
---
cycle: <N>
findings: none | minor | critical
findings-summary: <one line>
---
```

Body:
- **Attack surface considered** — what categories you probed (input ranges, concurrency, auth, perf, error paths, idempotency, etc.)
- **Tests written** — list any failing tests you added under `src/` (or wherever tests live) that probe edge cases. Reference the test paths.
- **Critical findings** — things that BLOCK promotion. Each must be reproducible (with a failing test where possible).
- **Minor findings (deferred)** — issues worth recording but not blocking.

## Discipline

- **You may write tests.** Adding a failing test that exposes an edge case is your most powerful tool. Mark such tests clearly (e.g., comment `# adversary: edge case for SPEC criterion N`) so the implementer knows their origin.
- **A "critical" finding is one that violates the spec OR breaks the implementation in a plausible production scenario.** "Could fail if the moon is full" is minor. "Fails if input is empty string" is critical (most APIs receive empty strings).
- **Look at the categories the spec didn't mention.** If the spec says nothing about timezones, that's where to look. If the spec says nothing about Unicode, probe Unicode. The spec's silences are your map.
- **Do NOT propose fixes.** Your job is finding, not solving. Each critical finding tells the implementer what's broken; they decide how to fix.
- **Do NOT modify production code in `src/`.** You may write tests there. If you find yourself wanting to fix something, that's a finding, not an action.

## Termination

End your turn after writing `adversary-<cycle>.md` (and any test files you added). Orchestrator decides what's next.
```

- [ ] **Step 5: Verify all four agents exist with frontmatter**

Run:
```bash
for a in planner implementer reviewer adversary; do
  f=/Users/gardnerwilson/workspace/workspace-blueprint/.claude/agents/$a-agent.md
  if [ ! -f "$f" ]; then echo "MISSING: $f"; continue; fi
  head -5 "$f" | grep -q "^name: $a$" && echo "$a: OK" || echo "$a: NAME MISMATCH"
done
```
Expected: all four print `OK`.

---

### Task 14: Write the four `.claude/hooks/` bash scripts

**Files:**
- Create: `$REPO/.claude/hooks/pre-commit-tdd.sh` (executable)
- Create: `$REPO/.claude/hooks/block-cycle-overrun.sh` (executable)
- Create: `$REPO/.claude/hooks/block-output-without-signoff.sh` (executable)
- Create: `$REPO/.claude/hooks/enforce-portability.sh` (executable)

**Hook protocol assumed:** Claude Code passes a JSON tool-call payload on stdin. Hooks exit 0 to allow, exit non-zero (with a stderr message) to block. Outputs: messages on stderr; agent sees the message in the blocked-tool error. Hooks use `jq` (assume installed; document in MCP-SETUP.md if not).

- [ ] **Step 1: Write `pre-commit-tdd.sh`**

```bash
#!/usr/bin/env bash
# Hook: pre-commit-tdd.sh
# Trigger: PreToolUse on Bash with `git commit`
# Behavior: Block commit if code files have no corresponding test files in the same diff.
# Exempt: docs-only commits (no source files), config-only commits, the first commit.

set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // ""')
command=$(echo "$input" | jq -r '.tool_input.command // ""')

# Only act on git commit invocations
if [[ "$tool_name" != "Bash" ]]; then exit 0; fi
if [[ ! "$command" =~ ^[[:space:]]*git[[:space:]]+commit ]]; then exit 0; fi

# Get the staged file list. Empty stage means git itself will block; let it.
staged=$(git diff --cached --name-only)
if [[ -z "$staged" ]]; then exit 0; fi

# Configurable: extensions considered "code" (not docs/config)
code_re='\.(py|ts|tsx|js|jsx|rs|go|rb|java|kt|swift|c|cpp|h|hpp|cs)$'
test_re='(^|/)(test_|tests?/|.*\.test\.|.*_test\.|.*\.spec\.)'

code_changed=0
test_changed=0
while IFS= read -r f; do
  if [[ "$f" =~ $code_re ]]; then
    if [[ "$f" =~ $test_re ]]; then
      test_changed=1
    else
      code_changed=1
    fi
  fi
done <<< "$staged"

if [[ $code_changed -eq 1 && $test_changed -eq 0 ]]; then
  cat >&2 <<EOF
[pre-commit-tdd] BLOCKED: this commit changes code files but adds no test files.

Per .claude/rules/testing-discipline.md, tests are written before (or with) the code they cover.

Staged code files (no matching test changes detected):
$(echo "$staged" | grep -E "$code_re" | grep -vE "$test_re" | sed 's/^/  - /')

Options:
  1. Add the corresponding test file changes to the same commit.
  2. If this is genuinely a non-tested change (refactor with snapshot proof, doc change in code, generated file), document why in the commit body and disable this hook in .claude/settings.json for the duration of the work, then re-enable.
EOF
  exit 1
fi

exit 0
```

- [ ] **Step 2: Write `block-cycle-overrun.sh`**

```bash
#!/usr/bin/env bash
# Hook: block-cycle-overrun.sh
# Trigger: PreToolUse on Edit | Write when target path is build/workflows/*/03-validate/
# Behavior: Block if 5 or more review-N.md files already exist in the target dir.

set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // ""')

case "$tool_name" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

target=$(echo "$input" | jq -r '.tool_input.file_path // ""')
if [[ -z "$target" ]]; then exit 0; fi

# Only fire for paths inside build/workflows/<slug>/03-validate/
if [[ ! "$target" =~ /build/workflows/[^/]+/03-validate/ ]]; then exit 0; fi

# Find the iteration's 03-validate dir from the target path
validate_dir=$(echo "$target" | sed 's|\(.*/03-validate\)/.*|\1|')

# Count existing review-N.md (any N)
review_count=$(find "$validate_dir" -maxdepth 1 -type f -name 'review-*.md' 2>/dev/null | wc -l | tr -d ' ')

if [[ "$review_count" -ge 5 ]]; then
  cat >&2 <<EOF
[block-cycle-overrun] BLOCKED: this iteration already has $review_count review cycles.

Per .claude/rules/review-discipline.md, the loop halts at 5 cycles. After this many failed cycles, the spec is likely wrong (not the implementation).

Iteration: $validate_dir

Required action:
  1. Stop the implementer/reviewer/adversary loop.
  2. Re-engage the planner with revised inputs (likely the original source artifact in spec/ needs revision).
  3. Generate a NEW iteration directory (build/workflows/<NN+1>-<slug>-v2/) rather than continuing this one.
  4. Document the escalation in 04-output/ESCALATION.md before opening a new iteration.
EOF
  exit 1
fi

exit 0
```

- [ ] **Step 3: Write `block-output-without-signoff.sh`**

```bash
#!/usr/bin/env bash
# Hook: block-output-without-signoff.sh
# Trigger: PreToolUse on Edit | Write when target path is build/workflows/*/04-output/
# Behavior: Block unless latest review-N.md has verdict: pass AND latest adversary-N.md
#           has findings: none|minor.

set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // ""')

case "$tool_name" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

target=$(echo "$input" | jq -r '.tool_input.file_path // ""')
if [[ -z "$target" ]]; then exit 0; fi

# Only fire for paths inside build/workflows/<slug>/04-output/
if [[ ! "$target" =~ /build/workflows/[^/]+/04-output/ ]]; then exit 0; fi

# Allow .gitkeep / .keep without sign-off (placeholder files)
basename=$(basename "$target")
if [[ "$basename" == ".gitkeep" || "$basename" == ".keep" ]]; then exit 0; fi

iteration_dir=$(echo "$target" | sed 's|\(.*\)/04-output/.*|\1|')
validate_dir="$iteration_dir/03-validate"

if [[ ! -d "$validate_dir" ]]; then
  cat >&2 <<EOF
[block-output-without-signoff] BLOCKED: no 03-validate/ directory at $validate_dir.
Reviewer + adversary must run before output. See .claude/rules/review-discipline.md.
EOF
  exit 1
fi

# Find latest review-N.md and adversary-N.md
latest_review=$(find "$validate_dir" -maxdepth 1 -type f -name 'review-*.md' | sort -V | tail -1)
latest_adv=$(find "$validate_dir" -maxdepth 1 -type f -name 'adversary-*.md' | sort -V | tail -1)

if [[ -z "$latest_review" || -z "$latest_adv" ]]; then
  cat >&2 <<EOF
[block-output-without-signoff] BLOCKED: missing review or adversary report.
  Latest review:    ${latest_review:-NONE}
  Latest adversary: ${latest_adv:-NONE}
Both required. See .claude/rules/review-discipline.md.
EOF
  exit 1
fi

# Parse frontmatter for verdict and findings
verdict=$(awk '/^verdict:/{print $2; exit}' "$latest_review" | tr -d '"')
findings=$(awk '/^findings:/{print $2; exit}' "$latest_adv" | tr -d '"')

if [[ "$verdict" != "pass" ]]; then
  cat >&2 <<EOF
[block-output-without-signoff] BLOCKED: latest review verdict is "$verdict" (need "pass").
File: $latest_review
EOF
  exit 1
fi

case "$findings" in
  none|minor) ;;
  *)
    cat >&2 <<EOF
[block-output-without-signoff] BLOCKED: latest adversary findings is "$findings" (need "none" or "minor").
File: $latest_adv
EOF
    exit 1
    ;;
esac

exit 0
```

- [ ] **Step 4: Write `enforce-portability.sh`**

```bash
#!/usr/bin/env bash
# Hook: enforce-portability.sh
# Trigger: PostToolUse on Edit | Write when target path is .claude/rules/ or .claude/skills/
# Behavior: Grep the file content against .claude/.portability-deny.txt; fail if any
#           denied term is found (case-insensitive, word-ish boundaries).
# Exempt path: .claude/skills/{docx,pptx,xlsx,pdf}/ — vendored from anthropics/skills.

set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // ""')

case "$tool_name" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

target=$(echo "$input" | jq -r '.tool_input.file_path // ""')
if [[ -z "$target" ]]; then exit 0; fi

# Only fire on .claude/rules/ or .claude/skills/
if [[ ! "$target" =~ /\.claude/(rules|skills)/ ]]; then exit 0; fi

# Exempt vendored office skills
if [[ "$target" =~ /\.claude/skills/(docx|pptx|xlsx|pdf)/ ]]; then exit 0; fi

# Locate the deny list relative to the .claude/ root
claude_root=$(echo "$target" | sed 's|\(.*/\.claude\)/.*|\1|')
deny_file="$claude_root/.portability-deny.txt"

if [[ ! -f "$deny_file" ]]; then
  # No deny list = nothing to enforce. Not an error.
  exit 0
fi

# File must exist (PostToolUse runs after the write)
if [[ ! -f "$target" ]]; then exit 0; fi

violations=()
while IFS= read -r term || [[ -n "$term" ]]; do
  # Skip blank lines and comments
  term=$(echo "$term" | sed 's/#.*$//' | xargs)
  [[ -z "$term" ]] && continue

  if grep -qi -- "$term" "$target"; then
    violations+=("$term")
  fi
done < "$deny_file"

if [[ ${#violations[@]} -gt 0 ]]; then
  cat >&2 <<EOF
[enforce-portability] VIOLATION: domain-specific terms found in $target
  $(printf '  - %s\n' "${violations[@]}")

Per .claude/rules/portability-discipline.md, files in .claude/rules/ and .claude/skills/ must stay domain-agnostic. Move the project-specific reference to .claude/reference/ instead.

Edit your file to remove these terms (or generalize the phrasing), then write again.
EOF
  exit 1
fi

exit 0
```

- [ ] **Step 5: Make all four hooks executable**

Run:
```bash
chmod +x /Users/gardnerwilson/workspace/workspace-blueprint/.claude/hooks/*.sh
```

- [ ] **Step 6: Smoke-test pre-commit-tdd.sh**

Run with a fake commit-without-tests payload:
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"x\""}}' | /Users/gardnerwilson/workspace/workspace-blueprint/.claude/hooks/pre-commit-tdd.sh; echo "EXIT=$?"
```
Expected: `EXIT=0` (because there are no staged files yet — empty stage exits OK so git itself can complain).

Run with non-Bash tool:
```bash
echo '{"tool_name":"Read","tool_input":{"file_path":"foo"}}' | /Users/gardnerwilson/workspace/workspace-blueprint/.claude/hooks/pre-commit-tdd.sh; echo "EXIT=$?"
```
Expected: `EXIT=0`.

- [ ] **Step 7: Smoke-test block-cycle-overrun.sh**

Create a fake validate dir with 5 review files and try to write a 6th:
```bash
mkdir -p /tmp/fakeit/build/workflows/01-foo/03-validate
for n in 1 2 3 4 5; do touch /tmp/fakeit/build/workflows/01-foo/03-validate/review-$n.md; done
echo '{"tool_name":"Write","tool_input":{"file_path":"/tmp/fakeit/build/workflows/01-foo/03-validate/review-6.md"}}' \
  | /Users/gardnerwilson/workspace/workspace-blueprint/.claude/hooks/block-cycle-overrun.sh
echo "EXIT=$?"
```
Expected: stderr message about overrun, `EXIT=1`.

Cleanup:
```bash
rm -rf /tmp/fakeit
```

- [ ] **Step 8: Smoke-test block-output-without-signoff.sh**

Create a fake iteration with passing review + clean adversary, try to write to 04-output:
```bash
mkdir -p /tmp/fakeit/build/workflows/01-foo/03-validate /tmp/fakeit/build/workflows/01-foo/04-output
cat > /tmp/fakeit/build/workflows/01-foo/03-validate/review-1.md <<'X'
---
cycle: 1
verdict: pass
verdict-reason: ok
---
X
cat > /tmp/fakeit/build/workflows/01-foo/03-validate/adversary-1.md <<'X'
---
cycle: 1
findings: none
findings-summary: ok
---
X
echo '{"tool_name":"Write","tool_input":{"file_path":"/tmp/fakeit/build/workflows/01-foo/04-output/OUTPUT.md"}}' \
  | /Users/gardnerwilson/workspace/workspace-blueprint/.claude/hooks/block-output-without-signoff.sh
echo "PASS_CASE_EXIT=$?"
```
Expected: `PASS_CASE_EXIT=0`.

Now flip review to fail:
```bash
sed -i '' 's/verdict: pass/verdict: fail/' /tmp/fakeit/build/workflows/01-foo/03-validate/review-1.md
echo '{"tool_name":"Write","tool_input":{"file_path":"/tmp/fakeit/build/workflows/01-foo/04-output/OUTPUT.md"}}' \
  | /Users/gardnerwilson/workspace/workspace-blueprint/.claude/hooks/block-output-without-signoff.sh
echo "FAIL_CASE_EXIT=$?"
```
Expected: stderr message, `FAIL_CASE_EXIT=1`.

Cleanup:
```bash
rm -rf /tmp/fakeit
```

- [ ] **Step 9: Smoke-test enforce-portability.sh**

Create a fake .claude with a deny list and a violating rule file:
```bash
mkdir -p /tmp/fakeit/.claude/rules
echo "stripe" > /tmp/fakeit/.claude/.portability-deny.txt
echo "We use Stripe for billing." > /tmp/fakeit/.claude/rules/foo.md

echo '{"tool_name":"Write","tool_input":{"file_path":"/tmp/fakeit/.claude/rules/foo.md"}}' \
  | /Users/gardnerwilson/workspace/workspace-blueprint/.claude/hooks/enforce-portability.sh
echo "VIOLATE_EXIT=$?"
```
Expected: stderr listing `stripe`, `VIOLATE_EXIT=1`.

Now neutralize the file:
```bash
echo "We use a billing provider configured in .claude/reference/tech-stack.md." > /tmp/fakeit/.claude/rules/foo.md
echo '{"tool_name":"Write","tool_input":{"file_path":"/tmp/fakeit/.claude/rules/foo.md"}}' \
  | /Users/gardnerwilson/workspace/workspace-blueprint/.claude/hooks/enforce-portability.sh
echo "CLEAN_EXIT=$?"
```
Expected: `CLEAN_EXIT=0`.

Cleanup:
```bash
rm -rf /tmp/fakeit
```

- [ ] **Step 10: Verify all four hooks are executable**

Run:
```bash
ls -l /Users/gardnerwilson/workspace/workspace-blueprint/.claude/hooks/*.sh | awk '{print $1, $NF}'
```
Expected: each line starts with `-rwxr-xr-x` (or similar with `x` bits).

---

### Task 15: Write `.portability-deny.txt` and `settings.json`

**Files:**
- Create: `$REPO/.claude/.portability-deny.txt`
- Create: `$REPO/.claude/settings.json`

- [ ] **Step 1: Write `.portability-deny.txt`**

```
# .portability-deny.txt — domain-specific terms that must not appear in
# .claude/rules/ or .claude/skills/ (enforced by enforce-portability.sh).
#
# Format: one term per line. Lines starting with # are comments. Blank lines
# are ignored. Matching is case-insensitive substring grep.
#
# Each consumer repo edits this list to add its own project-specific terms
# (vendor names, framework names, internal endpoints, brand terms).
#
# Examples (keep these commented; uncomment when relevant to YOUR project):
# stripe
# postgres
# acme-corp
# datadog
# segment
# braze
```

- [ ] **Step 2: Write `settings.json`**

This file wires the four hooks, declares enabled plugins, and configures the four credential-free MCP servers + the GitHub MCP with placeholder credentials.

```json
{
  "$schema": "https://raw.githubusercontent.com/anthropics/claude-code/main/schemas/settings.json",
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git show:*)",
      "Bash(git branch:*)",
      "Bash(git ls-files:*)",
      "Bash(ls:*)",
      "Bash(cat:*)",
      "Bash(head:*)",
      "Bash(tail:*)",
      "Bash(wc:*)",
      "Bash(find:*)",
      "Bash(grep:*)",
      "Bash(jq:*)",
      "Bash(npm test:*)",
      "Bash(npm run lint:*)",
      "Bash(pytest:*)",
      "Bash(cargo test:*)",
      "Bash(go test:*)",
      "Read(*)",
      "Glob(*)",
      "Grep(*)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/pre-commit-tdd.sh" }
        ]
      },
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/block-cycle-overrun.sh" },
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/block-output-without-signoff.sh" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/enforce-portability.sh" }
        ]
      }
    ]
  },
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "$CLAUDE_PROJECT_DIR"]
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git", "--repository", "$CLAUDE_PROJECT_DIR"]
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  },
  "_pluginsNote": "Claude Code plugins are installed via the /plugin install command and live globally in ~/.claude/plugins/. To enable the recommended plugins for this repo, run after cloning: `/plugin marketplace add anthropics/claude-plugins-official` then `/plugin install obra/superpowers` and `/plugin install affaan-m/everything-claude-code`. See .claude/MCP-SETUP.md for full instructions.",
  "_disablingHooks": "To disable a specific hook for a session, comment out its entry above (JSON does not support comments natively; remove the entry temporarily and restore from git) or set CLAUDE_DISABLE_HOOKS=<hook-name> as an env var if your Claude Code version supports it."
}
```

> **Note for the executor:** Claude Code's `settings.json` schema may have evolved. If `mcpServers` requires a different shape (e.g., a separate `~/.claude/.claude.json`), or if plugin enablement uses a dedicated field rather than the comment workaround above, consult Claude Code docs and update accordingly. The intent — wire 4 hooks, configure 4 MCP servers, set safe permissions — is the contract; field names are the implementation. Document any deviation in the commit message.

- [ ] **Step 3: Validate the JSON**

Run:
```bash
jq empty /Users/gardnerwilson/workspace/workspace-blueprint/.claude/settings.json && echo "VALID JSON"
```
Expected: `VALID JSON`. If it errors, fix the JSON (likely an unescaped char or missing comma).

- [ ] **Step 4: Verify expected fields exist**

Run:
```bash
jq -r 'keys[]' /Users/gardnerwilson/workspace/workspace-blueprint/.claude/settings.json
```
Expected to include (order may vary): `$schema`, `_disablingHooks`, `_pluginsNote`, `hooks`, `mcpServers`, `permissions`.

```bash
jq '.mcpServers | keys' /Users/gardnerwilson/workspace/workspace-blueprint/.claude/settings.json
```
Expected: `["filesystem", "git", "fetch", "github"]` (order may vary).

---

### Task 16: Write `.claude/MCP-SETUP.md`

**Files:**
- Create: `$REPO/.claude/MCP-SETUP.md`

- [ ] **Step 1: Write the setup guide**

```markdown
# MCP & Plugin Setup

This document covers post-clone setup for the agent infrastructure: installing the recommended Claude Code plugins, providing credentials for the GitHub MCP, and verifying everything works.

The four hooks in `.claude/hooks/` and the credential-free MCP servers (`filesystem`, `git`, `fetch`) work out of the box once the repo is cloned. The GitHub MCP and the two recommended plugins require setup.

---

## 1. Plugin installation

This repo benefits from two community plugins, declared in `settings.json` under `_pluginsNote`. Install them after cloning:

```bash
# Add the official Claude Code plugin marketplace (one-time)
/plugin marketplace add anthropics/claude-plugins-official

# Install the recommended plugins
/plugin install obra/superpowers
/plugin install affaan-m/everything-claude-code
```

**`obra/superpowers`** — by Jesse Vincent. Provides ~20 battle-tested skills (TDD workflows, debugging patterns, brainstorming, plan-writing, plan-execution). The skills here overlap with this repo's project-specific skills; they coexist (project skills win where they cover the same ground).

**`affaan-m/everything-claude-code`** — Anthropic hackathon winner. Comprehensive Claude Code setup with security scanning, hook patterns, and config conventions. Useful as a reference for further extending `.claude/hooks/`.

To verify installation:
```bash
/plugin list
```
Both should appear.

---

## 2. GitHub MCP credential setup

The `github` MCP server requires a GitHub Personal Access Token (PAT) to authenticate.

### 2.1 Create the token

1. Go to https://github.com/settings/tokens
2. Click **Generate new token (classic)** or **Fine-grained tokens** → **Generate new token**.
3. **Recommended scopes for read-only first use:**
   - `repo` (read access to repos you'll work with) — or use a fine-grained token scoped to specific repos
   - `read:org` (if you need org info)
   - `read:user` (basic user info)
4. **Do NOT grant write scopes (`workflow`, `delete_repo`, etc.) until you've used the read-only setup for at least one full work session and are comfortable.**
5. Copy the token immediately — GitHub will not show it again.

### 2.2 Make the token available

Set the env var in your shell profile so Claude Code can read it:

```bash
# In ~/.zshrc or ~/.bash_profile (whichever you use)
export GITHUB_TOKEN="ghp_..."
```

Reload your shell or source the file. Verify:
```bash
echo "${GITHUB_TOKEN:0:7}..."
```
Expected: a prefix like `ghp_xxxx...` (do not echo the full token).

### 2.3 Restart Claude Code so it picks up the env var

Quit and relaunch your Claude Code session in a shell where `GITHUB_TOKEN` is set.

### 2.4 Enabling write scopes later

When you're ready to give the agent write access (e.g., to open PRs, comment on issues), edit your token's scopes on GitHub (or generate a new one with broader scope) and update `GITHUB_TOKEN` in your shell profile. No `settings.json` change needed.

---

## 3. Verifying MCP servers

After Claude Code is running with the env var set, ask it to list MCP servers:

```
> What MCP servers do you have available?
```

Or run from the CLI:
```bash
claude mcp list
```

Expected output includes `filesystem`, `git`, `fetch`, `github`. If `github` is missing or shows an auth error, recheck `GITHUB_TOKEN`.

---

## 4. Verifying skills

Ask Claude Code:
```
> What skills do you have available in this project?
```

Expected output includes the ten project skills (`tdd-loop`, `bug-investigation`, `refactor-protocol`, `spike-protocol`, `spec-authoring`, `data-analysis`, plus the four office skills `docx`, `pptx`, `xlsx`, `pdf`).

---

## 5. Verifying hooks

The hooks fire on tool use; you can confirm they're wired by triggering them. Easiest test:

```bash
# Should fail with the pre-commit-tdd hook message:
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m foo"}}' \
  | $CLAUDE_PROJECT_DIR/.claude/hooks/pre-commit-tdd.sh
```

If you see the hook message on stderr (or the script exits non-zero), it's wired and runnable. The actual hook firing happens automatically when you invoke `git commit` via Claude Code.

To check the hook config that Claude Code is using:
```bash
jq '.hooks' .claude/settings.json
```

---

## 6. Adding more MCP servers

The four configured MCP servers (filesystem, git, fetch, github) are the recommended baseline. For more:

- **Browse the catalog:** see `.claude/reference/mcp-servers.md` for curated lists (Stripe, Slack, Notion, Postgres, Puppeteer, etc.)
- **Add a new server:** edit `.claude/settings.json` → `mcpServers` and append a new entry. Restart Claude Code.
- **Credential security:** never put raw secrets in `settings.json` (it's version-controlled). Use `${ENV_VAR}` references and document the env var here.

---

## 7. Disabling hooks

To temporarily disable a hook (e.g., during a refactor where the TDD hook is blocking legitimate work):

1. Open `.claude/settings.json`.
2. Remove the entry from the `hooks` field for the hook you want to skip.
3. Save. Claude Code re-reads settings on the next tool call.
4. **Re-enable** as soon as the temporary work is done. Disable in a branch, restore on merge.

If you find yourself disabling a hook repeatedly for the same reason, that's a signal the hook needs scoping (file extensions, paths) — file an issue rather than working around it.
```

- [ ] **Step 2: Verify**

Run:
```bash
wc -l /Users/gardnerwilson/workspace/workspace-blueprint/.claude/MCP-SETUP.md
```
Expected: roughly 130–160 lines.

---

### Task 17: Populate `.claude/reference/` files

**Files:**
- Create (placeholder): `$REPO/.claude/reference/project-architecture.md`
- Create (placeholder): `$REPO/.claude/reference/tech-stack.md`
- Create (placeholder): `$REPO/.claude/reference/glossary.md`
- Create (placeholder): `$REPO/.claude/reference/frontend-stack.md`
- Create (portable): `$REPO/.claude/reference/iteration-pattern.md`
- Create (portable): `$REPO/.claude/reference/claude-platform-capabilities.md`
- Create (portable): `$REPO/.claude/reference/mcp-servers.md`
- Create (portable): `$REPO/.claude/reference/external-resources.md`

(`skills-system.md` is already in place from Task 12.)

- [ ] **Step 1: Write `project-architecture.md` (placeholder)**

```markdown
# Project Architecture

<!-- REPLACE: This file is loaded on demand by the planner and reviewer agents
when they need to understand how the project is structured. Replace this
content with a description of YOUR project's architecture.

Suggested sections:
- High-level diagram (ASCII or Mermaid)
- Major components and their responsibilities
- Data flow / request flow
- External dependencies (databases, queues, third-party APIs)
- Deployment topology
- Where to find what (folder map within src/ and shared/)
-->

## Overview

<!-- REPLACE: 2-3 sentences. What does this project do, at the highest level? -->

## Components

<!-- REPLACE: list the major modules / services / packages. One paragraph each. -->

## Data flow

<!-- REPLACE: how does a request / event traverse the system? -->

## External dependencies

<!-- REPLACE: databases, message brokers, external APIs, third-party services. -->

## Folder layout

<!-- REPLACE: a tree view of src/ and shared/ with a one-liner per major directory. -->
```

- [ ] **Step 2: Write `tech-stack.md` (placeholder)**

```markdown
# Tech Stack

<!-- REPLACE: This file lists the languages, frameworks, libraries, and
project-specific commands that .claude/skills/ and agents reference.
Without this filled in, the implementer agent will guess at conventions.
-->

## Languages

<!-- REPLACE: e.g., Python 3.12, TypeScript 5.x, Rust stable -->

## Frameworks

<!-- REPLACE: e.g., FastAPI, Next.js 14 (app router), Tokio -->

## Test framework

<!-- REPLACE: e.g., pytest with pytest-asyncio; jest; cargo test -->

**Test command:** <!-- REPLACE: e.g., `pytest` or `npm test` or `cargo test` -->
**Test naming convention:** <!-- REPLACE: e.g., `test_*.py`, `*.test.ts`, `*_test.rs` -->
**Coverage tool + floor:** <!-- REPLACE: e.g., `coverage` with 80% on changed files -->

## Linter / formatter

**Lint command:** <!-- REPLACE: e.g., `ruff check .` or `npm run lint` -->
**Format command:** <!-- REPLACE: e.g., `ruff format .` or `npm run format` -->

## Type checker (if applicable)

**Type-check command:** <!-- REPLACE: e.g., `mypy` or `tsc --noEmit` -->

## Package management

**Add a dependency:** <!-- REPLACE: e.g., `uv add <pkg>` or `npm install <pkg>` -->
**Lockfile:** <!-- REPLACE: e.g., `uv.lock`, `package-lock.json` -->

## Build / run

**Local dev:** <!-- REPLACE: e.g., `uv run python -m app` or `npm run dev` -->
**Production build:** <!-- REPLACE: e.g., `docker build .` or `npm run build` -->

## CI

<!-- REPLACE: where CI lives (GitHub Actions, etc.) and what jobs run -->
```

- [ ] **Step 3: Write `glossary.md` (placeholder)**

```markdown
# Glossary

<!-- REPLACE: domain-specific terms that agents need to understand.
Without this, the planner and implementer will use generic synonyms
that don't match your codebase's vocabulary.

Format: term — definition. Sort alphabetically.
-->

<!-- REPLACE example:
- **Adjudication** — the process by which a claim is approved or denied. In our codebase, this is the `Adjudicator` service in `src/adjudicator/`.
- **Cohort** — a group of users selected for a feature flag rollout, defined in `src/cohort/`.
-->
```

- [ ] **Step 4: Write `frontend-stack.md` (placeholder, with sourced defaults)**

```markdown
# Frontend Stack

<!-- REPLACE if your project does NOT have a frontend, OR if your stack differs.
The defaults below are sourced from Clief Resource Index §2.5 (Frontend, UI, and Design)
and represent the libraries Claude knows best out of the box. -->

## Component library

**Default:** [shadcn/ui](https://github.com/shadcn-ui/ui) — copy-paste React components on Radix UI + Tailwind. Claude generates these natively.

## Styling

**Default:** [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) — utility-first. Claude generates Tailwind classes natively.

## Icons

**Default:** [Lucide](https://github.com/lucide-icons/lucide) (`lucide-react`). Default icon set in Claude artifacts.

## Charts / data viz

**Default:** [Recharts](https://github.com/recharts/recharts). Default React charts library Claude uses.

## Animated / marketing components (optional)

- [Acternity UI](https://ui.acternity.com)
- [Magic UI](https://magicui.design)

## Bootstrap a new component

When building a new UI component:
1. Use shadcn/ui patterns where possible (check if one already exists for the use case).
2. Tailwind for styling.
3. Lucide for icons.
4. Recharts for any charts.
5. If pixel-perfect mockups are needed, generate with [v0.dev](https://v0.dev) and iterate.

## NOT defaults (consumer overrides)

<!-- REPLACE: list anything you've chosen DIFFERENTLY from the above.
Examples: Mantine instead of shadcn, Chakra instead of Tailwind, Heroicons instead of Lucide. -->
```

- [ ] **Step 5: Write `iteration-pattern.md` (portable)**

```markdown
# Iteration Pattern

This file documents the canonical shape of a numbered iteration in this repo. Two iteration types exist: `lab/` (exploratory) and `build/workflows/` (production). They share a numbering convention and an outcome-orientation; their internal structure differs.

## Numbering

- Format: `NN-<slug>/` where `NN` is zero-padded (`01`, `02`, … `99`, `100`+).
- `00-template/` is reserved for the iteration template itself; copy from there to start a new iteration.
- The slug is `kebab-case`, descriptive in 2–5 words: `01-graphql-eval`, `07-fix-login-loop`.
- Iterations are append-only: `02` doesn't replace `01`, even if it supersedes it. Both stay in the tree as historical record.

## `lab/NN-<slug>/` — exploratory iteration

Files (copy from `lab/00-template/`):

| File | Purpose | Written when |
|---|---|---|
| `PREFLIGHT.md` | Hypothesis + prior art + success/failure criteria + time box | BEFORE any prototype code |
| `prototype/` | Throwaway code | DURING the spike |
| `VERIFY.md` | Tests performed, findings, surprises, limitations | AFTER prototype runs |
| `REPORT.md` | Decision: pursue, modify, abandon | AFTER VERIFY |

Outcomes:
- **Pursue** → write a `spec/` artifact, then start `build/workflows/NN-<slug>/`.
- **Modify** → next lab iteration with revised hypothesis.
- **Abandon** → write `docs/explorations/NN-<slug>.md` to preserve the learning.

## `build/workflows/NN-<slug>/` — production iteration

Stages (copy from `build/workflows/00-template/`):

| Stage | Folder | Owner | Output file pattern |
|---|---|---|---|
| 01 — Spec | `01-spec/` | planner agent (one-shot) | `SPEC.md` |
| 02 — Implement | `02-implement/` | implementer agent (cycle) | `notes-<cycle>.md` (code goes to `src/`) |
| 03 — Validate | `03-validate/` | reviewer + adversary agents (parallel each cycle) | `review-<cycle>.md`, `adversary-<cycle>.md` |
| 04 — Output | `04-output/` | orchestrator (after sign-off) | `OUTPUT.md` |

Cycle cap: 5 (enforced by `block-cycle-overrun.sh`). After 5 failed cycles, escalate.
Sign-off: latest `review-N.md` verdict=pass AND latest `adversary-N.md` findings in {none, minor (deferred)}. Enforced by `block-output-without-signoff.sh`.

## Cross-iteration handoff

```
spec/<artifact>            ─┐
                            ├─▶ build/workflows/NN-<slug>/   (production)
lab/NN-<slug>/REPORT.md ────┘     │
   (Pursue outcome)              ├─▶ src/  (the code)
                                  ├─▶ ship/  (release artifacts)
                                  └─▶ docs/explorations/NN-<slug>.md  (post-mortem)

lab/NN-<slug>/REPORT.md  ──▶ docs/explorations/NN-<slug>.md  (Abandon outcome)
```

## What goes where (decision tree)

- **Question I want to answer** → `lab/`
- **Decision I want to record** → `spec/adrs/`
- **Proposal I want to discuss** → `spec/rfcs/`
- **Small task to assign** → `spec/briefs/`
- **Production code change** → `build/workflows/` (sourced from one of the above)
- **Release artifacts** → `ship/`
- **Reusable infrastructure** → `shared/`
- **The actual production code** → `src/`
```

- [ ] **Step 6: Write `claude-platform-capabilities.md` (portable, from Clief §1, §5)**

```markdown
# Claude Platform Capabilities

This file summarizes Claude's capabilities outside Claude Code (Projects, Memory, etc.), and the cross-platform decision sequence. Sourced from the Clief Notes Skills Field Manual (`docs/teaching/clief-notes/skills_field_manual.pdf`, §1, §5, §4.1).

This repo is Claude Code-first; this file exists so the agent (and you) know what other Claude surfaces exist and when they're appropriate.

## Projects (Claude.ai)

A persistent workspace inside Claude.ai with its own knowledge base (≤200K tokens), custom instructions, and chat history. Use Projects when:

- Returning to the same body of work across many conversations
- A team needs shared AI workspace access
- You're re-uploading the same documents repeatedly

Skip when: one-off questions, quick brainstorming, knowledge base would exceed 200K tokens.

**For this repo:** Claude Code's `.claude/` infrastructure plays the same role at the project level. If you also use Claude.ai for non-Code work (docs, brainstorming, slide decks), a Project there can hold cross-conversation context.

## Memory (Claude.ai)

Cross-conversation personalization. Memory is account-scoped, applies outside Projects. Use Memory for: stable preferences (writing style, technical level). Skip when: working inside a Project (Project context overrides), need precise structured context, want incognito mode.

**For Claude Code:** the equivalent is `~/.claude/projects/<repo-path>/memory/` — a file-based memory system Claude Code maintains. Different mechanism, same goal.

## The decision sequence (Clief §4.1)

When starting any task on any Claude surface, run through these in order:

1. **Need persistent context?** → use a Project (Claude.ai) or rely on `CLAUDE.md` + `.claude/` (Claude Code).
2. **Need external data?** → enable MCP connectors / upload files. No → proceed.
3. **Repeatable process?** → build or use a skill. No → prompt directly.
4. **Output format?**
   - File → file creation skill (`.claude/skills/{docx,pptx,xlsx,pdf}/`)
   - Interactive → artifact (Claude.ai)
   - Data → code execution (Claude.ai sandbox or local)
   - Text → just talk
5. **Need deep reasoning?** → extended thinking. No → standard response.

This is the routing logic embedded in this repo's top-level `CONTEXT.md`.
```

- [ ] **Step 7: Write `mcp-servers.md` (portable, catalog from Clief §2.3)**

```markdown
# MCP Server Catalog

The four MCP servers configured in `.claude/settings.json` (`filesystem`, `git`, `fetch`, `github`) are the baseline. This file catalogs additional MCP servers available from the community and how to find more. Sourced from the Clief Resource Index (`docs/teaching/clief-notes/resource_index.pdf`, §4).

## How to add a server

1. Find the server (browse the directories below).
2. Read the source. **MCP servers can execute code on your machine.** Only install from repos you trust.
3. Add an entry to `.claude/settings.json` → `mcpServers`. Use `${ENV_VAR}` placeholders for credentials.
4. Document the env var setup in `.claude/MCP-SETUP.md`.
5. Restart Claude Code.

## Reference / first-party

| Server | Source | Purpose |
|---|---|---|
| Reference servers | github.com/modelcontextprotocol/servers | Filesystem, GitHub, Google Drive, Slack, Postgres, Puppeteer, etc. The canonical examples. |
| GitHub MCP (official) | github.com/github/github-mcp-server | Already configured in this repo (`github` server). Repo management, issue/PR automation, CI/CD intelligence, code analysis, Dependabot. |
| Stripe Agent Toolkit | github.com/stripe/agent-toolkit | Payments: products, customers, payment links, invoices, subscriptions. By Stripe. |

## Curated lists (for discovery)

| List | URL | Editorial style |
|---|---|---|
| `punkpeye/awesome-mcp-servers` | github.com/punkpeye/awesome-mcp-servers | Largest curated list, categorized with icons. Web directory included. |
| `wong2/awesome-mcp-servers` | github.com/wong2/awesome-mcp-servers | Broader categories; cross-reference with punkpeye. |
| `tolkonepiu/best-of-mcp-servers` | github.com/tolkonepiu/best-of-mcp-servers | 410+ servers ranked by quality score (stars, contributors, commit frequency). Updated weekly. |

**Recommended search order:** `tolkonepiu/best-of-mcp-servers` first (quality signal), then the awesome lists (coverage).

## Spec / protocol

[modelcontextprotocol.io](https://modelcontextprotocol.io) — official MCP spec, example servers and clients, guidance on building custom servers.

## Building a custom MCP server

If no existing server fits and you want Claude to interact with an internal tool:

- Reference: github.com/modelcontextprotocol/servers (study a similar one)
- SDKs: official Python and TypeScript SDKs at modelcontextprotocol.io
- Pattern: wrap your internal API in MCP's tool/resource/prompt vocabulary; expose the minimum surface area you need.
- Test locally before adding to `settings.json`.
```

- [ ] **Step 8: Write `external-resources.md` (portable, from Clief §2.1, §2.2, §2.6)**

```markdown
# External Resources

Curated resources for working with Claude (Code, API, plugins). Sourced from the Clief Resource Index (`docs/teaching/clief-notes/resource_index.pdf`).

## Official Anthropic

| Resource | URL | What it's for |
|---|---|---|
| Anthropic Skills repo | github.com/anthropics/skills | Production skills (docx, pptx, xlsx, pdf), examples for creative/enterprise/dev workflows. The 4 office skills in this repo's `.claude/skills/` come from here. |
| Claude Code | github.com/anthropics/claude-code | The CLI agent. Plugin system, subagent architecture, example plugins. |
| Official plugin marketplace | github.com/anthropics/claude-plugins-official | Browse via `/plugin marketplace`. |
| Knowledge work plugins | github.com/anthropics/knowledge-work-plugins | Open-source plugins for Claude Cowork (desktop automation). |
| Anthropic Cookbook | github.com/anthropics/anthropic-cookbook | Jupyter notebooks for the API: tool use, structured output, prompt caching, RAG, embeddings. |
| Courses | github.com/anthropics/courses | Official educational content: prompt engineering, tool use, RAG. |
| Quickstarts | github.com/anthropics/anthropic-quickstarts | Deployable starter apps using the Claude API (customer support agent, financial analyst, computer use demo). |

## Community skill collections

| Resource | URL | Use case |
|---|---|---|
| `obra/superpowers` | github.com/obra/superpowers | **Already enabled in this repo** (see `MCP-SETUP.md`). 20+ skills: TDD, debugging, brainstorming, planning. By Jesse Vincent. |
| `affaan-m/everything-claude-code` | github.com/affaan-m/everything-claude-code | **Already enabled in this repo.** Production setup, hook patterns, security scanning. Hackathon winner. |
| `travisvn/awesome-claude-skills` | github.com/travisvn/awesome-claude-skills | Comprehensive community list, categorized. |
| SkillsMP | https://skillsmp.com | Web directory of 400K+ agent skills, searchable. |
| AgentSkills.io | https://agentskills.io | Open spec for cross-platform agent skills. |

## Documentation

| Resource | URL | What it's for |
|---|---|---|
| Anthropic docs (Claude.ai) | https://docs.claude.com | Claude.ai features, API reference, prompt engineering. |
| Anthropic docs (Claude Code) | https://code.claude.com/docs | Claude Code-specific: skills, hooks, MCP, plugins, settings. |
| Skills Explained (blog) | https://claude.com/blog/skills-explained | Definitive post on Skills vs Projects vs Prompts vs MCP vs Subagents. Read first when confused. |

## When to use what

- **Want a working API example?** → Anthropic Cookbook
- **Want a deployable starter?** → Anthropic Quickstarts
- **Want a Claude Code workflow?** → obra/superpowers
- **Want to learn fundamentals?** → Anthropic Courses
- **Confused about which Claude feature to use?** → Skills Explained blog post
```

- [ ] **Step 9: Verify all 8 reference files exist (plus skills-system.md from Task 12)**

Run:
```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/.claude/reference/ | sort
```
Expected:
```
claude-platform-capabilities.md
external-resources.md
frontend-stack.md
glossary.md
iteration-pattern.md
mcp-servers.md
project-architecture.md
skills-system.md
tech-stack.md
```

---

### Task 18: Write the four workspace `CONTEXT.md` files

**Files:**
- Create: `$REPO/spec/CONTEXT.md`
- Create: `$REPO/lab/CONTEXT.md`
- Create: `$REPO/build/CONTEXT.md`
- Create: `$REPO/ship/CONTEXT.md`

Each follows the standard 6-section anatomy: What this is / What to load / Folder structure / Process / Skills & tools / What NOT to do. Target 25–80 lines each.

- [ ] **Step 1: Write `spec/CONTEXT.md`**

```markdown
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
```

- [ ] **Step 2: Write `lab/CONTEXT.md`**

```markdown
# Lab

## What This Workspace Is

Numbered exploratory iterations. The output of work here is a *learning*, not shipped code. Spikes, library evaluations, performance investigations, "is X feasible?" questions all live here as `NN-<slug>/` folders.

---

## What to Load

| Task | Load These | Skip These |
|------|-----------|------------|
| Start a new spike | `00-template/`, `../.claude/skills/spike-protocol/SKILL.md` | other workspaces' CONTEXT.md |
| Continue an in-flight spike | the iteration's `PREFLIGHT.md` and `prototype/` files | other iteration folders |
| Promote a spike outcome | the iteration's `REPORT.md`, `../spec/CONTEXT.md` (for the destination format) | `prototype/` (it's done) |
| Run a data-heavy analysis spike | `../.claude/skills/spike-protocol/SKILL.md`, `../.claude/skills/data-analysis/SKILL.md` | code-execution-irrelevant skills |

---

## Folder Structure

```
lab/
├─ CONTEXT.md       ← you are here
├─ 00-template/     ← copy this to start a new iteration
│  ├─ PREFLIGHT.md
│  ├─ prototype/
│  ├─ VERIFY.md
│  └─ REPORT.md
└─ NN-<slug>/       ← e.g., 01-graphql-eval/
```

---

## The Process

1. Copy `00-template/` to `NN-<slug>/` (next sequential number).
2. Fill in `PREFLIGHT.md` BEFORE writing prototype code. Define success and failure criteria up front.
3. Build the prototype in `prototype/`. Throwaway code; no production patterns required.
4. Fill in `VERIFY.md` with what was actually tested.
5. Fill in `REPORT.md` with the outcome (Pursue / Modify / Abandon).
6. Honor the time box from PREFLIGHT. Spikes that overrun their box become explicit decisions, not pushed-through work.

Outcomes:
- **Pursue** → write a `spec/` artifact, then start `build/workflows/NN-<slug>/`.
- **Modify** → next lab iteration with revised hypothesis.
- **Abandon** → write `docs/explorations/NN-<slug>.md` to preserve the learning.

---

## Skills & Tools

| Skill / Tool | When | Purpose |
|-------------|------|---------|
| `/spike-protocol` | Driving any iteration here | PREFLIGHT → prototype → VERIFY → REPORT shape |
| `/data-analysis` | Spikes that involve computing something from data | Trigger phrasing for code execution |
| Web Search MCP | PREFLIGHT phase | Prior art and current state of the question |
| Context7 MCP | PREFLIGHT phase | Up-to-date docs for libraries being evaluated |

---

## What NOT to Do

- Don't promote prototype code directly to `src/`. Promote the *learning* via `spec/` → `build/`.
- Don't skip PREFLIGHT. A spike without success/failure criteria has no defined outcome.
- Don't run unboxed. If your time box is exceeded, write the REPORT with what you have and decide explicitly whether the spike continues with a new (longer) box.
- Don't load `build/` or `ship/` here — those are downstream workspaces.
```

- [ ] **Step 3: Write `build/CONTEXT.md`**

```markdown
# Build

## What This Workspace Is

The production pipeline. **All production code work flows through here** — features, bug fixes, refactors. Each unit of work is a numbered iteration in `workflows/NN-<slug>/` with the four-stage shape (spec → implement → validate → output) and the four-agent loop (planner → implementer ↔ reviewer ↔ adversary).

---

## What to Load

| Task | Load These | Skip These |
|------|-----------|------------|
| Plan a new iteration | the source artifact from `../spec/`, `../.claude/agents/planner-agent.md`, `../.claude/reference/project-architecture.md`, `../.claude/reference/tech-stack.md` | implementer/reviewer/adversary agent files (planner doesn't need them) |
| Implement a cycle | the iteration's `01-spec/SPEC.md`, latest `03-validate/review-N.md` and `adversary-N.md` if any, `../.claude/skills/tdd-loop/SKILL.md`, `../.claude/rules/` (all 5) | other workspaces' CONTEXT.md |
| Review a cycle | `01-spec/SPEC.md`, the diff, `../.claude/rules/` (all 5), `../.claude/agents/reviewer-agent.md` | the implementer's notes (read those LAST, not first) |
| Adversary a cycle | `01-spec/SPEC.md` (especially Risks), the diff, `../.claude/agents/adversary-agent.md` | the reviewer's findings (you run in parallel, not series) |
| Promote to output | latest `review-N.md` + `adversary-N.md` (must be pass + clean), `01-spec/SPEC.md` | implement-cycle artifacts |

---

## Folder Structure

```
build/
├─ CONTEXT.md
└─ workflows/
   ├─ CONTEXT.md          ← pipeline routing
   ├─ 00-template/        ← copy this to start an iteration
   └─ NN-<slug>/
      ├─ 01-spec/SPEC.md           ← planner output
      ├─ 02-implement/notes-N.md   ← implementer process notes (CODE goes to src/)
      ├─ 03-validate/
      │  ├─ review-N.md           ← reviewer per cycle
      │  └─ adversary-N.md        ← adversary per cycle
      └─ 04-output/OUTPUT.md       ← signed-off deliverable
```

See `workflows/CONTEXT.md` for stage-by-stage routing.

---

## The Process

The four-agent loop is documented in `../docs/orchestrator-process.md`. In brief:

1. **Plan once:** orchestrator dispatches planner agent → SPEC.md.
2. **Loop until acceptance** (max 5 cycles, hook-enforced):
   - Implementer agent writes code to `src/` and notes to `02-implement/`.
   - Reviewer agent reads diff + SPEC.md, writes verdict to `03-validate/review-N.md`.
   - Adversary agent reads diff + SPEC.md (in parallel with reviewer), writes findings to `03-validate/adversary-N.md`.
   - If verdict=pass AND findings∈{none,minor}: promote to `04-output/`. Otherwise: next cycle.

The hooks (`block-cycle-overrun.sh`, `block-output-without-signoff.sh`) enforce both the cycle cap and the sign-off gate.

---

## Skills & Tools

| Skill / Tool | When | Purpose |
|-------------|------|---------|
| `/tdd-loop` | Implementer agent, every cycle | Mandatory test-first discipline |
| `/bug-investigation` | When the iteration is a bug fix (drives the SPEC shape) | Reproduce → diagnose → fix → regression test |
| `/refactor-protocol` | When the iteration is a refactor (drives the SPEC shape) | Behavior-equivalence proof + staged migration |
| Context7 MCP | Spec + implement | Up-to-date library docs |
| `github` MCP | Output stage | Open PRs, link issues, post updates |

---

## What NOT to Do

- Don't write code in `02-implement/` — that's process notes only. Code goes to `src/`.
- Don't skip the reviewer or adversary. They're hook-enforced gates, not optional quality checks.
- Don't keep cycling past 5. After 5 failed cycles, the spec is wrong; escalate.
- Don't bundle multiple iterations into one folder. One folder = one SPEC.md = one logical change.
- Don't load `lab/` or `ship/` here — those are different lifecycle stages.
```

- [ ] **Step 4: Write `ship/CONTEXT.md`**

```markdown
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
```

- [ ] **Step 5: Verify line counts (target 25–80 lines for the body)**

Run:
```bash
wc -l /Users/gardnerwilson/workspace/workspace-blueprint/{spec,lab,build,ship}/CONTEXT.md
```
Expected: each file 60–110 lines (the standard sections are dense).

---

### Task 19: Write `build/workflows/CONTEXT.md` (pipeline router)

**Files:**
- Create: `$REPO/build/workflows/CONTEXT.md`

- [ ] **Step 1: Write the file**

```markdown
# Workflows — The Build Pipeline

## What This Folder Is

The four-stage gated pipeline. Each iteration is `NN-<slug>/` with stages 01 → 02 → 03 → 04. The four-agent loop (planner → implementer ↔ reviewer ↔ adversary) runs over these stages.

```
01-spec/  →  02-implement/  →  03-validate/  →  04-output/
 (plan)        (build)            (review)        (done)
```

---

## Stage Routing

| Your Task | Input | Also Load | Output | Agent |
|-----------|-------|-----------|--------|-------|
| Plan iteration | Source artifact from `../../spec/` | `../.claude/agents/planner-agent.md`, `../.claude/reference/{project-architecture,tech-stack}.md`, `../.claude/rules/` | `01-spec/SPEC.md` | planner (one-shot) |
| Implement cycle | `01-spec/SPEC.md`, latest `03-validate/{review,adversary}-N.md` if any | `../.claude/skills/tdd-loop/SKILL.md`, `../.claude/rules/` (all 5), `../.claude/reference/tech-stack.md` | code in `../../src/`; `02-implement/notes-N.md` | implementer (cycle) |
| Review cycle | `01-spec/SPEC.md`, the diff | `../.claude/agents/reviewer-agent.md`, `../.claude/rules/` | `03-validate/review-N.md` | reviewer (cycle, parallel) |
| Adversary cycle | `01-spec/SPEC.md`, the diff | `../.claude/agents/adversary-agent.md` | `03-validate/adversary-N.md` | adversary (cycle, parallel) |
| Promote to output | latest `review-N.md` (verdict=pass) AND latest `adversary-N.md` (findings ∈ {none, minor}) | `01-spec/SPEC.md` (acceptance evidence) | `04-output/OUTPUT.md` | orchestrator |

---

## Stage Details

### 01-spec/

Planner agent's output. ONE file per iteration: `SPEC.md`. Re-planning produces a new SPEC (versioned in its header), not an in-place edit.

### 02-implement/

Implementer's working notes per cycle: `notes-1.md`, `notes-2.md`, etc. **The actual code lives in `src/` (or `shared/`), NOT here.** This folder is process; that folder is artifact.

### 03-validate/

Per-cycle reviewer + adversary reports: `review-1.md` + `adversary-1.md`, `review-2.md` + `adversary-2.md`, etc. Both run in parallel each cycle (no shared context within a cycle). Hook `block-cycle-overrun.sh` blocks at 5 cycles.

### 04-output/

The signed-off deliverable. Created only after the orchestrator confirms the latest cycle's reviewer and adversary both clear. Hook `block-output-without-signoff.sh` enforces this.

---

## Pipeline Rules

1. **Forward flow.** Stages 01 → 02 → 03 → 04. No skipping.
2. **Each agent loads only what it needs.** See routing table.
3. **Cycle counter increments per `review-N.md`.** Max 5 (hook-enforced).
4. **Code goes to `src/`, not `02-implement/`.** Reviewer flags violations.
5. **Sign-off is binary per cycle.** Pass + clean → 04-output. Anything else → next cycle.
```

### Task 20: Write supporting READMEs (`shared/`, `src/`, `scripts/`)

**Files:**
- Create: `$REPO/shared/README.md`
- Create: `$REPO/src/README.md`
- Create: `$REPO/scripts/README.md`

- [ ] **Step 1: Write `shared/README.md`**

```markdown
# shared/

Reusable infrastructure. Code that prevents bug-classes by construction, not by reminding the implementer to be careful.

## What lives here

- Helpers that multiple parts of `src/` depend on (utility functions, shared types, common protocols)
- Architectural constraints implemented as code (e.g., a `CursorEngine`-style pattern that makes look-ahead bugs impossible, or a typed envelope that makes error-shape inconsistency impossible)
- Test fixtures and harnesses shared across multiple test suites

## What does NOT live here

- Code specific to a single feature or module — that goes in `src/<module>/`
- Throwaway prototype code — that lives in `lab/NN/prototype/`
- Documentation about the architecture — that goes in `.claude/reference/project-architecture.md` (loaded on demand by agents)

## Discipline

When adding to `shared/`, ask: would TWO different parts of `src/` use this? If only one would, it belongs in that module, not here. The 60% layer (per the 60/30/10 framework) earns its place by being reused, not by being centralized.
```

- [ ] **Step 2: Write `src/README.md`**

```markdown
# src/

Long-lived production source code. The output of `build/workflows/NN/02-implement/` cycles lands here.

## Layout

The internal layout depends on the consumer project's tech stack. Document it in `.claude/reference/project-architecture.md` so agents know where to find what.

Common patterns (pick one or adapt):

- **Feature-first** (recommended for most new projects): `src/<feature-name>/{api,domain,infra,tests}/`
- **Layer-first**: `src/{api,domain,infra,tests}/<feature-name>/`
- **Single-package**: everything in `src/`, organized by module name

Whatever the layout, follow these rules:

- Tests live next to the code they test (`foo.py` ↔ `test_foo.py`, `Foo.ts` ↔ `Foo.test.ts`).
- No throwaway code — that goes in `lab/`.
- No code generated mid-implementation that isn't covered by tests — TDD is hook-enforced.

## What does NOT live here

- Process notes (those are in `build/workflows/NN/02-implement/notes-N.md`)
- Reusable infrastructure shared across modules (that's `shared/`)
- Build/deploy scripts (those are `scripts/` or `ship/deploy/`)
- Generated files committed by accident — add to `.gitignore`
```

- [ ] **Step 3: Write `scripts/README.md`**

```markdown
# scripts/

Repo-level utilities. Bash, Python, or whatever fits — these are the things you run, not the things you ship.

## What goes here

- Bootstrapping helpers (e.g., `bootstrap-new-repo.sh` if/when written — see Section 7.2 of the design spec for the manual procedure)
- One-off maintenance scripts
- Repo-level tooling that doesn't belong in `src/` or `shared/`

## What does NOT go here

- Build / lint / test runners — those are package.json/pyproject scripts in the language ecosystem
- Deploy scripts that ship — those go in `ship/deploy/`
- Hook scripts — those go in `.claude/hooks/`

## Conventions

- Scripts are `chmod +x` and start with a shebang (`#!/usr/bin/env bash`, `#!/usr/bin/env python3`, etc.)
- Each script has a header comment explaining purpose, inputs, outputs.
- `set -euo pipefail` for bash scripts.
- Scripts that take arguments document `--help` output.
```

### Task 21: Write `docs/iteration-process.md` and `docs/orchestrator-process.md`

**Files:**
- Create: `$REPO/docs/iteration-process.md`
- Create: `$REPO/docs/orchestrator-process.md`

- [ ] **Step 1: Write `docs/iteration-process.md`**

```markdown
# Iteration Process — End to End

How a unit of work travels from idea to shipped code in this repo.

## The two iteration types

- **Lab iteration** (`lab/NN-<slug>/`) — exploratory, output is a learning, not code.
- **Build iteration** (`build/workflows/NN-<slug>/`) — production, output is shipped code.

Both are numbered, both have a template (`00-template/` in each workspace), both are append-only.

## Lab iteration lifecycle

```
Open question
   │
   ▼
Copy lab/00-template/ → lab/NN-<slug>/
   │
   ▼
Author PREFLIGHT.md  (hypothesis, prior art, success/failure criteria, time box)
   │
   ▼
Build prototype/ within the time box
   │
   ▼
Write VERIFY.md  (what was tested, findings)
   │
   ▼
Write REPORT.md  (decision: Pursue | Modify | Abandon)
   │
   ├── Pursue   → write spec/ artifact → start build/workflows/NN-<slug>/
   ├── Modify   → next lab iteration with revised PREFLIGHT
   └── Abandon  → write docs/explorations/NN-<slug>.md (preserve learning)
```

## Build iteration lifecycle

```
spec/ artifact OR lab/NN/REPORT.md (Pursue)
   │
   ▼
Copy build/workflows/00-template/ → build/workflows/NN-<slug>/
   │
   ▼
Planner agent writes 01-spec/SPEC.md  (one-shot)
   │
   ▼
LOOP (max 5 cycles, hook-enforced):
   ├─ Implementer writes code → src/ + notes-N.md → 02-implement/
   ├─ Reviewer writes review-N.md → 03-validate/  (parallel with adversary)
   ├─ Adversary writes adversary-N.md → 03-validate/  (parallel with reviewer)
   └─ Orchestrator: pass + clean? exit. Otherwise: increment N, loop.
   │
   ▼ (only on pass + clean)
04-output/OUTPUT.md  (signed off, PR-ready)
   │
   ▼
ship/changelog/ entry; ship/docs/ updated; src/ merged
```

## Numbering rules

- `NN` is zero-padded (`01`, `02`, … `99`, `100+`).
- Numbers are repo-wide-unique within each workspace (`lab/01` and `build/workflows/01` are independent).
- `00-template/` is reserved.
- Numbers never reused. If `lab/03` is abandoned, `lab/04` is the next spike (not `lab/03-v2`).

## When to use what

- **Don't know if X is feasible** → `lab/`
- **Need a decision recorded** → `spec/adrs/`
- **Want to propose a change** → `spec/rfcs/`
- **Have a small task to assign** → `spec/briefs/`
- **Building, fixing, or refactoring production code** → `build/workflows/`
- **Cutting a release** → `ship/`
```

- [ ] **Step 2: Write `docs/orchestrator-process.md`**

```markdown
# Orchestrator Process — Running the Build Loop

The orchestrator is the main Claude Code session in your terminal. It dispatches subagents (planner, implementer, reviewer, adversary) and runs the cycle. This document is the protocol — a fresh Claude session can pick it up here.

## When to engage the loop

- A `spec/` artifact is accepted AND a `build/workflows/NN-<slug>/` iteration has been created (with `00-template/` copied).
- For trivial work (one-line fixes, doc typos), the loop is overkill. Use single-agent for those — the loop is for non-trivial production iterations.

## Phase 1: Plan (one-shot)

1. **Identify the source artifact.** One of: `spec/rfcs/<slug>.md` (Accepted), `spec/adrs/<NNNN>-<slug>.md`, `spec/briefs/<slug>.md`, or `lab/NN-<slug>/REPORT.md` (Pursue).
2. **Dispatch the planner** via the `Agent` tool with `subagent_type: planner`. Pass the source artifact path and the iteration directory path.
3. **Verify** that `01-spec/SPEC.md` was created. If not, re-prompt the planner with the missing context. If it exists but is incomplete, treat it like the source-was-insufficient case and ask the human.
4. **Read the SPEC.md** yourself (the orchestrator) to know what's being built.

## Phase 2: Loop (max 5 cycles)

For cycle `N` (starting at 1):

### Step A: Implement

Dispatch the implementer (`subagent_type: implementer`). Pass:
- The iteration directory path
- The cycle number `N`
- The latest `review-(N-1).md` and `adversary-(N-1).md` if `N > 1`

The implementer writes code to `src/` and `02-implement/notes-N.md`, then commits per the commit-discipline rule.

### Step B: Validate (parallel)

Dispatch the reviewer AND adversary in parallel (single message with two `Agent` tool uses). Each receives:
- The iteration directory path
- The cycle number `N`
- The git diff for this cycle (typically `git diff <base-ref>..HEAD`; choose `base-ref` as the commit before this cycle's implementer commits)

Wait for both reports.

### Step C: Decide

Read `03-validate/review-N.md` frontmatter `verdict` and `03-validate/adversary-N.md` frontmatter `findings`.

| review.verdict | adversary.findings | Action |
|---|---|---|
| pass | none | Promote to 04-output |
| pass | minor | Promote to 04-output (defer minors to follow-up issues) |
| pass | critical | Next cycle (implementer addresses critical findings) |
| fail | * | Next cycle (implementer addresses review findings) |

### Step D: Cycle counter

If next cycle: `N += 1`. If `N > 5`, the `block-cycle-overrun.sh` hook will block your next write to `03-validate/`. Stop and escalate to the human:
- Write `04-output/ESCALATION.md` describing the cycles that ran and the unresolved findings.
- Likely action: re-engage the planner with revised inputs and start a NEW iteration directory (`build/workflows/<NN+1>-<slug>-v2/`).

## Phase 3: Output

When the loop exits to 04-output:

1. Dispatch a final pass (this can be the orchestrator itself, no subagent needed) to write `04-output/OUTPUT.md` with summary, commit/PR link, acceptance evidence, cycle count, and follow-ups.
2. Verify the output write was not blocked by `block-output-without-signoff.sh`. If it was, your sign-off detection in Step C was wrong; recheck.
3. Open a PR (manual or via `github` MCP) if the consumer repo's workflow uses PRs.
4. Update `ship/changelog/` if this is a release-worthy change.

## When to collapse the loop

For trivial iterations (one-line fixes, docs-only changes), the four-agent loop is overhead. The orchestrator can:
- Skip the planner if the brief is already SPEC-shaped enough to drop straight into `01-spec/SPEC.md`.
- Combine implementer + reviewer in one session if the diff is genuinely small (one file, < 50 lines).
- Skip the adversary if the change has no behavioral surface area (e.g., a typo fix).

These are exceptions, not defaults. The hooks still enforce the gates — you can't promote to `04-output/` without sign-off files in `03-validate/`. For collapsed cycles, write minimal `review-1.md` and `adversary-1.md` documenting the collapse rationale.

## Multiple iterations in flight

The orchestrator can run multiple iterations sequentially in one session, but NOT in parallel — subagent dispatch is shared session state, and interleaving cycles produces unreviewable history. Finish one iteration's loop before starting another.
```

### Task 22: Run portability hook against new `.claude/` content

**Files:** none modified — verification only.

- [ ] **Step 1: Run the hook against every file in `.claude/rules/` and `.claude/skills/`**

Run:
```bash
fail_count=0
for f in $(find /Users/gardnerwilson/workspace/workspace-blueprint/.claude/rules /Users/gardnerwilson/workspace/workspace-blueprint/.claude/skills -type f -name '*.md'); do
  out=$(echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$f\"}}" \
    | /Users/gardnerwilson/workspace/workspace-blueprint/.claude/hooks/enforce-portability.sh 2>&1)
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "FAIL: $f"
    echo "$out"
    fail_count=$((fail_count + 1))
  fi
done
echo "TOTAL FAILURES: $fail_count"
```

Expected: `TOTAL FAILURES: 0`. The deny list is currently empty (placeholder only), so nothing should fail. If the deny list later gets populated and a rule file violates, this is the check that catches it.

If failures appear (you might have committed real-world examples in skills like office docs that weren't excluded properly), inspect each and either generalize the offending text or add an exception to the hook script's exempt-paths block.

### Task 23: Stage and commit Commit 2

- [ ] **Step 1: Stage every new and modified path under workspace-blueprint/**

```bash
# All the new files and directories created in Tasks 5-22
git add workspace-blueprint/.claude
git add workspace-blueprint/spec workspace-blueprint/lab workspace-blueprint/build workspace-blueprint/ship
git add workspace-blueprint/shared workspace-blueprint/src workspace-blueprint/scripts
git add workspace-blueprint/docs/iteration-process.md workspace-blueprint/docs/orchestrator-process.md
git add workspace-blueprint/docs/explorations
git add workspace-blueprint/docs/teaching/office-skills-source

# Anything moved with `mv` (not `git mv`) needs both the deletion and the addition staged
git add -u workspace-blueprint/claude-office-skills-ref 2>/dev/null || true
```

- [ ] **Step 2: Verify the staged set**

```bash
git status --short | grep workspace-blueprint | head -50
```

Spot-check that:
- Every `.claude/` file is staged (look for many `A` lines under `workspace-blueprint/.claude/`)
- All four workspace `CONTEXT.md` files are staged
- No files outside `workspace-blueprint/` are staged
- The `claude-office-skills-ref/` deletions are staged (D lines)

If anything outside `workspace-blueprint/` is staged, unstage it:
```bash
git reset HEAD <unwanted-path>
```

- [ ] **Step 3: Commit**

```bash
git commit -m "$(cat <<'EOF'
Scaffold spec/lab/build/ship workspaces and .claude/ infrastructure

Creates the agent-native software-dev structure described in
docs/superpowers/specs/2026-05-10-workspace-blueprint-software-redesign-design.md.

Workspaces:
- spec/{rfcs,adrs,briefs} for pre-build artifacts
- lab/00-template + lab/CONTEXT.md for exploratory iterations
- build/workflows/{00-template,01-spec,02-implement,03-validate,04-output}
  + build/CONTEXT.md and build/workflows/CONTEXT.md
- ship/{docs,changelog,deploy} for release artifacts
- shared/, src/, scripts/ with READMEs

.claude/ infrastructure:
- rules/{code-quality,testing-discipline,commit-discipline,review-discipline,
  portability-discipline}.md (5 always-loaded rules, <40KB total)
- skills/ with 6 project-specific (tdd-loop, bug-investigation,
  refactor-protocol, spike-protocol, spec-authoring, data-analysis)
  + 4 vendored from anthropics/skills (docx, pptx, xlsx, pdf)
- agents/{planner,implementer,reviewer,adversary}-agent.md
- reference/ with 4 placeholder files for consumer repos plus 4 portable
  files (iteration-pattern, claude-platform-capabilities, mcp-servers,
  external-resources) plus skills-system.md (moved from office-skills-ref)
- hooks/{pre-commit-tdd,block-cycle-overrun,block-output-without-signoff,
  enforce-portability}.sh (executable, smoke-tested)
- settings.json wires hooks + 4 MCP servers + permissions
- .portability-deny.txt (placeholder list)
- MCP-SETUP.md (plugin install + GitHub PAT setup)

Other:
- docs/iteration-process.md and docs/orchestrator-process.md document the
  end-to-end iteration lifecycle and the four-agent loop protocol
- claude-office-skills-ref/ decomposed into .claude/skills/, .claude/reference/,
  and docs/teaching/office-skills-source/; the empty directory is removed

Portability hook passes against the new .claude/rules/ and .claude/skills/.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: Verify the commit**

```bash
git log --oneline -1
git show --stat HEAD | head -10
```
Expected: a new commit with the message above and ~40+ files changed.

---

## COMMIT 3 — Migration

The final commit replaces the four root-level Acme DevRel docs (`CLAUDE.md`, `CONTEXT.md`, `START-HERE.md`) with software-dev versions, adds a public-facing `README.md`, rewrites the four `_examples/` files into `docs/teaching/`, and runs the full acceptance checklist.

### Task 24: Rewrite root `CLAUDE.md`

**Files:**
- Modify: `$REPO/CLAUDE.md` (full rewrite)

- [ ] **Step 1: Write the new content (full overwrite)**

```markdown
# Workspace Blueprint — Map

> **Always loaded.** This file is THE MAP. It shows every workspace, every key directory, every naming convention. It does NOT contain detailed instructions — those live in workspace `CONTEXT.md` files.

## What This Repo Is

An agent-native scaffold for software development work. Two roles:
1. **An active lab** — numbered iterations live here for ongoing software experiments, features, bug investigations, and refactors.
2. **The canonical scaffolding source** — the directory layout and markdown templates are domain-agnostic enough to copy into other repos. See `.claude/MCP-SETUP.md` and `START-HERE.md` for bootstrap.

The instruction layer (`CLAUDE.md`, `CONTEXT.md`, `.claude/`, all workspace `CONTEXT.md` files) is portable. Project-specific facts live only in `.claude/reference/`.

---

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
   ├─ teaching/          ← how to adapt this scaffold (incl. legacy DevRel example)
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

- **10 skills** in `.claude/skills/` — 6 project-specific (tdd-loop, bug-investigation, refactor-protocol, spike-protocol, spec-authoring, data-analysis) + 4 office (docx, pptx, xlsx, pdf vendored from `anthropics/skills`)
- **2 plugins** enabled: `obra/superpowers` and `affaan-m/everything-claude-code`
- **4 MCP servers** configured: `filesystem`, `git`, `fetch` (credential-free), `github` (placeholder env var)

Setup details: `.claude/MCP-SETUP.md`. Catalogs: `.claude/reference/{mcp-servers,external-resources}.md`.

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
```

### Task 25: Rewrite root `CONTEXT.md`

**Files:**
- Modify: `$REPO/CONTEXT.md` (full rewrite)

- [ ] **Step 1: Write the new content (full overwrite)**

```markdown
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
```

### Task 26: Rewrite `START-HERE.md`

**Files:**
- Modify: `$REPO/START-HERE.md` (full rewrite)

- [ ] **Step 1: Write the new content**

```markdown
# Start Here

A 5-minute orientation to this repo. Skip if you've worked here before.

## What this repo is

An agent-native scaffold for software development. Two roles:

1. **A working lab** — numbered iterations (`lab/01-...`, `build/workflows/01-...`) for spikes, features, bug fixes, and refactors. The repo accumulates these over time.
2. **A canonical scaffold** — the directory layout and markdown templates are domain-agnostic and can be copied into other repos as a starter.

## How the structure works

Three-layer routing keeps token usage tight:

1. **`CLAUDE.md`** is always loaded. It's THE MAP — every directory, every convention.
2. **`CONTEXT.md`** is the router. "What's your task → which workspace + what to load."
3. **Each workspace's `CONTEXT.md`** has the per-task load budget.

Then the agent infrastructure:

- **`.claude/rules/`** — 5 always-loaded constraints (TDD mandatory, conventional commits, portability, etc.)
- **`.claude/skills/`** — 10 procedures (6 project-specific, 4 office-doc generation)
- **`.claude/agents/`** — 4 subagent specs (planner, implementer, reviewer, adversary)
- **`.claude/hooks/`** — 4 bash hooks that enforce rules by construction
- **`.claude/settings.json`** — wires hooks, MCP servers, plugins, permissions

## How work flows

```
Have an open question? → lab/NN-<slug>/  (spike)
Have a decision to record? → spec/adrs/  (ADR)
Have a proposal? → spec/rfcs/  (RFC)
Have a small task? → spec/briefs/  (brief)

When ready to build:
spec/ artifact OR lab/REPORT.md (Pursue)
   → build/workflows/NN-<slug>/  (4 stages, 4 agents)
   → src/  (the code itself)
   → ship/  (release notes, docs, deploy)
```

The four-agent loop in `build/` is documented in `docs/orchestrator-process.md`.

## What to do FIRST after cloning (or forking)

If you're using this repo AS your project (not just as a scaffold):

1. **Run `.claude/MCP-SETUP.md` setup** — install the two recommended plugins, set up the GitHub PAT.
2. **Fill in `.claude/reference/`:**
   - `project-architecture.md` — describe what your project is and how it's organized
   - `tech-stack.md` — languages, frameworks, lint/test/build commands
   - `glossary.md` — domain terms agents need to know
   - `frontend-stack.md` — only if you have a frontend (defaults provided)
3. **Edit `.claude/.portability-deny.txt`** — add project-specific terms (vendor names, internal endpoints) so the portability hook catches drift.
4. **Replace `<!-- REPLACE -->` markers** in `CLAUDE.md`, `CONTEXT.md`, `START-HERE.md`, `README.md`.

If you're using this scaffold to bootstrap a NEW repo:

```bash
# Option A: full clone (lab + scaffolding)
git clone <this-repo> my-new-project
rm -rf my-new-project/.git my-new-project/lab/[1-9]* my-new-project/spec/{rfcs,adrs,briefs}/* my-new-project/build/workflows/[1-9]*
git init my-new-project

# Option B: scaffolding only (recommended)
rsync -av \
  --exclude='lab/[1-9]*' \
  --exclude='build/workflows/[1-9]*' \
  --exclude='spec/rfcs/*' --exclude='spec/adrs/*' --exclude='spec/briefs/*' \
  --exclude='docs/explorations/*' \
  --exclude='docs/superpowers/specs/*' --exclude='docs/superpowers/plans/*' \
  --exclude='.git' \
  workspace-blueprint/ my-new-project/

cd my-new-project
git init
# Then follow the "FIRST after cloning" steps above
```

## Where to learn more

- **Claude Code basics:** `.claude/reference/claude-platform-capabilities.md` (and Clief Notes PDFs in `docs/teaching/clief-notes/`)
- **How to adapt this template:** `docs/teaching/how-to-adapt.md`
- **Anatomy of a CONTEXT.md:** `docs/teaching/context-md-anatomy.md`
- **Skill integration patterns:** `docs/teaching/skill-integration-patterns.md`
- **Common mistakes:** `docs/teaching/common-mistakes.md`
- **Legacy Acme DevRel example** (alternate-domain illustration): `docs/teaching/legacy-devrel-example/`

## Where to find things FAST

- "I want to plan a feature" → `CONTEXT.md` task table → `spec/CONTEXT.md`
- "I want to implement a feature" → `build/CONTEXT.md`
- "I want to investigate something" → `lab/CONTEXT.md`
- "I want to ship a release" → `ship/CONTEXT.md`
- "How does the agent loop work?" → `docs/orchestrator-process.md`
- "How do I configure an MCP?" → `.claude/MCP-SETUP.md`
```

### Task 27: Write `README.md` (public-facing)

**Files:**
- Create: `$REPO/README.md`

- [ ] **Step 1: Write the file**

```markdown
# workspace-blueprint

An agent-native scaffold for software development with [Claude Code](https://github.com/anthropics/claude-code). Designed to serve simultaneously as a **working lab** (numbered iterations accumulate here) and as **portable scaffolding** (copy the structure into other repos).

## What's inside

- **Three-layer routing** (`CLAUDE.md` → `CONTEXT.md` → workspace `CONTEXT.md`) for tight token discipline
- **Four workspaces** mapped to phases of dev work: `spec/` (RFCs, ADRs, briefs), `lab/` (exploratory iterations), `build/` (production pipeline), `ship/` (release artifacts)
- **A four-agent loop** for the build pipeline: planner (one-shot) → implementer ↔ reviewer ↔ adversary (cycle, max 5)
- **`.claude/` infrastructure:**
  - 5 rules (always loaded, &lt;40KB total) enforcing TDD, conventional commits, review gates, portability
  - 10 skills (6 project-specific, 4 vendored from `anthropics/skills`)
  - 4 subagent specs
  - 4 bash hooks enforcing rules by construction (TDD, cycle cap, output sign-off, portability)
  - 4 configured MCP servers (`filesystem`, `git`, `fetch`, `github`)
  - 2 enabled plugins (`obra/superpowers`, `affaan-m/everything-claude-code`)

## Inspiration

Structurally inspired by [adam-s/alphadidactic](https://github.com/adam-s/alphadidactic). Adopts the multi-agent loop, numbered iterations, and `.claude/` instruction set patterns; preserves the existing 3-layer routing pattern from the original Acme DevRel template (which is preserved in `docs/teaching/legacy-devrel-example/` for reference).

The 60/30/10 mental model and the §4.1 decision sequence in `CONTEXT.md` come from the [Clief Notes Skills Field Manual](docs/teaching/clief-notes/skills_field_manual.pdf).

## Getting started

See [`START-HERE.md`](START-HERE.md).

## Setup after cloning

See [`.claude/MCP-SETUP.md`](.claude/MCP-SETUP.md) for plugin installation and the GitHub MCP token setup.

## Bootstrapping a new repo from this scaffold

See the "If you're using this scaffold to bootstrap a NEW repo" section in [`START-HERE.md`](START-HERE.md).

## Project status

This scaffold is itself the first iteration. Use it, evolve it, file issues for friction.
```

### Task 28: Rewrite the four `_examples/` files into `docs/teaching/`

**Files:**
- Move + rewrite: `$REPO/_examples/01-how-to-adapt-this.md` → `$REPO/docs/teaching/how-to-adapt.md`
- Move + rewrite: `$REPO/_examples/02-skill-integration-patterns.md` → `$REPO/docs/teaching/skill-integration-patterns.md`
- Move + rewrite: `$REPO/_examples/03-context-md-anatomy.md` → `$REPO/docs/teaching/context-md-anatomy.md`
- Move + rewrite: `$REPO/_examples/04-common-mistakes.md` → `$REPO/docs/teaching/common-mistakes.md`
- Delete: `$REPO/_examples/` (after move)

The original files are DevRel-themed; rewrite to use software-dev examples. Move the files first (preserving content), then rewrite each.

- [ ] **Step 1: Move the files (use `mv`; they were never tracked in this branch)**

Run:
```bash
mv /Users/gardnerwilson/workspace/workspace-blueprint/_examples/01-how-to-adapt-this.md /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/how-to-adapt.md
mv /Users/gardnerwilson/workspace/workspace-blueprint/_examples/02-skill-integration-patterns.md /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/skill-integration-patterns.md
mv /Users/gardnerwilson/workspace/workspace-blueprint/_examples/03-context-md-anatomy.md /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/context-md-anatomy.md
mv /Users/gardnerwilson/workspace/workspace-blueprint/_examples/04-common-mistakes.md /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/common-mistakes.md
rmdir /Users/gardnerwilson/workspace/workspace-blueprint/_examples
```

- [ ] **Step 2: Rewrite `how-to-adapt.md` for software-dev examples**

Open `/Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/how-to-adapt.md` and replace its contents with:

```markdown
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
- **Need stricter rules?** Add to `.claude/rules/` (mind the &lt;40KB budget).

The scaffold is a starting point. Don't preserve patterns that don't fit your work.
```

- [ ] **Step 3: Rewrite `skill-integration-patterns.md` for software-dev examples**

Open `/Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/skill-integration-patterns.md` and replace its contents with:

```markdown
# Skill Integration Patterns

Skills aren't just `.md` files. The CONTEXT routing tells the agent WHEN to invoke a skill. Below are the four patterns this scaffold uses, with examples from the current setup.

## 1. The pipeline gate

A skill that MUST run at a specific stage transition.

```markdown
<!-- In .claude/rules/testing-discipline.md -->
TDD is mandatory. The implementer agent invokes .claude/skills/tdd-loop/SKILL.md every cycle.
The pre-commit-tdd.sh hook enforces this by blocking commits without test files.
```

The combination of rule + skill + hook is the gate: the rule states the discipline, the skill encodes the procedure, the hook enforces by construction.

## 2. The stage specialist

A skill that activates only at one specific stage.

```markdown
<!-- In build/workflows/CONTEXT.md routing table -->
| Plan iteration   | Source artifact, .claude/agents/planner-agent.md          |
| Implement cycle  | SPEC.md, .claude/skills/tdd-loop/SKILL.md                 |
| Review cycle     | SPEC.md, .claude/agents/reviewer-agent.md                 |
```

The implementer cycle never loads the planner agent. The reviewer never sees the implementer's reasoning. Skills + agents are contextual, not global.

## 3. The format trigger

A skill that activates based on the OUTPUT FORMAT.

```markdown
<!-- In ship/CONTEXT.md -->
| /docx | Word deliverables   | From anthropics/skills |
| /pdf  | PDF deliverables    | From anthropics/skills |
| /pptx | Slide decks         | From anthropics/skills |
| /xlsx | Spreadsheets        | From anthropics/skills |
```

The `ship/` workspace has no pipeline; the OUTPUT FORMAT determines which skill loads.

## 4. The cross-workspace skill

A skill referenced from multiple workspaces with different triggers.

```markdown
<!-- The data-analysis skill -->
- In lab/CONTEXT.md: triggered when running data-heavy spikes
- In .claude/skills/spike-protocol/: cross-referenced as "use this when computing"
```

Same skill, different trigger conditions per workspace.

## When to add a skill

- You repeat the same multi-step procedure across iterations → make it a skill.
- Agents make the same mistake repeatedly → add a skill that documents the right procedure.
- A built-in or community skill (`obra/superpowers`, `anthropics/skills`) already does what you need → enable it via plugin or vendor it; don't reinvent.

## When NOT to add a skill

- Single-use procedure → just prompt directly.
- Procedure that varies wildly per call → write the variations into the rule, not the skill.
- The skill would just be "be careful" → that's not a procedure; either add a hook (enforces by construction) or accept that some judgment is irreducible.
```

- [ ] **Step 4: Rewrite `context-md-anatomy.md`**

Open and replace contents with:

```markdown
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
```

- [ ] **Step 5: Rewrite `common-mistakes.md`**

Open and replace contents with:

```markdown
# Common Mistakes (and How to Fix Them)

Earned mistakes from running this scaffold. Add to this list when you see a new pattern.

## 1. One giant `CLAUDE.md`

**What happens:** You put everything — full architecture, full conventions, full standards — into `CLAUDE.md` because it's "always loaded."

**Why it breaks:** `CLAUDE.md` is loaded in EVERY conversation. If it's 500 lines, you've burned tokens on iteration-process details when the agent is reviewing a one-line change.

**Fix:** `CLAUDE.md` = map only. Folder structure, naming conventions, cross-workspace flow, agent roles at a glance. Everything else lives in workspace `CONTEXT.md` files and `.claude/`.

## 2. No "Skip These" column

**What happens:** Your "What to Load" table tells agents what to read, but not what to ignore.

**Why it breaks:** Without explicit skip instructions, a thorough agent loads related-looking files "just in case." Wasted context, potential distraction.

**Fix:** Add the "Skip These" column. Be explicit about what's NOT needed for each task.

## 3. Skills listed but not triggered

**What happens:** You list skills in `CLAUDE.md` but never wire them into specific workflow moments.

**Why it breaks:** The agent knows `/tdd-loop` exists but doesn't know when to invoke it. It either invokes randomly or never.

**Fix:** Wire skills into `CONTEXT.md` routing tables with explicit trigger conditions. "Implementer agent, every cycle" is a trigger. "Available" is not.

## 4. Code in `02-implement/` instead of `src/`

**What happens:** The implementer agent writes the actual code under `build/workflows/NN/02-implement/` because the iteration is "scoped" there.

**Why it breaks:** Code that ships needs to live where the build/lint/deploy tools find it (`src/`). Splitting "process notes" from "shipped code" is the whole reason for the two-folder pattern.

**Fix:** Code goes to `src/`, period. `02-implement/notes-N.md` records what was done; `src/` IS what was done. The reviewer flags any code that ended up in `02-implement/`.

## 5. Project-specific terms leaking into `.claude/rules/` or `.claude/skills/`

**What happens:** Someone writes "Use Stripe webhooks for billing events" in `.claude/skills/data-analysis/SKILL.md`.

**Why it breaks:** When the scaffold is copied to a non-Stripe project, that skill becomes confusing or wrong.

**Fix:** The `enforce-portability.sh` hook catches this if `stripe` is in `.claude/.portability-deny.txt`. Add project-specific terms to that file as you encounter them. Move project-specific facts to `.claude/reference/` (which the consumer rewrites).

## 6. Skipping the reviewer or adversary

**What happens:** Implementer finishes a cycle and you (the orchestrator) decide it looks good and skip straight to `04-output/`.

**Why it breaks:** The hooks block you (`block-output-without-signoff.sh`), so you'll hit the wall. More importantly, the reviewer + adversary catch what you don't think to check.

**Fix:** Always run both, even for small iterations. For trivial work, the cycle is fast — but it's not optional.

## 7. Cycling past 5

**What happens:** Cycle 5 fails. You think "one more try" and start cycle 6.

**Why it breaks:** The hook blocks you (`block-cycle-overrun.sh`). Beyond that — at 5 cycles, the spec is wrong, not the implementation. More cycles won't fix that.

**Fix:** When the cycle cap is hit, stop. Write `04-output/ESCALATION.md`. Re-engage the planner with revised inputs. Open a NEW iteration.

## 8. Building the perfect structure before doing any work

**What happens:** You spend a week tuning `.claude/rules/`, perfecting every CONTEXT.md, before running a single iteration.

**Why it breaks:** You don't know what your project actually needs until you've run through the loop a few times. Pre-built rules will be wrong; pre-configured skills will be unused.

**Fix:** Run a few iterations first. Note what goes wrong. Then evolve the scaffold based on real friction, not anticipated friction.

## 9. Mixing iteration types in one folder

**What happens:** `lab/03-graphql-eval/` outgrows the spike shape and you start adding tests, CI configs, production code.

**Why it breaks:** `lab/` is throwaway. Code there isn't reachable from `src/` and won't be deployed. You're building a feature in the wrong workspace.

**Fix:** When a spike's outcome is "Pursue," CLOSE the lab iteration (write the REPORT), open a `spec/` artifact, then start a fresh `build/workflows/NN-<slug>/`. The prototype code stays in `lab/` as historical reference.

## 10. Editing accepted ADRs

**What happens:** A decision recorded in `spec/adrs/0003-use-postgres.md` turned out wrong. You edit the ADR.

**Why it breaks:** ADRs are append-only by convention. Editing erases history of what was decided when. Future readers won't understand why the codebase has Postgres-shaped seams if the ADR pretends Mongo was always the choice.

**Fix:** Write a NEW ADR (`0007-switch-to-mongo.md`) that supersedes the old one. Update the old ADR's status to "Superseded by 0007" and add a link. Never touch the rest of its body.
```

- [ ] **Step 6: Verify all four teaching files exist + the empty `_examples/` directory is gone**

Run:
```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/*.md | sort
```
Expected:
```
/Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/common-mistakes.md
/Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/context-md-anatomy.md
/Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/how-to-adapt.md
/Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/skill-integration-patterns.md
```

Run:
```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/_examples 2>&1 | head -1
```
Expected: `ls: ... _examples: No such file or directory`.

### Task 29: Run the acceptance checklist

**Files:** verification only.

The full criteria are in §10 of the design spec. Below is the executable subset.

- [ ] **Step 1: Verify rule budget**

```bash
total=$(wc -c /Users/gardnerwilson/workspace/workspace-blueprint/.claude/rules/*.md | tail -1 | awk '{print $1}')
echo "Rules total: $total bytes (budget: 40000)"
[ "$total" -lt 40000 ] && echo "PASS" || echo "FAIL: over budget"
```
Expected: PASS, total well under 40000.

- [ ] **Step 2: Verify all 10 skills have SKILL.md with frontmatter**

```bash
for s in tdd-loop bug-investigation refactor-protocol spike-protocol spec-authoring data-analysis docx pptx xlsx pdf; do
  f=/Users/gardnerwilson/workspace/workspace-blueprint/.claude/skills/$s/SKILL.md
  if [ ! -f "$f" ]; then echo "MISSING: $s"; continue; fi
  head -5 "$f" | grep -q '^name:' && echo "$s: OK" || echo "$s: NO FRONTMATTER"
done
```
Expected: all 10 print `OK`.

- [ ] **Step 3: Verify all 4 agent specs exist**

```bash
for a in planner implementer reviewer adversary; do
  f=/Users/gardnerwilson/workspace/workspace-blueprint/.claude/agents/$a-agent.md
  [ -f "$f" ] && echo "$a: OK" || echo "$a: MISSING"
done
```
Expected: all 4 print `OK`.

- [ ] **Step 4: Verify all 4 hooks exist + executable**

```bash
for h in pre-commit-tdd block-cycle-overrun block-output-without-signoff enforce-portability; do
  f=/Users/gardnerwilson/workspace/workspace-blueprint/.claude/hooks/$h.sh
  if [ ! -x "$f" ]; then echo "$h: MISSING or NON-EXECUTABLE"; else echo "$h: OK"; fi
done
```
Expected: all 4 print `OK`.

- [ ] **Step 5: Verify settings.json validity + key fields**

```bash
jq empty /Users/gardnerwilson/workspace/workspace-blueprint/.claude/settings.json && echo "JSON: OK"
mcps=$(jq -r '.mcpServers | keys | join(",")' /Users/gardnerwilson/workspace/workspace-blueprint/.claude/settings.json)
echo "MCP servers: $mcps"
hooks=$(jq -r '.hooks | keys | join(",")' /Users/gardnerwilson/workspace/workspace-blueprint/.claude/settings.json)
echo "Hook events: $hooks"
```
Expected: `JSON: OK`; MCP servers includes `filesystem,git,fetch,github`; hook events include `PreToolUse,PostToolUse`.

- [ ] **Step 6: Verify all 4 workspace CONTEXT.md files exist with standard sections**

```bash
for w in spec lab build ship; do
  f=/Users/gardnerwilson/workspace/workspace-blueprint/$w/CONTEXT.md
  if [ ! -f "$f" ]; then echo "$w: MISSING"; continue; fi
  for sec in "## What This Workspace Is" "## What to Load" "## Folder Structure" "## Skills & Tools" "## What NOT to Do"; do
    grep -qF "$sec" "$f" || echo "$w: missing section: $sec"
  done
  echo "$w: checked"
done
```
Expected: each workspace prints `checked` with no `missing section` lines in between.

- [ ] **Step 7: Verify templates exist**

```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/lab/00-template/{PREFLIGHT,VERIFY,REPORT}.md
ls /Users/gardnerwilson/workspace/workspace-blueprint/build/workflows/00-template/{01-spec/SPEC,02-implement/notes-1,03-validate/review-N.md.template,04-output/OUTPUT}.md 2>&1 | head
```
Expected: all paths print without errors. (The `review-N.md.template` and `adversary-N.md.template` may need a `2>&1` to suppress the suffix-pattern weirdness; verify each individually if the glob is unhappy.)

- [ ] **Step 8: Verify legacy DevRel preservation**

```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/legacy-devrel-example/
```
Expected: `community  production  README.md  writing-room`.

- [ ] **Step 9: Verify Clief Notes preservation**

```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/clief-notes/
```
Expected: `inventory.md  resource_index.pdf  skills_field_manual.pdf`.

- [ ] **Step 10: Verify office-skills-source preservation**

```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/docs/teaching/office-skills-source/
```
Expected: any subset of `CLAUDE.md README.md html2pptx-local.cjs package-lock.json package.json requirements.txt` (depending on what existed in the original).

- [ ] **Step 11: Verify `claude-office-skills-ref/` is gone**

```bash
ls /Users/gardnerwilson/workspace/workspace-blueprint/claude-office-skills-ref 2>&1 | head -1
```
Expected: `ls: ... No such file or directory`.

- [ ] **Step 12: Re-run portability hook against final `.claude/` content**

```bash
fail_count=0
for f in $(find /Users/gardnerwilson/workspace/workspace-blueprint/.claude/rules /Users/gardnerwilson/workspace/workspace-blueprint/.claude/skills -type f -name '*.md'); do
  out=$(echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$f\"}}" \
    | /Users/gardnerwilson/workspace/workspace-blueprint/.claude/hooks/enforce-portability.sh 2>&1)
  rc=$?
  if [ $rc -ne 0 ]; then echo "FAIL: $f"; fail_count=$((fail_count + 1)); fi
done
echo "FAILURES: $fail_count"
```
Expected: `FAILURES: 0`.

If any step in this task fails, STOP and address before committing. The goal of Commit 3 is a green acceptance check.

### Task 30: Stage and commit Commit 3

- [ ] **Step 1: Stage the changed and new files**

```bash
git add workspace-blueprint/CLAUDE.md
git add workspace-blueprint/CONTEXT.md
git add workspace-blueprint/START-HERE.md
git add workspace-blueprint/README.md
git add workspace-blueprint/docs/teaching/how-to-adapt.md
git add workspace-blueprint/docs/teaching/skill-integration-patterns.md
git add workspace-blueprint/docs/teaching/context-md-anatomy.md
git add workspace-blueprint/docs/teaching/common-mistakes.md
git add -u workspace-blueprint/_examples 2>/dev/null || true
```

- [ ] **Step 2: Verify staged set**

```bash
git status --short | grep workspace-blueprint
```

Expected: rewrites of `CLAUDE.md`, `CONTEXT.md`, `START-HERE.md`; new `README.md`; four new files in `docs/teaching/`; deletions of `_examples/*` if they were tracked. Nothing outside `workspace-blueprint/`.

- [ ] **Step 3: Commit**

```bash
git commit -m "$(cat <<'EOF'
Migration: rewrite root docs for software-dev, port _examples/ to teaching

- Rewrite CLAUDE.md as the always-loaded MAP for the new structure
- Rewrite CONTEXT.md as the task ROUTER, embedding Clief Notes §4.1
  decision sequence
- Rewrite START-HERE.md with software-dev onboarding + scaffold-bootstrap
  procedures (full clone vs scaffolding-only rsync)
- Add README.md as the public-facing repo description
- Move _examples/0[1-4]-*.md to docs/teaching/ with full software-dev
  rewrites (how-to-adapt, skill-integration-patterns, context-md-anatomy,
  common-mistakes)
- Remove now-empty _examples/ directory

Acceptance criteria checklist (Task 29) all green:
- 5 rules under 40KB budget
- 10 skills with SKILL.md + YAML frontmatter
- 4 agent specs present
- 4 hooks executable + smoke-tested
- settings.json valid; 4 MCP servers + hooks wired
- 4 workspace CONTEXT.md files have all standard sections
- lab/00-template/ and build/workflows/00-template/ present
- Legacy DevRel + Clief Notes + office-skills provenance preserved
- claude-office-skills-ref/ fully decomposed and removed
- portability hook passes against all .claude/rules/ and .claude/skills/

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: Verify the commit + final repo state**

```bash
git log --oneline -5
ls /Users/gardnerwilson/workspace/workspace-blueprint/
```
Expected: three new commits visible (cleanup, scaffolding, migration). Top-level listing shows: `.claude  build  CLAUDE.md  CONTEXT.md  docs  lab  README.md  scripts  shared  ship  spec  src  START-HERE.md`.

---

## Done

The redesign is complete when:

1. All three commits land cleanly on `main`.
2. Task 29's acceptance checklist passes end-to-end.
3. The final `git status --short | grep workspace-blueprint` shows no surprises.

If any acceptance criterion fails after Commit 3, fix in a follow-up commit (don't amend the migration commit — it's already pushed conceptually, even if not literally pushed to a remote).

For deferred work (bootstrap script, evaluating obra/superpowers in depth, etc.), open a new iteration in `lab/` or write a `spec/briefs/` entry.


