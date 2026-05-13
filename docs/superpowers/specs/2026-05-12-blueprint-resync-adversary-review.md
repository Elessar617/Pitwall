---
findings: critical
reviewing: docs/superpowers/specs/2026-05-12-blueprint-resync-design.md
proposed-alternative: "Copy blueprint as base, run setup, then systematically migrate F1 in"
date: 2026-05-12
---

# Adversary review: "blueprint-as-base" alternative

The user proposed replacing the spec's "feature branch in Pitwall, overlay + replay" approach with: copy the blueprint repo, run setup, then systematically migrate F1 content in.

The proposal is reasonable on its face. It also has **three critical defects** that, unaddressed, will lose work. Below I steelman the proposal, then attack it.

## What's right about the alternative

- Avoids the spec's psychologically uncomfortable "intentionally lose Pitwall content in commit C7, restore in C8" sequence.
- The final tree-state is the same as Approach A's, file-for-file (for shared files). The difference is purely commit ordering and which file is treated as the "base."
- For an *appropriately empty* Pitwall, this is genuinely the simplest mental model: "blueprint with our F1 stuff on top."
- Lets you run blueprint's verification (`bootstrap.sh`, registry rebuild, hook self-tests) on a known-clean tree before mixing in F1 content. Approach A only verifies at the end.

I have to give the alternative its due: as a *clean-room* operation in a new directory, it's clearer than the overlay approach.

## What's wrong with it

### Critical 1: "Copy the repo" is mechanically ambiguous — every interpretation loses something

The phrase has at least three meanings:

| Interpretation | Loses | Notes |
|---|---|---|
| `cp -r blueprint pitwall-new/` (filesystem copy) | **All of Pitwall's git history** (6 commits including `ab3b834` openf1 spike, `64207c9` design spec, `d00da80` this resync spec) | The most literal reading. The new dir has blueprint's `.git`. Pitwall's commits are orphaned in the old dir. |
| `git clone blueprint pitwall-new/` then drop F1 files in | All of Pitwall's git history | Same problem as above, dressed up. |
| `git remote add blueprint` + `git merge --allow-unrelated-histories` | Nothing technically, but forces conflict resolution across two unrelated trees | This is **option B from the original brainstorming**, which you explicitly rejected. |
| `rsync -a blueprint/ pitwall/ --exclude=.git` (overlay onto Pitwall) | Files Pitwall has but rsync didn't include — i.e., nothing if `--delete` is omitted | This is **literally Approach A in a single command**. Not actually a different approach; just a different commit shape. |

**The user must specify which.** Without specification, "copy the repo" defaults to the first interpretation, which loses 5 of 6 Pitwall commits including this spec, the openf1 spike, and the Pitwall design.

### Critical 2: Default-lose vs default-keep — safety inversion

Approach A starts from Pitwall as the base. Anything in Pitwall I forgot to enumerate in the migration plan **survives by default**. Worst case: an extra file lingers.

Approach B starts from blueprint as the base. Anything in Pitwall I forgot to enumerate **is lost by default**. Worst case: missing F1 content discovered weeks later when the registry rebuild silently omits something.

For an empty project this asymmetry is small. For Pitwall right now it's contained but real. The Pitwall-exclusive content surface I verified:

- `lab/01-openf1-feed-eval/` (28 KB — REPORT.md, PREFLIGHT.md, VERIFY.md, prototype/)
- `spec/briefs/pitwall-overview.md`
- `spec/CONTEXT.md` (might be customized vs. blueprint)
- `docs/superpowers/specs/2026-05-11-pitwall-design.md`
- `docs/superpowers/specs/2026-05-12-blueprint-resync-design.md` (this spec)
- `docs/superpowers/plans/2026-05-11-pitwall-v01-season-tracker.md`
- `docs/teaching/bootstrap.md`
- `data/telemetry.db` and `data/.gitkeep`
- `shared/README.md`
- F1 facts inside 7 differing `.claude/reference/*.md` files
- 32 F1 deny terms in `.claude/.portability-deny.txt`
- F1 framing inside `CLAUDE.md`, `CONTEXT.md`, `README.md`, `START-HERE.md`

That list is the minimum. If I missed something during this audit, Approach B silently drops it. Approach A preserves it whether I enumerated it or not.

(`src/pitwall/` is currently an empty directory and `faceoff/` is gitignored — neither is a concern for either approach, but worth confirming.)

### Critical 3: The spec we just committed dies if you "copy the repo"

You said "track and save changes with git" and we just committed `docs/superpowers/specs/2026-05-12-blueprint-resync-design.md` at `d00da80`. Under interpretation 1 of "copy the repo," this commit is dropped. The migration's own audit trail dies in the migration.

This is the worst kind of failure: silently caused by the very plan we're trying to enact.

### Significant 4: "Run setup first, then migrate F1" interacts badly with two hooks

After `bootstrap.sh` runs in the new tree:

- `enforce-portability.sh` is live. The deny-list is blueprint's base (no F1 terms). If F1 migration touches a `.claude/skills/` or `.claude/rules/` file before updating the deny list, the hook either blocks the edit or — worse, depending on direction — passes content it should have blocked, because the F1 terms aren't in the deny list yet.
- `pre-commit-tdd.sh` enforces "test file before code file" at commit time. If F1 migration includes any code-style file, the hook may reject the commit, requiring an out-of-order test scaffold to land first.

**Same risks exist in Approach A**, but Approach A's spec sequences the deny-list restore (C6) before any further F1 content edits. The alternative as stated doesn't sequence these dependencies.

### Significant 5: Registry depends on `.claude/reference/` content

`bootstrap.sh` runs `npm run rebuild-registry` after submodule init. The registry indexes `.claude/` content. If you then migrate F1 facts INTO `.claude/reference/*.md`, the registry is out of date with the migrated state — you have to rebuild it again post-migration. The "run setup first" sequencing implies a single bootstrap, but you need two: once after blueprint copy, once after F1 migration. Approach A faces the same issue but its verification phase (Section 5.4) is positioned after replay, so the rebuild lands at the right moment.

### Significant 6: Granularity of commits is harder to defend

The spec's stated success criterion #15 is "21 commits — one logical change per commit." Approach B can hit this number, but the commits split unnaturally:

- "Initial blueprint state" is one commit of ~150 files.
- "Add F1 lab spike" is one commit.
- "Add F1 facts to tech-stack.md" is one commit.
- etc.

Reviewers reading `git log` see commit #1 as a massive un-reviewable blob ("everything from blueprint") and then 20 small commits adding F1 stuff. Approach A's commits are each individually reviewable diffs against the previous state.

### Moderate 7: The C4/C7 "intentionally lose then restore" pattern is fixable WITHOUT switching approaches

The user's discomfort with Approach A appears to be the C4/C7 commits that show "loss of F1 content" in the intermediate state. Two ways to address it without switching to Approach B:

**Option α:** Combine C4+C5 into a single commit `chore(reference): adopt blueprint structure with F1 facts merged in`. Loses the "clean diff for reviewers" property but eliminates the lossy intermediate state. Same for C7+C8.

**Option β:** Reverse the order: C5 first (extract F1 facts to a separate scratch file), C4 second (overwrite reference files), C5' third (re-introduce F1 facts onto blueprint base). This is exactly Approach B applied per-file. Approach B at a per-file granularity = Option β at the spec level. They're isomorphic.

This suggests the question isn't "A vs B" — it's whether you want the intermediate "blueprint-without-F1" state to ever exist on the branch. Reasonable people can want it (clean review diffs) or not want it (no temporary loss state).

### Minor 8: Disk / time cost

`du -sh` blueprint excluding `.git` and `node_modules` is probably <20 MB. Negligible either way.

### Minor 9: Pitwall's `.git/` already has hooks installed

After commits, Pitwall's `.git/hooks/` may have pre-commit / pre-push hooks installed locally. A fresh blueprint clone wouldn't. Both approaches need to verify hook installation post-migration. Approach A inherits Pitwall's `.git/hooks/` state for free; Approach B has to re-install them.

## Verdict

The alternative is not safe as stated. It can be made safe with three modifications:

1. **Specify the mechanic.** "Copy the repo" must become "rsync blueprint files onto the Pitwall branch with `--exclude=.git --exclude=node_modules`." That is mechanically Approach A with a different opening commit.
2. **Preserve Pitwall git history.** Stay on Pitwall's branch. Never `cp -r` blueprint into a separate dir as the new home.
3. **Sequence the dependencies.** Update the deny list BEFORE any F1 content lands in shared files. Rebuild the registry AFTER F1 migration, not just after bootstrap.

If you accept those three modifications, what you have is **Approach A with a different opening commit ordering** — specifically, swap Phase B and the early commits of Phase C, so the blueprint base lands as a single "wholesale overlay" commit, then F1 content lands additively on top.

I recommend the following adjustment to the original spec:

### Adjusted overlay sequence (compatible with the user's stated preference)

Replace Phase B + Phase C as currently spec'd with:

- **A1** snapshot (unchanged).
- **B0** `chore(scaffold): wholesale overlay of blueprint files (no F1 content overwritten)` — single rsync commit. `rsync -a /path/to/blueprint/ ./ --exclude=.git --exclude=node_modules --exclude=external/ecc/.git`. Result: tree contains union of (blueprint files) + (Pitwall-exclusive dirs untouched). Shared files now show blueprint's content; F1 content in those shared files is gone from this commit's state.
- **C-merged-1** through **C-merged-N** — per-file F1-facts replay commits. Same as the original C5+C6+C8+P merged into per-file scope: `docs(reference): replay F1 facts into tech-stack.md`, etc. One commit per shared file restored.
- **B8 alt** `chore(scaffold): adopt ECC submodule` — separate commit because `git submodule add` writes `.gitmodules` and we want that traceable.
- **D1** cleanup (unchanged).

Total commit count: roughly the same (20-22). Difference: the "wholesale overlay" lands as one big commit (reviewers can verify via `diff -r` against blueprint) rather than as 11 small ones. Subsequent commits are then purely additive F1 replays — no more "intentionally lose then restore" sequence.

This is, I think, what the user actually wants: blueprint-base in one move, then F1 added back additively, without ever moving repos.

## Findings: CRITICAL

Block the migration as currently spec'd (Approach A unmodified) AND as proposed verbally (Approach B unmodified). Adopt either:

- Approach A with the C4/C5 and C7/C8 pairs combined (Option α above), OR
- The adjusted sequence described in this review (single wholesale-overlay commit, then additive F1 replays).

Both preserve git history, both avoid the lossy intermediate state, both keep the per-commit reviewability for the F1 replay phase. The user's verbal proposal needs the modifications above to be safe.
