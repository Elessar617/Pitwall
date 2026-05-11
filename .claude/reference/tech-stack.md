# Tech Stack

## Languages

Python 3.13+

## Frameworks

- **TUI:** [Textual](https://textual.textualize.io/) ≥ 3.0
- **HTTP client:** `httpx` (async)
- **F1 telemetry library:** `fastf1` (uses `pandas`, `numpy` under the hood)
- **F1 live timing:** raw `httpx` against the OpenF1 REST + WebSocket API
- **F1 season history:** raw `httpx` against the Jolpica-F1 REST API
- **Storage:** `sqlite3` (Python stdlib — no extra dependency)

## Test framework

`pytest`, with doctest collection enabled (matches the faceoff convention this project draws from).

**Test command:** `uv run pytest`
**Test naming convention:** `tests/test_<module>.py` — one test file per `src/pitwall/<module>.py`
**Coverage tool + floor:** `pytest-cov`, **75 %** on changed files (per `.claude/rules/testing-discipline.md`)

## Linter / formatter

`ruff` — same strict ruleset as faceoff: `YTT`, `S`, `B`, `A`, `C4`, `T10`, `SIM`, `I`, `C90`, `E`, `W`, `F`, `PGH`, `UP`, `RUF`, `TRY`. Line length 120. `E501` and `E731` ignored. `S101` ignored under `tests/`.

**Lint command:** `uv run ruff check .`
**Format command:** `uv run ruff format .`

## Type checker

`ty` (Astral's type checker — matches faceoff)

**Type-check command:** `uv run ty check`

## Package management

`uv` (Astral)

**Add a dependency:** `uv add <pkg>`
**Add a dev dependency:** `uv add --dev <pkg>`
**Sync after pulling main:** `uv sync`
**Lockfile:** `uv.lock`

## Build / run

**Local dev:** `uv run pitwall`
**With a custom refresh interval (5 s minimum):** `uv run pitwall --refresh-interval 5`
**Production build:** `uv build` (produces a wheel + sdist in `dist/`)
**Run from wheel without installing:** `uvx pitwall`

## CI

GitHub Actions in `.github/workflows/`:

1. **Pre-commit** — runs `ruff check`, `ruff format --check`, lockfile validation, generic file-hygiene hooks.
2. **Tests** — `uv run pytest` on Python 3.13. Includes doctests.
3. **Type check** — `uv run ty check`.
4. **Build smoke** — `uv build` to confirm the wheel + sdist still assemble.

Releases are tag-driven (e.g., `v0.1.0`). A tag push triggers a publish-to-PyPI workflow.

## Pre-commit hooks

`pre-commit` runs the same `ruff` checks, format check, and standard hygiene hooks (trailing whitespace, end-of-file fixer, no-large-files, etc.) before every commit. `make install` (when the Makefile lands) installs the pre-commit hooks into git.
