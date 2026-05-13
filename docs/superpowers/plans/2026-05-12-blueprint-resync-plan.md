# Blueprint Resync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring Pitwall's scaffold up to the current state of `workspace-blueprint` (routing/registry, ECC submodule, multi-IDE preambles, new skills/rules, npm scripts, `.github/workflows/`) without losing F1 domain content or Pitwall-specific software-dev customizations. Land the result as 22 reviewable commits on `chore/blueprint-resync`, then open a PR for merge into `main`.

**Architecture:** One wholesale `rsync -avc` overlay (B1) brings blueprint files in across the board; Pitwall-exclusive directories survive by default (rsync without `--delete`). Then purely additive replay commits restore F1 facts, Pitwall dev customizations, and top-level identity onto the new shared files. Submodule and registry rebuild land last. Two follow-up commits create `DEVELOPMENT.md` (Pitwall progress tracker) and `docs/development-philosophy.md` (durable principles doc).

**Tech Stack:** `rsync`, `git`, `git submodule`, `npm` (for blueprint's registry tooling), `bash` (hook self-tests), `gh` (PR creation). No application-level code in this iteration.

**TDD applicability:** **This iteration is migration/scaffolding only — no new production code is written.** TDD does not apply. Verification is by checklist (file presence, content grep, hook execution, registry rebuild exit code). The "write the verification before doing the work" *spirit* of TDD applies and is honored by completing the success-criteria checks in Section 4 of the spec at the gate before opening the PR.

**Related artifacts:**
- Spec: `docs/superpowers/specs/2026-05-12-blueprint-resync-design.md` (commit `4763e7e`)
- Adversary review: `docs/superpowers/specs/2026-05-12-blueprint-resync-adversary-review.md` (commit `9fd3ef8`)
- Source-of-truth blueprint: `/Users/gardnerwilson/workspace/github.com/elessar617/workspace-blueprint` (must be on its `main` and clean before running B1)

---

## File map

### Created by this plan
- `.migration-scratch/` — temporary scratch dir (gitignored); deleted in Task 23.
- `.migration-scratch/pitwall-pre-resync/` — snapshot of pre-merge state for reference during replays.
- `.migration-scratch/pitwall-overlay.md` — hand-authored checklist of every F1 fact + Pitwall dev customization that must be replayed.
- `DEVELOPMENT.md` — top-level Pitwall progress tracker (Task 25).
- `docs/development-philosophy.md` — durable principles doc (Task 26).
- (Many) — all files that blueprint has and Pitwall doesn't, brought in by B1 rsync.

### Modified by this plan
- The 20 shared files enumerated in the spec's B1 row (rsync overwrites blueprint content; then replays restore F1/dev content additively).
- `.gitignore` — re-add F1 patterns (Task 22).

### Untouched by this plan (verification gates 7–10 confirm)
- `src/pitwall/`
- `data/`
- `shared/`
- `lab/01-openf1-feed-eval/`
- `spec/briefs/pitwall-overview.md`
- `docs/superpowers/{specs,plans}/2026-05-1{1,2}-pitwall-*`
- `docs/teaching/bootstrap.md`
- `faceoff/` (gitignored)

---

## Pre-flight verification (run once before Task 1)

- [ ] **P1: Confirm clean working tree on `main`.**

Run: `git status --short`
Expected: empty output.
If non-empty: stop. Commit or stash before proceeding.

- [ ] **P2: Confirm we're on `main` at the expected SHA.**

Run: `git rev-parse --abbrev-ref HEAD && git log -1 --oneline`
Expected: branch is `main`, HEAD is `4763e7e docs(spec): revise resync design per adversary review` (or a later commit if more work has landed).
If branch is not `main`: `git checkout main` first.

- [ ] **P3: Confirm blueprint source tree is clean and on its `main`.**

Run: `cd /Users/gardnerwilson/workspace/github.com/elessar617/workspace-blueprint && git status --short && git rev-parse --abbrev-ref HEAD && git rev-parse --short HEAD`
Expected: empty status, branch `main`, capture HEAD SHA (referred to as `<BLUEPRINT_SHA>` below).
If status non-empty or wrong branch: pause; fix the source tree state before proceeding.

- [ ] **P4: Capture the ECC submodule SHA from blueprint.**

Run: `cd /Users/gardnerwilson/workspace/github.com/elessar617/workspace-blueprint && git submodule status external/ecc`
Expected: one line of the form `<SHA> external/ecc (...)`. Record the SHA as `<ECC_SHA>`; you'll pin to it in Task 20.

- [ ] **P5: Confirm `rsync` is GNU/BSD rsync, not a stub.**

Run: `rsync --version | head -1`
Expected: a version banner. The flags `-avc` and `--exclude=PATTERN` must be supported (true for stock macOS rsync and any modern Linux rsync).

- [ ] **P6: Confirm `npm` is available.**

Run: `npm --version`
Expected: a version number (any reasonably modern Node/npm — blueprint's `package.json` engines field is the source of truth for the minimum).

If any pre-flight check fails, stop and resolve before starting Task 1.

---

## Phase A: Pre-flight setup

### Task 1: Create the resync branch

**Files:**
- No files modified yet — branch only.

- [ ] **Step 1: Create and switch to the feature branch.**

Run:
```bash
git checkout -b chore/blueprint-resync
git rev-parse --abbrev-ref HEAD
```
Expected output: `chore/blueprint-resync`.

- [ ] **Step 2: Verify branch starts at the same SHA as `main`.**

Run: `git log -1 --oneline main && git log -1 --oneline chore/blueprint-resync`
Expected: both show the same SHA.

(No commit on this task — branch creation is the work.)

---

### Task 2: Snapshot the pre-merge state (A1)

**Files:**
- Create: `.migration-scratch/pitwall-pre-resync/` (mirror of files that will be overwritten)
- Create: `.migration-scratch/pitwall-overlay.md` (replay checklist)
- Modify: `.gitignore` (add `.migration-scratch/`)

- [ ] **Step 1: Add `.migration-scratch/` to `.gitignore`.**

Edit `.gitignore` to add a new section at the end:
```
# Temporary migration scratch (created/deleted within a single iteration)
.migration-scratch/
```

- [ ] **Step 2: Create the scratch directory tree.**

Run:
```bash
mkdir -p .migration-scratch/pitwall-pre-resync/.claude/hooks
mkdir -p .migration-scratch/pitwall-pre-resync/.claude/reference
```

- [ ] **Step 3: Copy the 20 overwrite-targets from current state into the snapshot.**

Run:
```bash
cp .gitignore .migration-scratch/pitwall-pre-resync/.gitignore
cp CLAUDE.md .migration-scratch/pitwall-pre-resync/CLAUDE.md
cp CONTEXT.md .migration-scratch/pitwall-pre-resync/CONTEXT.md
cp README.md .migration-scratch/pitwall-pre-resync/README.md
cp START-HERE.md .migration-scratch/pitwall-pre-resync/START-HERE.md
cp .claude/.portability-deny.txt .migration-scratch/pitwall-pre-resync/.claude/.portability-deny.txt
cp .claude/MCP-SETUP.md .migration-scratch/pitwall-pre-resync/.claude/MCP-SETUP.md
cp .claude/settings.json .migration-scratch/pitwall-pre-resync/.claude/settings.json
cp .claude/settings.local.json .migration-scratch/pitwall-pre-resync/.claude/settings.local.json
cp .claude/hooks/block-cycle-overrun.sh .migration-scratch/pitwall-pre-resync/.claude/hooks/block-cycle-overrun.sh
cp .claude/hooks/block-output-without-signoff.sh .migration-scratch/pitwall-pre-resync/.claude/hooks/block-output-without-signoff.sh
cp .claude/hooks/enforce-portability.sh .migration-scratch/pitwall-pre-resync/.claude/hooks/enforce-portability.sh
cp .claude/hooks/pre-commit-tdd.sh .migration-scratch/pitwall-pre-resync/.claude/hooks/pre-commit-tdd.sh
cp .claude/reference/claude-platform-capabilities.md .migration-scratch/pitwall-pre-resync/.claude/reference/claude-platform-capabilities.md
cp .claude/reference/external-resources.md .migration-scratch/pitwall-pre-resync/.claude/reference/external-resources.md
cp .claude/reference/frontend-stack.md .migration-scratch/pitwall-pre-resync/.claude/reference/frontend-stack.md
cp .claude/reference/glossary.md .migration-scratch/pitwall-pre-resync/.claude/reference/glossary.md
cp .claude/reference/mcp-servers.md .migration-scratch/pitwall-pre-resync/.claude/reference/mcp-servers.md
cp .claude/reference/project-architecture.md .migration-scratch/pitwall-pre-resync/.claude/reference/project-architecture.md
cp .claude/reference/tech-stack.md .migration-scratch/pitwall-pre-resync/.claude/reference/tech-stack.md
```

- [ ] **Step 4: Verify the snapshot has 20 files.**

Run: `find .migration-scratch/pitwall-pre-resync -type f | wc -l`
Expected: `20`.
If less: re-run Step 3 carefully.

- [ ] **Step 5: Author the replay checklist.**

Create `.migration-scratch/pitwall-overlay.md` with this exact content:

```markdown
# Pitwall replay checklist

For each F1 fact or Pitwall software-dev customization found in the
`.migration-scratch/pitwall-pre-resync/` snapshot, tick the corresponding
box BEFORE the relevant Phase C commit. Each line maps to a specific commit.

## F1 deny terms (Task 5 → C1)

- [ ] All 32 F1 terms restored to `.claude/.portability-deny.txt` under the
      existing `# Pitwall (Formula 1 TUI)` header. Verify by diffing the
      Pitwall-specific section of snapshot vs current file.

## Reference files — F1 + dev content (Tasks 6–12 → C2–C8)

For each file: read the snapshot version, read the new (blueprint) version,
identify the F1 facts and Pitwall dev customizations in the snapshot,
re-introduce them into the new version's appropriate sections, and tick.

- [ ] `tech-stack.md` — F1 stack (Python, Textual, FastF1, OpenF1, Jolpica),
      coverage threshold, test commands, lint/format commands
- [ ] `frontend-stack.md` — Textual specifics, terminal rendering choices
- [ ] `project-architecture.md` — Pitwall layout, src/pitwall/ structure,
      F1 data flow, season tracker / live timing / strategy-game subsystems
- [ ] `glossary.md` — F1 terms (DRS, tyre compounds, parc fermé, etc.)
- [ ] `external-resources.md` — FastF1 docs, OpenF1 API, Jolpica/Ergast,
      F1 official sources
- [ ] `mcp-servers.md` — Pitwall-specific MCP entries (if any)
- [ ] `claude-platform-capabilities.md` — Pitwall-specific platform notes
      (if any)

## Top-level docs — Pitwall identity (Tasks 13–16 → C9–C12)

- [ ] `CLAUDE.md` — "What This Repo Is" Pitwall intro, F1 framing,
      Pitwall folder structure callouts
- [ ] `CONTEXT.md` — Pitwall-specific routing, F1 task examples
- [ ] `README.md` — Pitwall public-facing description
- [ ] `START-HERE.md` — Pitwall onboarding

## Settings + MCP setup (Tasks 17–19 → C13–C15)

- [ ] `settings.json` — any Pitwall-specific hook profile or MCP entries
- [ ] `settings.local.json` — any per-user Pitwall config
- [ ] `MCP-SETUP.md` — any Pitwall-specific MCP setup steps

## Gitignore (Task 22 → C16)

- [ ] `.gitignore` — F1 patterns: `data/*.db`, `data/*.sqlite`,
      `data/*.sqlite3`, `data/*.db-journal`, `faceoff/`,
      `.serena/`, `.remember/`

## Verification (do AFTER all replays land)

- [ ] `grep -rE "fastf1|openf1|jolpica" .claude/reference/` returns hits
- [ ] `grep -rE "fastf1|openf1|jolpica|formula 1|pitwall" .claude/rules/ .claude/skills/` returns ZERO hits outside vendored office-skill paths
```

- [ ] **Step 6: Commit the snapshot.**

Run:
```bash
git add .gitignore .migration-scratch/
git status --short
```
Expected: 2 modified/new entries (`.gitignore` and `.migration-scratch/`).
But: `.migration-scratch/` is now ignored! It will NOT appear in `git status`. That's intentional. The directory exists on disk for the duration of the migration; it is never committed.

So the actual diff is just `.gitignore`:
```bash
git add .gitignore
git commit -m "chore(migration): snapshot pre-resync state and ignore scratch dir

Adds .migration-scratch/ to .gitignore. The scratch directory itself is
populated with a snapshot of the 20 files that will be overwritten by the
wholesale rsync overlay in the next commit, plus a hand-authored replay
checklist. The directory is local-only and will be deleted in Task 23
once the migration is complete."
```

Expected: commit succeeds. `git status --short` is empty.

---

### Task 3: Remove empty build/workflows placeholders (A2)

**Files:**
- Delete: `build/workflows/01-spec/.gitkeep`
- Delete: `build/workflows/02-implement/.gitkeep`
- Delete: `build/workflows/03-validate/.gitkeep`
- Delete: `build/workflows/04-output/.gitkeep`
- Delete: `build/workflows/{01-spec,02-implement,03-validate,04-output}/` (now-empty dirs)

- [ ] **Step 1: Verify the dirs only have .gitkeep files.**

Run: `find build/workflows/01-spec build/workflows/02-implement build/workflows/03-validate build/workflows/04-output -type f`
Expected: exactly 4 `.gitkeep` files.
If anything else: stop. Investigate. These dirs are supposed to be empty placeholders only.

- [ ] **Step 2: Remove the dirs.**

Run:
```bash
git rm build/workflows/01-spec/.gitkeep
git rm build/workflows/02-implement/.gitkeep
git rm build/workflows/03-validate/.gitkeep
git rm build/workflows/04-output/.gitkeep
rmdir build/workflows/01-spec build/workflows/02-implement build/workflows/03-validate build/workflows/04-output
```

- [ ] **Step 3: Commit.**

Run:
```bash
git commit -m "chore(scaffold): remove empty build/workflows placeholders

Per workspace-blueprint convention, iterations are created on demand
under build/workflows/NN-<slug>/. The empty placeholder phase directories
(01-spec/, 02-implement/, 03-validate/, 04-output/) at the workflows
level are not used and should not exist."
```

Expected: commit succeeds.

---

## Phase B: Wholesale overlay

### Task 4: Wholesale rsync overlay (B1)

**Files:**
- Create: ~580 new files from blueprint (everything blueprint has and Pitwall doesn't).
- Modify: 20 files (the spec's confirmed overwrite list).

This is the single biggest commit in the iteration. It is intentionally bulky — reviewers verify it by running `diff -r` against the blueprint source, not by line-by-line read.

- [ ] **Step 1: Dry-run the rsync and confirm the overwrite list.**

Run:
```bash
rsync -avnc /Users/gardnerwilson/workspace/github.com/elessar617/workspace-blueprint/ ./ \
  --exclude=.git \
  --exclude=node_modules \
  --exclude=external/ecc \
  --exclude=.serena \
  --exclude=.remember \
  2>&1 | tee /tmp/rsync-dryrun.log | tail -5
```
Expected last line: `total size is <N> speedup is <M>`. Total transfer should be roughly 600 files.

- [ ] **Step 2: Extract the actual overwrite list (files that exist in dest AND would change).**

Run:
```bash
rsync -avnc /Users/gardnerwilson/workspace/github.com/elessar617/workspace-blueprint/ ./ \
  --exclude=.git \
  --exclude=node_modules \
  --exclude=external/ecc \
  --exclude=.serena \
  --exclude=.remember \
  2>&1 | grep -v '/$' | grep -v '^$' \
  | while read f; do [ -f "$f" ] && echo "$f"; done | sort > /tmp/rsync-overwrites.txt
wc -l /tmp/rsync-overwrites.txt
```
Expected: exactly **20** lines.
If the count differs from 20: the overwrite list has drifted since the spec was written. Stop. Inspect `/tmp/rsync-overwrites.txt` against the spec's B1 row to find the delta. Document the delta and add or remove a replay commit in Phase C as appropriate.

- [ ] **Step 3: Diff the overwrite list against the spec's expected 20.**

Run:
```bash
cat /tmp/rsync-overwrites.txt
```
Expected (sort order from `sort`):
```
.claude/.portability-deny.txt
.claude/hooks/block-cycle-overrun.sh
.claude/hooks/block-output-without-signoff.sh
.claude/hooks/enforce-portability.sh
.claude/hooks/pre-commit-tdd.sh
.claude/MCP-SETUP.md
.claude/reference/claude-platform-capabilities.md
.claude/reference/external-resources.md
.claude/reference/frontend-stack.md
.claude/reference/glossary.md
.claude/reference/mcp-servers.md
.claude/reference/project-architecture.md
.claude/reference/tech-stack.md
.claude/settings.json
.claude/settings.local.json
.gitignore
CLAUDE.md
CONTEXT.md
README.md
START-HERE.md
```
If anything other than these 20: stop, investigate.

- [ ] **Step 4: Execute the real rsync.**

Run:
```bash
rsync -avc /Users/gardnerwilson/workspace/github.com/elessar617/workspace-blueprint/ ./ \
  --exclude=.git \
  --exclude=node_modules \
  --exclude=external/ecc \
  --exclude=.serena \
  --exclude=.remember
```
Note: dropped the `-n` flag (no longer a dry run). Same flags otherwise.
Expected: many lines of file transfers, ending with `sent X bytes received Y bytes ...`.

- [ ] **Step 5: Confirm the overlay landed and Pitwall-exclusive content is intact.**

Run:
```bash
# Pitwall-exclusive directories must still exist:
ls lab/01-openf1-feed-eval/REPORT.md
ls spec/briefs/pitwall-overview.md
ls docs/superpowers/specs/2026-05-11-pitwall-design.md
ls docs/superpowers/plans/2026-05-11-pitwall-v01-season-tracker.md
ls docs/superpowers/specs/2026-05-12-blueprint-resync-design.md
ls docs/teaching/bootstrap.md
ls data/.gitkeep

# New blueprint files must now exist:
ls ROUTING.md
ls SKILLS.md
ls AGENTS.md
ls GEMINI.md
ls package.json
ls scripts/bootstrap.sh
ls .claude/skills/brainstorming/SKILL.md
```
Expected: all `ls` commands succeed with no "No such file" errors.
If any fail: stop, investigate.

- [ ] **Step 6: Run `npm install` to verify the npm setup works (do NOT commit `node_modules/`).**

Run: `npm install --silent`
Expected: succeeds, creates `node_modules/`. No errors. `node_modules/` is NOT committed because it should be in blueprint's `.gitignore` which we just adopted.

- [ ] **Step 7: Verify `node_modules/` is gitignored.**

Run: `git check-ignore node_modules/`
Expected output: `node_modules/`.
If empty: the new `.gitignore` doesn't exclude `node_modules/`. Add it now before staging.

- [ ] **Step 8: Stage and commit.**

Run:
```bash
git add -A
git status --short | head -20
```
Expected: many new files (`A` prefix), 20 modified (`M` prefix), 0 deleted. `node_modules/` is NOT in the list.

Then commit:
```bash
git commit -m "chore(scaffold): wholesale overlay of blueprint onto Pitwall

Brings every blueprint file into Pitwall via a single rsync -avc.
Pitwall-exclusive directories (data/, src/pitwall/, shared/, lab/01-openf1-feed-eval/,
spec/briefs/pitwall-overview.md, docs/superpowers/{specs,plans}/2026-05-1*-pitwall-*,
docs/teaching/bootstrap.md) are untouched by rsync because --delete is omitted.

20 shared files are overwritten with blueprint's versions: 5 hooks, 7 reference
files, 2 settings files, MCP-SETUP.md, .portability-deny.txt, .gitignore, and 4
top-level docs (CLAUDE.md, CONTEXT.md, README.md, START-HERE.md). Each is
reconciled in a subsequent purely additive replay commit (C1-C16).

Verified via dry-run on 2026-05-12: 20 overwrites and ~580 new files. Source:
workspace-blueprint at SHA <BLUEPRINT_SHA from P3>."
```
Replace `<BLUEPRINT_SHA from P3>` with the actual short SHA captured in P3.

Expected: commit succeeds. `git status --short` is empty (node_modules excluded).

- [ ] **Step 9: Verify the hooks now work.**

Run: `bash .claude/hooks/enforce-portability.sh 2>&1 | head -5 || echo "hook ran"`
Expected: hook either passes silently or prints output (depending on its argument handling). It must not throw a "command not found" or path error.

If the hook fails on missing arguments: that's expected behavior (hooks are typically invoked via Claude Code's tool-call lifecycle, not standalone). The verification gate in Task 24 runs hooks against synthetic edits.

---

## Phase C: F1 + dev content replays (additive, one file per commit)

### Task 5: Restore F1 deny terms (C1)

**Files:**
- Modify: `.claude/.portability-deny.txt`

**Why first:** subsequent replay commits will introduce F1 terms into `.claude/reference/*.md`. The `enforce-portability.sh` hook scans `.claude/rules/` and `.claude/skills/` (NOT `.claude/reference/`) — so technically the hook wouldn't block reference edits. **But** if any future edit lands in `rules/` or `skills/` during the migration window, the deny list needs to be sane. Safer to restore first.

- [ ] **Step 1: Read the current (blueprint) deny list and the snapshot.**

Run:
```bash
diff .claude/.portability-deny.txt .migration-scratch/pitwall-pre-resync/.claude/.portability-deny.txt
```
Expected: a diff showing Pitwall's F1 section is present in the snapshot but absent in the current file.

- [ ] **Step 2: Append Pitwall's F1 section to `.claude/.portability-deny.txt`.**

The Pitwall section is the 32 lines under the comment `# Pitwall (Formula 1 TUI)` in the snapshot. Copy them verbatim. The full section to append (exactly as it was in the snapshot):

```
# Pitwall (Formula 1 TUI) — domain-specific terms that must not leak into
# .claude/rules/ or .claude/skills/. These keep this scaffold's rules and
# skills portable to non-F1 projects.
pitwall
formula 1
formula-1
formula1
fastf1
openf1
jolpica
ergast
pirelli
parc fermé
parc ferme
fia
fom
silverstone
monza
nurburgring
spa-francorchamps
sprint qualifying
pole position
constructors' championship
tyre compound
tyre-degradation
tyre deg curve
pit window
pit-window prompt
safety car
virtual safety car
strategy plan
sim delta
player-vs-actual
track-position map
live timing tower
drs zone
chequered flag
```

Append (with a blank line separator) to the end of the current `.claude/.portability-deny.txt`.

- [ ] **Step 3: Verify the deny list now contains both blueprint's base and Pitwall's terms.**

Run: `grep -c "fastf1" .claude/.portability-deny.txt`
Expected: at least 1.

Run: `wc -l .claude/.portability-deny.txt`
Expected: approximately (blueprint's line count) + 34 (32 F1 terms + 2 comment lines + 1 blank). Sanity check, not strict.

- [ ] **Step 4: Tick the corresponding checkbox in the overlay checklist.**

Edit `.migration-scratch/pitwall-overlay.md` to change `- [ ]` to `- [x]` for the "F1 deny terms" item.

- [ ] **Step 5: Commit.**

Run:
```bash
git add .claude/.portability-deny.txt
git commit -m "chore(portability): restore Pitwall F1 deny terms

Re-adds Pitwall's 32 F1-domain terms (FastF1, OpenF1, tyre compounds,
DRS, etc.) under the existing '# Pitwall (Formula 1 TUI)' header.
Sequenced before subsequent F1-content replays so the portability hook
has the right deny-list state throughout the migration."
```

---

### Task 6: Restore F1 + dev content in `.claude/reference/tech-stack.md` (C2)

**Files:**
- Modify: `.claude/reference/tech-stack.md`

- [ ] **Step 1: Read the snapshot and the current (blueprint) file.**

Run:
```bash
diff .migration-scratch/pitwall-pre-resync/.claude/reference/tech-stack.md .claude/reference/tech-stack.md | head -100
```
Inspect the diff. Pitwall's snapshot has F1-specific entries (Python, Textual, FastF1, OpenF1, Jolpica, lint/format commands, coverage threshold, etc.) that the new blueprint version is missing.

- [ ] **Step 2: Add the F1/Pitwall sections to the new file.**

Open `.claude/reference/tech-stack.md` in your editor. Identify the appropriate sections in the new (blueprint) structure where Pitwall's content fits. Typical sections to populate:
- "Language and runtime" → add Python version
- "Frameworks and libraries" → add Textual, FastF1, OpenF1, Jolpica
- "Build/test commands" → add Pitwall's commands
- "Lint/format" → add Pitwall's tools
- "Coverage threshold" → add Pitwall's value (if not in blueprint's default)

Use the snapshot as the source of truth. Where the snapshot has content the new blueprint structure doesn't have a section for, add a new section near the bottom labeled `## Pitwall-specific` and put it there.

- [ ] **Step 3: Verify F1 content is present.**

Run: `grep -E "fastf1|openf1|jolpica|textual|python" .claude/reference/tech-stack.md`
Expected: at least one match per term that was in the snapshot. If a term was in the snapshot but isn't in the new file: re-add it.

- [ ] **Step 4: Tick the checklist box.**

Edit `.migration-scratch/pitwall-overlay.md` to tick `tech-stack.md`.

- [ ] **Step 5: Commit.**

Run:
```bash
git add .claude/reference/tech-stack.md
git commit -m "docs(reference): restore F1+dev content in tech-stack.md

Replays Pitwall's F1 stack (Python, Textual, FastF1, OpenF1, Jolpica) and
dev customizations (build/test/lint/coverage settings) onto blueprint's
updated tech-stack.md structure. Source: pre-resync snapshot at
.migration-scratch/pitwall-pre-resync/.claude/reference/tech-stack.md."
```

---

### Task 7: Restore F1 + dev content in `.claude/reference/frontend-stack.md` (C3)

**Files:**
- Modify: `.claude/reference/frontend-stack.md`

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/.claude/reference/frontend-stack.md .claude/reference/frontend-stack.md | head -100`

- [ ] **Step 2: Replay Pitwall content.**

Pitwall's "frontend" is the Textual TUI. Add: Textual framework version, terminal rendering choices, color/style conventions, keybinding philosophy — whatever is in the snapshot.

- [ ] **Step 3: Verify.**

Run: `grep -iE "textual|tui|terminal" .claude/reference/frontend-stack.md`
Expected: hits.

- [ ] **Step 4: Tick `frontend-stack.md` in the checklist.**

- [ ] **Step 5: Commit.**

```bash
git add .claude/reference/frontend-stack.md
git commit -m "docs(reference): restore Pitwall TUI specifics in frontend-stack.md

Replays Textual TUI framework choices, terminal rendering decisions, and
Pitwall-specific UI conventions onto blueprint's updated frontend-stack.md."
```

---

### Task 8: Restore F1 + dev content in `.claude/reference/project-architecture.md` (C4)

**Files:**
- Modify: `.claude/reference/project-architecture.md`

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/.claude/reference/project-architecture.md .claude/reference/project-architecture.md | head -100`

- [ ] **Step 2: Replay Pitwall content.**

Pitwall's architecture content includes: `src/pitwall/` structure, F1 data flow (FastF1 → cache → TUI), session/race subsystem split, season-tracker / live-timing / strategy-game module layout, `data/` runtime layout, `shared/` purpose.

- [ ] **Step 3: Verify.**

Run: `grep -iE "src/pitwall|season|live timing|strategy|telemetry" .claude/reference/project-architecture.md`
Expected: hits.

- [ ] **Step 4: Tick `project-architecture.md`.**

- [ ] **Step 5: Commit.**

```bash
git add .claude/reference/project-architecture.md
git commit -m "docs(reference): restore Pitwall architecture in project-architecture.md

Replays Pitwall's src/pitwall/ layout, F1 data flow, and subsystem split
(season tracker / live timing / strategy game) onto blueprint's updated
project-architecture.md."
```

---

### Task 9: Restore F1 + dev content in `.claude/reference/glossary.md` (C5)

**Files:**
- Modify: `.claude/reference/glossary.md`

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/.claude/reference/glossary.md .claude/reference/glossary.md | head -100`

- [ ] **Step 2: Replay F1 glossary entries.**

Pitwall's glossary has F1 domain definitions: DRS, tyre compounds (soft/medium/hard/inter/wet), parc fermé, sprint qualifying, pit window, safety car, virtual safety car, tyre degradation curve, etc. Add them to the new file (likely in a `## F1 terms` section).

- [ ] **Step 3: Verify.**

Run: `grep -iE "drs|tyre|parc ferm|safety car|pit window" .claude/reference/glossary.md`
Expected: hits.

- [ ] **Step 4: Tick `glossary.md`.**

- [ ] **Step 5: Commit.**

```bash
git add .claude/reference/glossary.md
git commit -m "docs(reference): restore F1 glossary entries in glossary.md

Replays F1 domain terms (DRS, tyre compounds, parc fermé, sprint
qualifying, pit window, safety car, etc.) onto blueprint's updated
glossary.md."
```

---

### Task 10: Restore F1 + dev content in `.claude/reference/external-resources.md` (C6)

**Files:**
- Modify: `.claude/reference/external-resources.md`

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/.claude/reference/external-resources.md .claude/reference/external-resources.md | head -100`

- [ ] **Step 2: Replay external F1 resources.**

Pitwall's external-resources has: FastF1 docs URL, OpenF1 API URL, Jolpica / Ergast API URL, F1 official site, FIA technical regs, any reference data sources.

- [ ] **Step 3: Verify.**

Run: `grep -iE "fastf1|openf1|jolpica|ergast" .claude/reference/external-resources.md`
Expected: hits.

- [ ] **Step 4: Tick `external-resources.md`.**

- [ ] **Step 5: Commit.**

```bash
git add .claude/reference/external-resources.md
git commit -m "docs(reference): restore F1 external resources

Replays FastF1, OpenF1, Jolpica/Ergast, and F1 official source links
onto blueprint's updated external-resources.md."
```

---

### Task 11: Restore F1 + dev content in `.claude/reference/mcp-servers.md` (C7)

**Files:**
- Modify: `.claude/reference/mcp-servers.md`

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/.claude/reference/mcp-servers.md .claude/reference/mcp-servers.md | head -100`

- [ ] **Step 2: Replay any Pitwall-specific MCP entries.**

Inspect the snapshot for Pitwall-specific MCP server documentation. If none (i.e., snapshot is identical to blueprint except for unrelated drift), this commit may be a no-op — in which case skip Steps 3–5 and proceed to Task 12.

- [ ] **Step 3: Verify (if non-no-op).**

Confirm Pitwall MCP entries are present in the new file.

- [ ] **Step 4: Tick `mcp-servers.md`.**

- [ ] **Step 5: Commit (if non-no-op).**

```bash
git add .claude/reference/mcp-servers.md
git commit -m "docs(reference): restore Pitwall MCP entries in mcp-servers.md

Replays Pitwall-specific MCP server documentation onto blueprint's
updated mcp-servers.md."
```

If the file ended up identical to blueprint's: tick the checklist with a note "no Pitwall-specific content to replay" and skip the commit.

---

### Task 12: Restore F1 + dev content in `.claude/reference/claude-platform-capabilities.md` (C8)

**Files:**
- Modify: `.claude/reference/claude-platform-capabilities.md`

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/.claude/reference/claude-platform-capabilities.md .claude/reference/claude-platform-capabilities.md | head -100`

- [ ] **Step 2: Replay any Pitwall-specific platform notes.**

Likely no Pitwall-specific content here (this is Claude platform info, not Pitwall info). If none: this commit is a no-op.

- [ ] **Step 3: Tick `claude-platform-capabilities.md` (with no-op note if applicable).**

- [ ] **Step 4: Commit (skip if no-op).**

```bash
git add .claude/reference/claude-platform-capabilities.md
git commit -m "docs(reference): restore Pitwall platform notes in claude-platform-capabilities.md

Replays Pitwall-specific Claude platform notes onto blueprint's updated
claude-platform-capabilities.md."
```

---

### Task 13: Restore Pitwall identity in `CLAUDE.md` (C9)

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/CLAUDE.md CLAUDE.md | head -200`

The snapshot is Pitwall's customized top-level CLAUDE.md (with the "What This Repo Is" Pitwall intro, F1 framing, folder structure callouts for `data/`, `src/pitwall/`, `faceoff/`).

The current (blueprint) version is generic, describing the scaffold itself.

- [ ] **Step 2: Replay Pitwall identity onto the new structure.**

Replace the "What's inside" / generic-scaffold section with Pitwall's "What This Repo Is" content from the snapshot. Add Pitwall's folder-structure callouts. Preserve any NEW blueprint structural sections (the "Three-layer routing" / "Four workspaces" framing, ROUTING.md reference, the new portability discipline section, etc.) but adapt them to mention Pitwall where appropriate.

- [ ] **Step 3: Verify.**

Run: `grep -iE "pitwall|formula 1|f1 tui|f1 companion" CLAUDE.md | head -5`
Expected: at least 2 hits.

- [ ] **Step 4: Tick `CLAUDE.md`.**

- [ ] **Step 5: Commit.**

```bash
git add CLAUDE.md
git commit -m "docs(routing): restore Pitwall identity in CLAUDE.md

Replays Pitwall's 'What This Repo Is' intro, F1 framing, and folder-
structure callouts (data/, src/pitwall/, faceoff/) onto blueprint's
updated CLAUDE.md. Preserves blueprint's new routing/registry structural
sections (ROUTING.md reference, etc.)."
```

---

### Task 14: Restore Pitwall framing in `CONTEXT.md` (C10)

**Files:**
- Modify: `CONTEXT.md`

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/CONTEXT.md CONTEXT.md | head -200`

- [ ] **Step 2: Replay Pitwall framing.**

CONTEXT.md is the Layer 2 router. Pitwall's customization here is task-routing examples ("if working on F1 race telemetry, go to..."). Add these to the new file.

- [ ] **Step 3: Verify.**

Run: `grep -iE "pitwall|f1|race|session" CONTEXT.md | head -5`
Expected: hits.

- [ ] **Step 4: Tick `CONTEXT.md`.**

- [ ] **Step 5: Commit.**

```bash
git add CONTEXT.md
git commit -m "docs(routing): restore Pitwall framing in CONTEXT.md

Replays Pitwall task-routing examples (F1 race telemetry, session work,
strategy game) onto blueprint's updated CONTEXT.md."
```

---

### Task 15: Restore Pitwall framing in `README.md` (C11)

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/README.md README.md | head -200`

- [ ] **Step 2: Replay Pitwall framing.**

README.md is the public-facing repo description. Pitwall's snapshot has the "what is Pitwall" pitch (F1 TUI companion, season tracker + live timing + strategy game). The blueprint version is about the scaffold.

This is a more aggressive replay: most of the file body should be Pitwall-specific. Keep blueprint's structural sections (Getting started, Setup after cloning) but rewrite the body to be about Pitwall.

- [ ] **Step 3: Verify.**

Run: `head -20 README.md`
Expected: the first non-blank line is about Pitwall, not the workspace-blueprint scaffold.

- [ ] **Step 4: Tick `README.md`.**

- [ ] **Step 5: Commit.**

```bash
git add README.md
git commit -m "docs(routing): restore Pitwall identity in README.md

Replays Pitwall's public-facing description (F1 TUI companion: season
tracker, live timing, strategy mini-game) onto blueprint's updated
README.md. Preserves blueprint's setup/clone instructions, adapted to
the Pitwall repo URL."
```

---

### Task 16: Restore Pitwall framing in `START-HERE.md` (C12)

**Files:**
- Modify: `START-HERE.md`

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/START-HERE.md START-HERE.md | head -200`

- [ ] **Step 2: Replay Pitwall onboarding content.**

START-HERE.md is for contributor onboarding. Add Pitwall-specific onboarding (where the F1 docs live, how to run the TUI, how to seed data caches).

- [ ] **Step 3: Verify.**

Run: `grep -iE "pitwall|tui|f1" START-HERE.md | head -3`
Expected: hits.

- [ ] **Step 4: Tick `START-HERE.md`.**

- [ ] **Step 5: Commit.**

```bash
git add START-HERE.md
git commit -m "docs(routing): restore Pitwall onboarding in START-HERE.md

Replays Pitwall-specific contributor onboarding (F1 docs locations, TUI
run instructions, data cache seeding) onto blueprint's updated
START-HERE.md."
```

---

### Task 17: Reconcile `settings.json` (C13)

**Files:**
- Modify: `.claude/settings.json` (only if Pitwall has customizations)

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/.claude/settings.json .claude/settings.json`

- [ ] **Step 2: Identify Pitwall-specific customizations.**

Likely candidates: extra MCP servers added for Pitwall (e.g., a custom F1 data MCP), or `BLUEPRINT_HOOK_PROFILE` env var preference, or extra permissions for Pitwall paths.

If the diff is entirely structural (blueprint added new fields, Pitwall has no project-specific overrides): this commit is a **no-op**. Tick the checklist with that note and skip Steps 3–5.

- [ ] **Step 3: Merge Pitwall customizations into the new structure.**

Be careful with JSON. Use a tool (`jq` or your editor's JSON support) to avoid syntax errors. Validate after edit:
```bash
python3 -c "import json; json.load(open('.claude/settings.json'))" && echo OK
```
Expected: `OK`.

- [ ] **Step 4: Tick `settings.json`.**

- [ ] **Step 5: Commit (skip if no-op).**

```bash
git add .claude/settings.json
git commit -m "chore(scaffold): reconcile settings.json with Pitwall customizations

Replays Pitwall-specific MCP entries and hook-profile preferences onto
blueprint's updated settings.json."
```

---

### Task 18: Reconcile `settings.local.json` (C14)

**Files:**
- Modify: `.claude/settings.local.json` (only if Pitwall has customizations)

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/.claude/settings.local.json .claude/settings.local.json`

Note: `.claude/settings.local.json` is per-user, NOT committed (it's in `.gitignore`). So in a fresh clone scenario, this file may not even exist. If both snapshot and current are absent or empty: no-op.

- [ ] **Step 2: Replay Pitwall customizations if applicable. Validate JSON. Tick the checklist.**

- [ ] **Step 3: Commit (skip if no-op).**

```bash
git add .claude/settings.local.json
git commit -m "chore(scaffold): reconcile settings.local.json with Pitwall preferences

Replays per-user Pitwall-specific config onto blueprint's updated
settings.local.json."
```

Note: this file is gitignored by default. If you're operating in a context where it's gitignored, this commit will fail because there's nothing to commit. That's expected — skip.

---

### Task 19: Reconcile `MCP-SETUP.md` (C15)

**Files:**
- Modify: `.claude/MCP-SETUP.md`

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/.claude/MCP-SETUP.md .claude/MCP-SETUP.md | head -100`

- [ ] **Step 2: Replay any Pitwall-specific MCP setup steps.**

Likely: if Pitwall has a custom F1 MCP, instructions for installing/configuring it. If none: no-op.

- [ ] **Step 3: Verify.**

If non-no-op: ensure the new file reads cleanly end-to-end (no half-merged sections).

- [ ] **Step 4: Tick `MCP-SETUP.md`.**

- [ ] **Step 5: Commit (skip if no-op).**

```bash
git add .claude/MCP-SETUP.md
git commit -m "chore(scaffold): reconcile MCP-SETUP.md with Pitwall MCP setup

Replays Pitwall-specific MCP installation/configuration steps onto
blueprint's updated MCP-SETUP.md."
```

---

### Task 20: Reconcile `.gitignore` with Pitwall patterns (C16)

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Read snapshot vs current.**

Run: `diff .migration-scratch/pitwall-pre-resync/.gitignore .gitignore`

Pitwall's snapshot has F1-specific patterns; the new blueprint version doesn't.

- [ ] **Step 2: Add the Pitwall-specific patterns to the new `.gitignore`.**

Add this block at the end of the new `.gitignore` (after any existing entries):

```
# Pitwall runtime data caches (the data/ directory is tracked via .gitkeep)
data/*.db
data/*.sqlite
data/*.sqlite3
data/*.db-journal

# External reference repo (separately maintained, cloned alongside if needed)
faceoff/
```

(If blueprint's `.gitignore` already has `.serena/` and `.remember/`, skip those. Otherwise add them.)

- [ ] **Step 3: Verify `node_modules/` is still excluded.**

Run: `git check-ignore node_modules/`
Expected: `node_modules/`.

Run: `git check-ignore data/example.db faceoff/foo`
Expected: both paths echoed (proving the F1 patterns are active).

- [ ] **Step 4: Verify `.migration-scratch/` is still excluded.**

Run: `git check-ignore .migration-scratch/`
Expected: `.migration-scratch/`. (Critical — if this regresses, the scratch dir would get committed in Task 22's `git add -A`.)

- [ ] **Step 5: Tick `.gitignore`.**

- [ ] **Step 6: Commit.**

```bash
git add .gitignore
git commit -m "chore(scaffold): reconcile .gitignore with Pitwall patterns

Re-adds Pitwall-specific patterns (data/*.db, faceoff/) onto blueprint's
updated .gitignore. Confirms .migration-scratch/ exclusion (added in
Task 2) is still in force."
```

---

## Phase D: Finalize

### Task 21: Add ECC submodule (D1)

**Files:**
- Create: `.gitmodules` (or modify if blueprint's rsync brought one in)
- Create: `external/ecc/` (populated by submodule add)

- [ ] **Step 1: Verify blueprint's `.gitmodules` is present.**

Run: `cat .gitmodules`
Expected: shows the `[submodule "external/ecc"]` block with URL `https://github.com/affaan-m/everything-claude-code.git`.

If `.gitmodules` is missing: the rsync in Task 4 should have brought it in. Investigate before proceeding. (Possible cause: the `--exclude=external/ecc` excluded `external/` entirely, not just `external/ecc/`. Confirm with `find external -maxdepth 2`.)

- [ ] **Step 2: Initialize the submodule at the captured SHA.**

Run:
```bash
git submodule update --init --recursive
cd external/ecc
git checkout <ECC_SHA from P4>
cd ../..
git submodule status external/ecc
```
Expected: status line shows `<ECC_SHA>` at the start.

- [ ] **Step 3: Stage the submodule pointer.**

Run: `git add external/ecc`
Then: `git status --short`
Expected: `M external/ecc` (the submodule pointer is staged).

- [ ] **Step 4: Verify nothing else is staged.**

Run: `git diff --cached --name-only`
Expected: only `external/ecc`. (If you see other files, you accidentally edited something — un-stage them.)

- [ ] **Step 5: Commit.**

Run:
```bash
git commit -m "chore(scaffold): adopt ECC submodule pinned at <ECC_SHA>

Adds external/ecc as a git submodule pinned to <ECC_SHA from P4>.
Required by the new routing/registry subsystem; rebuilt in Task 22."
```
Replace `<ECC_SHA from P4>` with the actual short SHA.

---

### Task 22: Run bootstrap and rebuild registry (D2)

**Files:**
- Modify: `.claude/registry/*.json` (regenerated from current `.claude/` and ECC state)

- [ ] **Step 1: Run blueprint's bootstrap script.**

Run: `./scripts/bootstrap.sh`
Expected: prints `[bootstrap] verifying submodule...`, `[bootstrap] installing npm deps...` (or skips if `node_modules/` exists), `[bootstrap] rebuilding registries...`, `[bootstrap] complete.` No errors.

If errors: stop. Common failure modes:
- `external/ecc/README.md not found` → submodule not initialized; redo Task 21 Step 2.
- `npm install` failure → check `node` version against `package.json` engines.
- `rebuild-registry` failure → inspect script output; possibly registry validator caught a missing ROUTING.md reference.

- [ ] **Step 2: Inspect registry diff.**

Run: `git status --short .claude/registry/`
Expected: zero, one, or a few modified registry JSON files (depends on whether F1 replays affected any registered content).

- [ ] **Step 3: Stage and commit (skip commit if zero diff).**

If diff is non-empty:
```bash
git add .claude/registry/
git commit -m "chore(scaffold): rebuild registry post-replay

Runs npm run rebuild-registry to regenerate .claude/registry/ JSON
indexes that reflect the F1 content added in C2-C12 and the ECC
submodule pinned in D1. Required because the registry indexes
.claude/ content; any .claude/ edit invalidates the registry."
```

If diff is empty: skip this commit. Note in `.migration-scratch/pitwall-overlay.md` that D2 was a no-op.

---

### Task 23: Cleanup scratch directory (D3)

**Files:**
- Delete: `.migration-scratch/` (entire tree)
- Modify: `.gitignore` (remove the `.migration-scratch/` entry)

- [ ] **Step 1: Confirm all overlay checklist items are ticked.**

Run: `grep -c '\- \[x\]' .migration-scratch/pitwall-overlay.md`
Expected: at least 16 (the count of replay items). Some may be marked as no-ops with notes.

Run: `grep -c '\- \[ \]' .migration-scratch/pitwall-overlay.md`
Expected: `0` (no unchecked replay items).

If there are unchecked items: stop. Either complete them or document why they're being deferred (and add a follow-up task in `DEVELOPMENT.md` created in Task 25).

- [ ] **Step 2: Delete the scratch directory.**

Run: `rm -rf .migration-scratch`
Expected: `.migration-scratch/` no longer exists.

- [ ] **Step 3: Remove the gitignore entry.**

Edit `.gitignore` to delete the two lines added in Task 2 Step 1:
```
# Temporary migration scratch (created/deleted within a single iteration)
.migration-scratch/
```

- [ ] **Step 4: Commit.**

Run:
```bash
git add .gitignore
git commit -m "chore(migration): remove scratch directory and gitignore entry

The .migration-scratch/ directory served as the snapshot + replay-
checklist workspace during the resync. All 16 replay checklist items
were ticked before deletion. The scratch dir was never committed (it
was gitignored from Task 2 onward); removing the gitignore entry now
since the dir is gone."
```

---

## Phase E: Pitwall-specific tracking artifacts

### Task 24: Create top-level `DEVELOPMENT.md`

**Files:**
- Create: `DEVELOPMENT.md`

**Why:** The user requested a "project development.md to track progress." Blueprint's `docs/development-log.md` (adopted via rsync in Task 4) documents BLUEPRINT's history. Pitwall needs its own top-level progress tracker that's high-visibility (root-level, not buried in `docs/`).

- [ ] **Step 1: Create the file with this content.**

Create `DEVELOPMENT.md` at the repo root:

````markdown
# Pitwall — Development Log

> **High-level project progress tracker.** Updated when iterations start, gate, or land. For per-iteration spec/plan detail, see `docs/superpowers/{specs,plans}/`. For development *principles*, see `docs/development-philosophy.md`. For the inherited scaffold history, see `docs/development-log.md`.

---

## Current state (as of YYYY-MM-DD)

- **Branch:** `main`
- **Most recent merge:** *(set after first PR merge)*
- **In-flight iteration:** *(name of current `build/workflows/NN-<slug>/` or "none")*
- **Cycle count (out of 5):** *(N/5; bumps each `review-N.md` written)*
- **Blockers:** *(any verification gate currently failing, or "none")*

## Verification gate status (current iteration)

| Gate | Pass / Fail / N/A | Last checked |
|---|---|---|
| Bootstrap script (`./scripts/bootstrap.sh` exits 0) | | |
| Registry rebuild succeeds | | |
| All 5 hooks execute without error | | |
| Portability hook rejects synthetic F1-term-in-rules edit | | |
| TDD hook rejects new-code-without-test commit | | |
| F1 reference content present (grep verification) | | |
| Portability discipline preserved (no F1 terms in rules/skills) | | |

---

## Iteration history (newest first)

### Iteration 1: Resync scaffold with workspace-blueprint
- **Status:** *(in-progress | merged | reverted)*
- **Branch:** `chore/blueprint-resync`
- **Spec:** [`docs/superpowers/specs/2026-05-12-blueprint-resync-design.md`](docs/superpowers/specs/2026-05-12-blueprint-resync-design.md)
- **Adversary review:** [`docs/superpowers/specs/2026-05-12-blueprint-resync-adversary-review.md`](docs/superpowers/specs/2026-05-12-blueprint-resync-adversary-review.md)
- **Plan:** [`docs/superpowers/plans/2026-05-12-blueprint-resync-plan.md`](docs/superpowers/plans/2026-05-12-blueprint-resync-plan.md)
- **PR:** *(URL after `gh pr create`)*
- **Started:** 2026-05-12
- **Merged:** *(date)*
- **Commits in branch:** *(count after merge; target: 22)*
- **Cycles consumed:** *(N/5)*
- **What landed:** routing/registry subsystem, ECC submodule, multi-IDE preambles (AGENTS.md/GEMINI.md/.cursorrules), npm tooling, scripts/, 4 new skills, 2 new rules, tests/, .github/workflows/, blueprint's living docs. F1 content + Pitwall identity preserved.
- **What did not land:** wiring new skills into Pitwall workflows (deferred), GitHub Actions behavior tuning (deferred), docs/explorations/ format migration if needed (deferred).

### Iteration 0: Initial scaffold
- **Status:** merged
- **Commit:** `ce97dd9`
- **What landed:** initial scaffold from workspace-blueprint, Pitwall identity customization (`dd7d0f3`), planning seed including OpenF1 lab spike (`ab3b834`), consolidated Pitwall design spec v0.1→v1.0 (`64207c9`), v0.1 season tracker plan (`7c58a34`).

---

## Active follow-ups

*(Lightweight backlog. Promote each item to its own `build/workflows/NN-<slug>/` iteration when prioritized.)*

- [ ] Wire `brainstorming` / `writing-plans` / `systematic-debugging` skills into the Pitwall iteration workflow (defines the first task an implementer reaches for in each iteration type).
- [ ] Tune `.github/workflows/` for Pitwall-specific CI (Python tests, lint, type check on `src/pitwall/`).
- [ ] Start `build/workflows/01-<slug>/` for the v0.1 season tracker per the existing plan.

---

## How to update this file

- After every PR merge, add an entry under "Iteration history" with the merged commits, what landed, what didn't.
- During an active iteration, keep "Verification gate status" current (re-run gates after each cycle, mark pass/fail).
- "Active follow-ups" is the lightweight backlog — promote items to formal iterations when ready.
- Don't put detail here that belongs in a spec or plan — link to those instead.

````

- [ ] **Step 2: Verify it renders.**

Run: `head -30 DEVELOPMENT.md`
Expected: the title and the "Current state" section visible.

- [ ] **Step 3: Commit.**

Run:
```bash
git add DEVELOPMENT.md
git commit -m "docs: add top-level DEVELOPMENT.md for Pitwall progress tracking

High-visibility progress tracker at repo root. Distinct from blueprint's
docs/development-log.md (which tracks scaffold evolution) — this one is
Pitwall-specific: current iteration, verification gate status, iteration
history, lightweight follow-up backlog."
```

---

### Task 25: Create `docs/development-philosophy.md`

**Files:**
- Create: `docs/development-philosophy.md`

**Why:** The user asked for "dev philosophies to save us time by writing once and checking twice." This file codifies the principles already embodied (but not explicitly stated) by the scaffold's rules + skills + hook system.

- [ ] **Step 1: Create the file with this content.**

````markdown
# Development Philosophy

> Principles that govern how we work in this repo. Most are already enforced by `.claude/rules/`, `.claude/hooks/`, or the four-agent loop. This file is the *explicit* statement of the *implicit* discipline, so a new contributor can read it once and operate consistently.

## Measure twice, cut once

**Write the spec before the code. Write the verification before doing the work.**

- Every iteration starts with a spec (`01-spec/SPEC.md` for builds; `docs/superpowers/specs/` for cross-cutting designs). Implementers receive a spec; they do not invent one.
- Every spec has explicit, verifiable success criteria. "Make it work" is not a success criterion. "`./scripts/bootstrap.sh` exits 0" is.
- For destructive operations (migrations, deletions, force-pushes): dry-run first, eyeball the output, then do it for real.
- For replace-and-replay operations: snapshot the pre-state into a scratch directory before the replace, so the replay has a source of truth.

## Reversibility over speed

**Prefer the action that's easy to undo.**

- Branch first, commit second. `git branch -D` an unmerged branch is reversible; reverting a merged commit is two more commits of churn.
- New commits over `--amend` on pushed commits. Amend only locally before pushing.
- Never `--no-verify`. The hook is telling you something real. If it's wrong, fix the hook.
- For changes affecting shared state (push, PR, gh actions): pause and confirm before executing.

## One logical change per commit

**Each commit is a unit of revertibility.**

- A commit that mixes a feature, a refactor, and a typo fix can't be cleanly reverted if any of the three turns out wrong.
- Conventional Commits format (`feat(scope): ...`, `fix: ...`, `chore: ...`) — see `.claude/rules/commit-discipline.md`.
- Per-file commits when reasonable. Per-concept commits when granularity would over-fragment.
- Mega-commits ("everything from blueprint") are allowed *only* when reviewing the diff is impractical anyway — and only when the spec calls them out.

## TDD where TDD applies; checklist where it doesn't

**Production code: tests first. Migrations and scaffolding: checklists first.**

- For application code in `src/pitwall/`: red → green → refactor. The pre-commit-tdd hook enforces this. See `.claude/rules/testing-discipline.md` and `.claude/skills/tdd-loop/`.
- For migrations, scaffolding, and one-off operations: write the verification gates before the operation. Tick them as they pass. See the resync plan for the template.
- For exploratory spikes in `lab/`: no test discipline required; the spike's `REPORT.md` is the deliverable. See `.claude/skills/spike-protocol/`.
- For bug fixes: write a failing test that reproduces the bug, *then* fix it. See `.claude/skills/bug-investigation/`.

## Reviewer + adversary on every build iteration

**Two failure modes, two reviewers.**

- The reviewer (`.claude/agents/reviewer-agent.md`) checks compliance with the spec — "did you do the right thing?"
- The adversary (`.claude/agents/adversary-agent.md`) checks for things the spec didn't anticipate — "did you do the right thing in a way that breaks under conditions you didn't think about?"
- Both run on every cycle. After 5 failed cycles, the orchestrator halts and escalates — the spec is likely wrong. See `.claude/rules/review-discipline.md`.

## Portability discipline

**This scaffold is portable. Project-specific facts go in `.claude/reference/`, never in `.claude/rules/` or `.claude/skills/`.**

- New project-specific terms go in `.claude/.portability-deny.txt`. The `enforce-portability.sh` hook blocks edits that drag those terms into rules or skills.
- This rule exists so the scaffold can be lifted into the next project. It's not aesthetic — it's *load-bearing*. Bootstrap recipe in `docs/teaching/bootstrap.md`.

## Token discipline

**Each workspace is siloed. Don't load everything.**

- Working in `build/`? Load `build/CONTEXT.md`, the iteration's spec, the relevant agent files. Skip `spec/`, `lab/`, `ship/` CONTEXT.md.
- Working in `lab/`? Load `lab/CONTEXT.md` + the spike-protocol skill. Skip everything else.
- The "What to Load / Skip These" tables in each workspace's CONTEXT.md are the token budget.

## When to ask vs when to act

**Reversible local actions: act. Hard-to-reverse or shared-state actions: ask.**

- Freely: editing files, running tests, local commits on a feature branch.
- Ask first: pushing to remote, opening PRs, force-pushing, modifying CI, sending external messages, deleting branches, dropping data.
- "I once approved X" does not generalize to "always approve X" — match each action's scope to what was actually requested.

## What this file is NOT

- Not a checklist. Checklists are per-iteration, in the relevant plan.
- Not a substitute for the rules. The rules are the enforcement layer. This is the *narrative*.
- Not exhaustive. New principles get added here when a misstep would have been prevented by stating them. If the rule was already enforced by a hook, don't add it here.

````

- [ ] **Step 2: Verify it renders.**

Run: `head -20 docs/development-philosophy.md`
Expected: title + "Measure twice, cut once" section visible.

- [ ] **Step 3: Commit.**

Run:
```bash
git add docs/development-philosophy.md
git commit -m "docs: codify development philosophy

Distills the principles already enforced by .claude/rules/ + .claude/hooks/
+ the four-agent loop into an explicit narrative. Lets a new contributor
read once and operate consistently. Key principles: measure twice cut once,
reversibility over speed, one logical change per commit, TDD where it
applies / checklist where it doesn't, reviewer+adversary every cycle,
portability discipline, token discipline."
```

---

### Task 26: Update `DEVELOPMENT.md` with completed iteration state

**Files:**
- Modify: `DEVELOPMENT.md`

**Why:** Task 24 created the file with placeholders for "in-flight" state. Now that the resync is essentially complete (only verification + PR remaining), fill in the iteration history concretely.

- [ ] **Step 1: Update the "Current state" section.**

Edit `DEVELOPMENT.md`:
- Replace `(as of YYYY-MM-DD)` with today's date.
- Replace `In-flight iteration: ...` with `Iteration 1: Resync scaffold with workspace-blueprint`.
- Set `Cycle count` to `1/5`.
- Set `Blockers` to `none` (assuming verification gates will pass; if not, fill them in after Task 27 fails).

- [ ] **Step 2: Update the "Verification gate status" table.**

Fill the table with the actual gate results once Task 27 runs. (At this point, leave it blank; come back after Task 27.)

- [ ] **Step 3: Update "Iteration 1" history entry.**

- Set `Status` to `in-progress`.
- Fill in `Started: 2026-05-12`.

- [ ] **Step 4: Commit.**

Run:
```bash
git add DEVELOPMENT.md
git commit -m "docs: log iteration 1 (blueprint resync) in DEVELOPMENT.md

Records the in-flight resync as iteration 1: branch, spec/plan/adversary
links, cycle count, status. Will be updated after verification and merge."
```

---

## Phase F: Verification and PR

### Task 27: Verification gate

**Files:**
- No file modifications — verification only.

Walk through the 16 success criteria in Section 4 of the spec. Each is pass/fail. **Do not proceed to Task 28 if any gate fails.** Fix-in-place on the branch; re-run.

- [ ] **Gate 1: `./scripts/bootstrap.sh` exits 0.**

Run: `./scripts/bootstrap.sh; echo "exit=$?"`
Expected: `exit=0`.

- [ ] **Gate 2: `npm run rebuild-registry` exits 0.**

Run: `npm run rebuild-registry; echo "exit=$?"`
Expected: `exit=0`.

- [ ] **Gate 3: ROUTING.md → registry resolution.**

Inspect `scripts/bootstrap.sh` for the validation step. It is the step that "Validates that every name referenced in `ROUTING.md` resolves to a registry entry" per blueprint README. Confirm Gate 1 already covered this; if a separate command exists (e.g., `node scripts/route.mjs --validate`), run it.

- [ ] **Gate 4: All 5 hooks execute without error on synthetic edits.**

For each of the 5 hooks, run it with a representative argument. Many hooks are designed to be invoked by Claude Code's tool-call lifecycle, so direct invocation may need a dummy input. At minimum confirm `bash -n` (syntax-only) parses each:

```bash
for h in .claude/hooks/*.sh; do
  bash -n "$h" && echo "OK: $h" || echo "FAIL: $h"
done
```
Expected: all 5 print `OK`.

- [ ] **Gate 5: Portability hook rejects synthetic F1-term-in-rules edit.**

Create a temp file containing an F1 term and run the hook against it. The exact invocation depends on the hook's interface — check the script's top comment. Common pattern: pipe the would-be diff to the hook. Loose example:
```bash
echo 'this rule mentions fastf1' > /tmp/synthetic-rule.md
bash .claude/hooks/enforce-portability.sh /tmp/synthetic-rule.md && echo "GATE FAIL: hook should have rejected"
rm /tmp/synthetic-rule.md
```
Expected: the hook returns non-zero AND/OR prints a rejection message. If it passes silently, the deny list isn't wired correctly — investigate.

- [ ] **Gate 6: TDD hook rejects new-code-without-test commit.**

Same idea: invoke `pre-commit-tdd.sh` against a synthetic staged-diff where a new `.py` file is added with no corresponding `test_*.py`. Confirm it rejects.

- [ ] **Gate 7-10: Pitwall-exclusive content untouched.**

Run:
```bash
for path in src/pitwall data shared lab/01-openf1-feed-eval; do
  git diff main -- "$path" | head -5
done
```
Expected: each `git diff` produces NO output (the directories are byte-identical between `main` and the branch).

- [ ] **Gate 11: F1 reference content present.**

Run: `grep -rE "fastf1|openf1|jolpica" .claude/reference/`
Expected: at least 3 hits across the 7 reference files.

- [ ] **Gate 12: Portability preserved (no F1 in rules/skills outside vendored).**

Run: `grep -rE "fastf1|openf1|jolpica|pitwall|formula 1" .claude/rules/ .claude/skills/ | grep -v ".claude/skills/docx\|.claude/skills/pptx\|.claude/skills/xlsx\|.claude/skills/pdf"`
Expected: ZERO matches. (Office skills under docx/pptx/xlsx/pdf are vendored from `anthropics/skills` and may legitimately contain unrelated terms — they're excluded from the check.)

- [ ] **Gate 13: F1 checklist 100% ticked.**

Already verified in Task 23 Step 1.

- [ ] **Gate 14: Pitwall dev customizations preserved.**

Same checklist. Already verified.

- [ ] **Gate 15: 22 commits in `main..chore/blueprint-resync`.**

Run: `git log main..chore/blueprint-resync --oneline | wc -l`
Expected: roughly 22 (some C7/C8/C13–C15 may have been dropped as no-ops; count may be 17–22).

If wildly off (e.g., 5 or 50): investigate.

- [ ] **Gate 16: Verify nothing accidentally squashed.**

Run: `git log main..chore/blueprint-resync --oneline`
Expected: each commit's subject is one of the expected commit messages (per the plan). No commit subject mentions multiple unrelated changes.

- [ ] **Update DEVELOPMENT.md with gate results.**

Edit the "Verification gate status" table in `DEVELOPMENT.md`. Fill in pass/fail for each gate. Commit:
```bash
git add DEVELOPMENT.md
git commit -m "docs: record verification gate results for iteration 1"
```

---

### Task 28: Push and open PR

**Files:**
- No file modifications — pushing branch and opening PR.

- [ ] **Step 1: Confirm we're on the resync branch.**

Run: `git rev-parse --abbrev-ref HEAD`
Expected: `chore/blueprint-resync`.

- [ ] **Step 2: Confirm working tree is clean.**

Run: `git status --short`
Expected: empty.

- [ ] **Step 3: Push the branch.**

Run: `git push -u origin chore/blueprint-resync`
Expected: branch published; no force-push required (we haven't rewritten history).

- [ ] **Step 4: Open the PR.**

Run:
```bash
gh pr create --title "chore: resync scaffold with workspace-blueprint" --body "$(cat <<'EOF'
## Summary

Brings Pitwall's scaffold up to current `workspace-blueprint` state. F1 domain content and Pitwall-specific software-dev customizations preserved. 22-ish commits land on `main` as a merge commit (not squash) — the per-step history is the audit trail.

## What this brings in
- Routing/registry layer (`ROUTING.md`, `.claude/routing/`, `.claude/registry/`, `route-inject.sh`)
- ECC submodule (`external/ecc/`, pinned)
- Multi-IDE preambles (`AGENTS.md`, `GEMINI.md`, `.cursorrules`, `.agents/`, `.codex/`, `.superpowers/`)
- Node tooling (`package.json`, `scripts/`)
- 4 new skills (`brainstorming`, `karpathy-guidelines`, `systematic-debugging`, `writing-plans`)
- 2 new rules (`nasa-power-of-10.md`, `unix-philosophy.md`)
- `tests/`, `.github/workflows/`, blueprint's living docs

## What this preserves
- All F1 domain content (data/, src/pitwall/, shared/, lab/01-openf1-feed-eval/, F1 facts in `.claude/reference/`, F1 deny terms)
- All Pitwall identity (CLAUDE.md, README.md, START-HERE.md, CONTEXT.md, briefs, design specs)
- Pitwall git history (no remote/merge across unrelated histories; no clean-room copy)

## Verification

All 16 success criteria in [spec Section 4](docs/superpowers/specs/2026-05-12-blueprint-resync-design.md) passed locally. Gate results recorded in `DEVELOPMENT.md`.

## Mechanic

Single wholesale `rsync -avc` overlay (B1), then 15 purely additive replay commits (C1–C16) for shared files, then submodule + registry rebuild (D1, D2), scratch cleanup (D3), plus 3 Pitwall-specific artifacts: `DEVELOPMENT.md`, `docs/development-philosophy.md`, gate-results update. Detailed plan: [`docs/superpowers/plans/2026-05-12-blueprint-resync-plan.md`](docs/superpowers/plans/2026-05-12-blueprint-resync-plan.md).

## Merge strategy

**Use a merge commit, NOT squash.** The per-step history is the audit trail.

## Test plan
- [ ] Reviewer runs `./scripts/bootstrap.sh` on a fresh clone of the merged result — exits 0
- [ ] Reviewer runs `npm run rebuild-registry` — exits 0
- [ ] Reviewer spot-checks 3 F1 reference files — F1 facts present
- [ ] Reviewer spot-checks `.claude/rules/` and non-vendored `.claude/skills/` — no F1 terms
EOF
)"
```
Expected: gh prints the PR URL. Record the URL.

- [ ] **Step 5: Update `DEVELOPMENT.md` with PR URL.**

Edit `DEVELOPMENT.md`, fill in the "PR:" field under Iteration 1.

Run:
```bash
git add DEVELOPMENT.md
git commit -m "docs: record PR URL in DEVELOPMENT.md"
git push
```

- [ ] **Step 6: Hand off.**

Reply to the user: PR URL, summary of gates passed, any deferred items. Stop. The user (or a human reviewer) does the merge.

---

## Rollback paths

- **Failure during Task 1-26 (pre-PR):** Branch is throwaway.
  ```bash
  git checkout main
  git branch -D chore/blueprint-resync
  # If npm install left node_modules/, optionally rm -rf node_modules
  # If submodule was initialized, optionally rm -rf external/ecc
  ```
  `main` is untouched.

- **Failure during Task 27 (verification):** Fix-in-place on the branch. Add a new commit with the fix. Re-run the failed gate. Do not amend prior commits unless they were never pushed.

- **Failure post-merge:** `git revert -m 1 <merge-sha>` reverts the entire resync atomically. F1 content is restorable from the revert's parent.

---

## Self-review (run after writing this plan)

**Spec coverage:** Walked through spec Section 5.3 (overlay commits): A1 → Task 2 ✓, A2 → Task 3 ✓, B1 → Task 4 ✓, C1 → Task 5 ✓, C2–C8 → Tasks 6–12 ✓, C9–C12 → Tasks 13–16 ✓, C13–C15 → Tasks 17–19 ✓, C16 → Task 20 ✓, D1 → Task 21 ✓, D2 → Task 22 ✓, D3 → Task 23 ✓. Spec Section 4 (success criteria) → Task 27 ✓. Spec Section 5.5 (PR + merge) → Task 28 ✓. Plus Tasks 24–26 cover the user's add-on asks (DEVELOPMENT.md, philosophy, tracking).

**Placeholder scan:** Searched for "TBD", "TODO", "implement later", "add appropriate". Found zero literal placeholders. Tasks 11, 12, 17, 18, 19 have "no-op if X" branches with concrete commit-skip conditions — those are decision points, not placeholders.

**Type consistency:** No types involved (no production code in this iteration). Cross-references (`<BLUEPRINT_SHA from P3>`, `<ECC_SHA from P4>`) are consistent across tasks where they appear (Task 4 and Task 21 both reference them with the same variable name).

**Style consistency:** Every task has Files / Steps / Commit pattern. Every commit message follows Conventional Commits per `.claude/rules/commit-discipline.md`. Every verification step has an explicit expected output.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-12-blueprint-resync-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. Best for this plan because Tasks 4 (wholesale rsync) and Task 27 (verification gate) are isolated and benefit from a clean context.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints. Best if you want to watch each step interactively.

**Which approach?**
