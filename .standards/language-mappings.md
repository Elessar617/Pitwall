<!-- Generated from standards/manifest.json by standards/manage.py; do not edit. -->

# Language Mappings — Enforcing Rules per Toolchain

Standards version: 2.0.0 (2026-07-10)

Each mapping is independently normative and keeps its own stable ID, parent-rule lineage, applicability, verifier, and waiver policy.

## All

### M-ALL-01 MUST · Style is owned by the formatter
**Parent rules:** U10, U15
**Mapping:** One auto-formatter per language, its config committed, run by hook on every edit (U10, U15). Numeric style trivia (line length, quote style) is repo-local formatter config, not universal law — no manual style debates.
**Applies:** all codebases and languages.
**Verify (command):** The committed formatter configuration and edit or commit hook run the selected formatter.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

## Python

### M-PYTHON-01 MUST · Format (U15)
**Parent rules:** U15
**Mapping:** `ruff format`, config committed in `pyproject.toml`
**Applies:** Python code
**Verify (command):** Run `ruff format --check` with the committed configuration.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-PYTHON-02 MUST · Lint (U1, U5, U7, U8, U10)
**Parent rules:** U1, U5, U7, U8, U10
**Mapping:** `ruff check`; committed `[tool.ruff.lint]` selection includes the house baseline `YTT,S,B,A,C4,T10,SIM,I,C90,E,W,F,PGH,UP,RUF,TRY` plus `ANN`, `PYI`, and `BLE`. `ANN` enforces function-signature annotations, `PYI` enforces stub-file rules, and `BLE` provides `BLE001` for broad exception catches; tests may waive `S101`; every `# noqa` names a rule code and carries a reason or valid waiver reference (U10).
**Applies:** Python code
**Verify (lint):** Inspect committed `[tool.ruff.lint]` `select` for `ANN`, `PYI`, and `BLE`, then run `ruff check`; reject any `# noqa` without a rule code and a reason or valid waiver reference.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-PYTHON-03 MUST · Types (U5, U10)
**Parent rules:** U5, U10
**Mapping:** `ty check` performs type analysis but does not report missing type annotations; Ruff `ANN` enforces function-signature annotations and Ruff `PYI` enforces stub-file rules; `mypy --strict` or a committed equivalent pyright configuration is an acceptable alternate type analyzer.
**Applies:** Python code
**Verify (command):** Inspect the committed Ruff selection for `ANN` and `PYI`; run `ruff check` for annotations and stubs, then run `ty check` or the committed alternate for type analysis.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-PYTHON-04 MUST · Boundary guards (U5)
**Parent rules:** U5
**Mapping:** Pydantic/dataclass validation at entry points; **no bare `assert` on prod paths** — `python -O` strips them; raise real errors
**Applies:** Python code
**Verify (test):** Run boundary tests and scan production paths for bare `assert` statements.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-PYTHON-05 MUST · Immutability (U6)
**Parent rules:** U6
**Mapping:** `@dataclass(frozen=True)`, tuples over lists at boundaries
**Applies:** Python code
**Verify (lint):** Lint and review public boundaries for frozen dataclasses and tuple use.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-PYTHON-06 MUST · Tests (Q1–Q3)
**Parent rules:** Q1, Q2, Q3
**Mapping:** pytest; coverage via `--cov --cov-fail-under=80` in committed config
**Applies:** Python code
**Verify (test):** Run pytest with the configured coverage floor.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-PYTHON-07 MUST · Env (Q10)
**Parent rules:** Q10
**Mapping:** `uv` with committed lockfile
**Applies:** Python code
**Verify (command):** Verify the committed `uv` lockfile reproduces the environment.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

## Typescript

### M-TYPESCRIPT-01 MUST · Format (U15)
**Parent rules:** U15
**Mapping:** Prettier, config committed
**Applies:** TypeScript and JavaScript code
**Verify (command):** Run Prettier with the committed configuration.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-TYPESCRIPT-02 MUST · Lint (U1, U7, U10)
**Parent rules:** U1, U7, U10
**Mapping:** ESLint 9 flat config; the committed baseline extends `js.configs.recommended`, configures `no-unused-vars` with a `^_` ignore, and enables `complexity`. TypeScript also extends `tseslint.configs.strictTypeChecked`, sets `parserOptions.projectService: true`, and configures `"@typescript-eslint/no-floating-promises": ["error", { ignoreVoid: false }]`; legacy `allowEmptyCatch: true` is prohibited by U7, so empty catches require handling or a valid scoped waiver; every `eslint-disable` carries a reason (U10).
**Applies:** TypeScript and JavaScript code
**Verify (lint):** Inspect committed `eslint.config.*` for `js.configs.recommended`; for TypeScript, also require `tseslint.configs.strictTypeChecked`, `parserOptions.projectService: true`, and `"@typescript-eslint/no-floating-promises": ["error", { ignoreVoid: false }]`; run ESLint and reject unexplained disables.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-TYPESCRIPT-03 MUST · Types (U5, U10)
**Parent rules:** U5, U10
**Mapping:** Committed `tsconfig.json` or its committed base sets `"strict": true` and separately sets `"noUncheckedIndexedAccess": true`; plain `.mjs` uses `// @ts-check` plus JSDoc when TypeScript is not adopted.
**Applies:** TypeScript and JavaScript code
**Verify (command):** Inspect the committed TSConfig inheritance chain, run `tsc --showConfig` to confirm resolved `strict` and `noUncheckedIndexedAccess` are both true, then run `tsc --noEmit`; for plain `.mjs`, run the committed checked-JavaScript equivalent.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-TYPESCRIPT-04 MUST · Async (U7)
**Parent rules:** U7
**Mapping:** Every Promise is awaited, returned for propagation, given a rejection path with `.catch` or two-argument `.then(onFulfilled, onRejected)`, or handed to a named background wrapper that attaches a rejection handler before returning a non-Promise; bare `void promise` never handles rejection.
**Applies:** TypeScript and JavaScript code
**Verify (lint):** Run ESLint under the typed config with `"@typescript-eslint/no-floating-promises": ["error", { ignoreVoid: false }]`; inspect each named background wrapper to confirm it attaches a rejection handler before returning a non-Promise.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-TYPESCRIPT-05 MUST · Tests (Q1–Q3)
**Parent rules:** Q1, Q2, Q3
**Mapping:** `node --test` (house pattern) or vitest; coverage threshold configured
**Applies:** TypeScript and JavaScript code
**Verify (test):** Run the configured Node or Vitest suite with its coverage threshold.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-TYPESCRIPT-06 MUST · Env (Q10)
**Parent rules:** Q10
**Mapping:** committed `package-lock.json`/`pnpm-lock.yaml`; ESM (`"type": "module"`)
**Applies:** TypeScript and JavaScript code
**Verify (command):** Verify the committed lockfile and ESM configuration.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

## Rust

### M-RUST-01 MUST · Format (U15)
**Parent rules:** U15
**Mapping:** `rustfmt`, config committed
**Applies:** Rust code
**Verify (command):** Run `cargo fmt --check`.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-RUST-02 MUST · Lint (U1, U7, U10)
**Parent rules:** U1, U7, U10
**Mapping:** Lint policy is committed, not CI-only: a standalone package defines `[lints.rust]` and `[lints.clippy]`; a workspace defines `[workspace.lints.rust]` and `[workspace.lints.clippy]`, with `[lints]` plus `workspace = true` in every member package. The committed policy sets `warnings = "deny"`, `unused_must_use = "deny"`, and Clippy `cognitive_complexity = "deny"`; CI-only flags are insufficient. Run `cargo clippy --all-targets --all-features`; use edition 2024 for new crates.
**Applies:** Rust code
**Verify (lint):** Inspect every tracked `Cargo.toml`: require `[lints.rust]` and `[lints.clippy]` for a standalone package, or root `[workspace.lints.rust]` and `[workspace.lints.clippy]` plus `[lints]` and `workspace = true` in every member package; require the three denial keys. Then run `cargo clippy --all-targets --all-features` for a package or `cargo clippy --workspace --all-targets --all-features` at a workspace root; CI-only flags are insufficient.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-RUST-03 MUST · Unsafe (U9)
**Parent rules:** U9
**Mapping:** `#![forbid(unsafe_code)]` by default; where unsafe is necessary: isolated module + `// SAFETY:` per block + clippy `undocumented_unsafe_blocks`
**Applies:** Rust code
**Verify (lint):** Run the unsafe-code lint policy and audit every documented exception.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-RUST-04 MUST · Errors (U7, U13)
**Parent rules:** U7, U13
**Mapping:** `Result` + `thiserror`/`anyhow` at the boundary; no `.unwrap()`/`.expect()` outside tests and provably-infallible sites (comment why)
**Applies:** Rust code
**Verify (lint):** Run Clippy and tests for Result handling and panic-free production paths.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-RUST-05 MUST · Tests (Q1–Q3)
**Parent rules:** Q1, Q2, Q3
**Mapping:** Run `cargo test --workspace`; keep integration tests in `tests/`; commit the Q2 coverage gate `cargo llvm-cov --workspace --fail-under-lines 80`. No configured coverage floor requires a Q2 waiver. An alternate coverage tool may substitute only when it enforces the same ≥80% owned-code line floor and carries an M-RUST-05 waiver.
**Applies:** Rust code
**Verify (test):** Run `cargo test --workspace` and the committed `cargo llvm-cov --workspace --fail-under-lines 80` gate. For an alternate committed tool, run its equivalent ≥80% gate and validate its M-RUST-05 waiver; if no coverage floor exists, validate a Q2 waiver.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-RUST-06 MUST · Env (Q10)
**Parent rules:** Q10
**Mapping:** committed `Cargo.lock` for binaries
**Applies:** Rust code
**Verify (command):** Verify the committed Cargo.lock for binaries.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

## Bash

### M-BASH-01 MUST · Prelude (U7, U13)
**Parent rules:** U7, U13
**Mapping:** `set -euo pipefail` in every script; `trap` for cleanup
**Applies:** Bash scripts
**Verify (lint):** Run ShellCheck and verify the strict prelude and cleanup trap.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-BASH-02 MUST · Lint (U10)
**Parent rules:** U10
**Mapping:** `shellcheck` clean; every `# shellcheck disable=` carries a reason (house practice already uses inline directives; no CI enforces it yet — rollout item)
**Applies:** Bash scripts
**Verify (lint):** Run ShellCheck and inspect every suppression for a reason.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-BASH-03 MUST · Interfaces (U12, U13)
**Parent rules:** U12, U13
**Mapping:** stdin/stdout composable; distinct exit codes documented in `--help`; errors to stderr
**Applies:** Bash scripts
**Verify (test):** Exercise pipe mode, stderr, help text, and documented exit codes.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-BASH-04 MUST · Safety (U15, U16)
**Parent rules:** U15, U16
**Mapping:** destructive scripts take `--dry-run`; no `rm -rf "$VAR/"` without guard against empty `$VAR`
**Applies:** Bash scripts
**Verify (test):** Exercise dry-run and empty-variable guards before destructive paths.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

### M-BASH-05 MUST · Scale (U4)
**Parent rules:** U4
**Mapping:** a bash script outgrowing ~100 lines or needing data structures graduates to Python/Rust
**Applies:** Bash scripts
**Verify (evidence):** Count lines and record the review decision for scripts near the size threshold.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

## Web

### M-WEB-01 MUST · Web frontend
**Parent rules:** P1, U3, U10, U15, U16, Q6
**Mapping:** Defers to the ECC web pack (loads path-scoped): CWV budgets (LCP < 2.5s, CLS < 0.1), bundle budgets, compositor-only animation, semantic HTML, nonce-based CSP, and the design-quality bar. The U-rules still apply to the JS/TS that ships.
**Applies:** web frontends.
**Verify (evidence):** Capture applicable ECC web-pack checks for performance budgets, semantic HTML, CSP, and design quality.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.

## New

### M-NEW-01 MUST · New-language bootstrap
**Parent rules:** U1, U2, U5, U7, U9, U10, Q2
**Mapping:** Before the first commit in a new language: pick the community-standard formatter and the strictest practical linter/type-checker, wire them into hooks (U10), map U1/U2/U5/U7/U9 to concrete tool flags in this file via an amendment, and declare the test runner + coverage mechanism (Q2). A language without a mapping here has no standing to merge.
**Applies:** the first commit in any language not already mapped.
**Verify (evidence):** The first commit records the formatter, strict lint and type flags, hooks, rule mappings, test runner, and coverage mechanism.
**Waiver:** Allowed only through a valid `.standards/waivers.json` record using the carrier required by its declared scope: a matching in-glob `std-waiver: <WAIVER-ID>` reference for `path:<glob>` or the non-empty `evidence` field (never an inline reference) for `process:<name>`.
