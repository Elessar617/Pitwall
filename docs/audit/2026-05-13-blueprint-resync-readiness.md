# Blueprint Resync Readiness Review

**Date:** 2026-05-13
**Branch:** `chore/blueprint-resync`
**Base reviewed:** `7c58a34d6890c360014d8908161c6c8bff9145a3`
**Head reviewed before fixes:** `2027aa790e17b1266ba82cb747764465575deccb`

## Verdict

Ready to proceed with development after the corrective commit from this review lands.

The migration successfully brought in the routing/registry layer, ECC submodule, hooks, CI, Node tooling, multi-IDE preambles, and the new scaffold rules/skills while preserving Pitwall's F1 reference content. The review found two blocking issues in the branch as-reviewed and fixed both in-place before final verification.

## Findings

### Critical: runtime data cache was tracked

`data/telemetry.db` was an empty tracked file on the branch, and `.gitignore` no longer ignored `data/*.db`. That violated the spec's gate that `data/` stay untouched, and it would have made future runtime caches easy to commit by accident.

Resolution: removed the tracked empty DB and restored the `data/*.db`, `data/*.sqlite`, `data/*.sqlite3`, and `data/*.db-journal` ignore rules.

### Critical: migrated CI test suite was not green

`npm test` failed in `tests/unit/source-of-truth.test.mjs`. One assertion caught a stale README skill-count line. The other was a blueprint-specific "published surface" guard that rejected `docs/teaching`/Clief markers, but Pitwall intentionally tracks scaffold teaching material inherited before this resync.

Resolution: added the README skill-count line expected by the source-of-truth guard, and replaced the blueprint-specific marker grep with a Pitwall-relevant guard that generated local state (`.agents/`, `.codex/`, `.serena/`, `.remember/`, `.migration-scratch/`, `node_modules/`) stays untracked.

### Minor: hook count drift in human docs

Human-facing docs still said four hooks after `route-inject.sh` made the actual count five.

Resolution: updated `CLAUDE.md`, `START-HERE.md`, and `docs/development-log.md`.

### Process note: branch count differs from the original estimate

The original spec expected 22 implementation commits. The branch has 27 commits from `main` at readiness because it also contains the design/adversary/spec-plan commits and this post-review corrective commit. I do not treat this as a merge blocker because the commits remain logically separated and reviewable.

## Adversary Notes

The main regression vector was source-repo policy leaking into the consumer repo: copied scaffold tests and docs must be checked for assumptions about what belongs only in `workspace-blueprint`. The second vector was ignored-file drift after the wholesale overlay: tracked empty files are especially easy to miss because they produce no line diff.

## Verification

- `npm test` passes: 50 unit tests, 2 hook tests, and integration tests.
- `./scripts/bootstrap.sh` exits 0.
- `npm run rebuild-registry` exits 0 and validates all 7 routing files.
- All five hook scripts pass `bash -n`.
- Runtime cache ignore checks pass for `data/*.db`, `data/*.sqlite`, `data/*.sqlite3`, and `data/*.db-journal`.
- F1 reference content is present under `.claude/reference/`.
- Portability grep returns no F1/Pitwall hits under non-office `.claude/rules` and `.claude/skills`.

## Remaining Follow-Ups

- The private `package.json` still uses the blueprint package name. It is not blocking because the package is private and only drives scaffold tooling, but renaming it to a Pitwall-specific tooling package would reduce confusion in `npm` output.
