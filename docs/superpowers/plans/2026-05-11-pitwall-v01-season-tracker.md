# Pitwall v0.1 — Season Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Pitwall v0.1 — a runnable Textual TUI showing the current F1 season's schedule, standings, results, and driver/constructor profiles, working offline once seeded from Jolpica-F1.

**Architecture:** Single-process Textual app. Data flows: `JolpicaClient` (httpx) → `SQLiteCache` (write-through, source of truth) → `models.py` (validated Pydantic) → screens. Background refresh via Textual `@work` on a `jolpica_sync` worker. Screens NEVER call clients directly. CLI entry via `uv run pitwall`.

**Tech Stack:** Python 3.13, Textual ≥ 0.85, httpx (async), Pydantic v2, sqlite3 (stdlib), uv, ruff, ty, pytest, pytest-asyncio, respx (httpx mock), pytest-textual-snapshot.

**Source of truth:** [`docs/superpowers/specs/2026-05-11-pitwall-design.md`](../specs/2026-05-11-pitwall-design.md). Section refs in tasks point there.

---

## Pre-flight: Verify clean baseline

- [ ] **Step 0.1: Confirm git state**

  Run: `git -C /Users/gardnerwilson/workspace/github.com/elessar617/Pitwall status`
  Expected: `On branch main`, `nothing to commit, working tree clean`.
  If dirty: stop and resolve before proceeding.

- [ ] **Step 0.2: Confirm current HEAD has the spec**

  Run: `git log --oneline -5`
  Expected: top commit is `64207c9 docs(spec): consolidated Pitwall design spec (v0.1 → v1.0)` (or a descendant).

- [ ] **Step 0.3: Confirm uv and Python 3.13 are available**

  Run: `uv --version && python3.13 --version`
  Expected: both print versions without error. If `uv` missing: `brew install uv` (macOS) or see https://docs.astral.sh/uv/getting-started/installation/.

---

## COMMIT 1 — Drop stray empty stage dirs (chore)

Resolves the scaffold bug noted in the spec's Section 2.5.

### Task 1: Delete misplaced stage dirs at `build/workflows/` root

**Files:**
- Delete: `build/workflows/01-spec/.gitkeep`
- Delete: `build/workflows/02-implement/.gitkeep`
- Delete: `build/workflows/03-validate/.gitkeep`
- Delete: `build/workflows/04-output/.gitkeep`
- Delete: the four now-empty parent dirs

**Why:** Per `build/workflows/CONTEXT.md`, the four pipeline stages (`01-spec`, `02-implement`, `03-validate`, `04-output`) live INSIDE iteration dirs (`NN-<slug>/`), not at the workflows root. The leftover root-level dirs (each containing only a `.gitkeep`) would mislead future iterations and risk false-positive matches in `block-cycle-overrun.sh` / `block-output-without-signoff.sh`. The valid template at `build/workflows/00-template/{01-spec,02-implement,03-validate,04-output}/` is unaffected.

- [ ] **Step 1.1: Verify the stray dirs exist and are empty (apart from .gitkeep)**

  Run:
  ```bash
  for d in 01-spec 02-implement 03-validate 04-output; do
    echo "--- build/workflows/$d ---"
    ls -A build/workflows/$d
  done
  ```
  Expected: each prints exactly `.gitkeep` and nothing else.

- [ ] **Step 1.2: git rm the .gitkeep files and remove the dirs**

  Run:
  ```bash
  git rm build/workflows/01-spec/.gitkeep \
         build/workflows/02-implement/.gitkeep \
         build/workflows/03-validate/.gitkeep \
         build/workflows/04-output/.gitkeep
  rmdir build/workflows/01-spec \
        build/workflows/02-implement \
        build/workflows/03-validate \
        build/workflows/04-output
  ```
  Expected: 4 files removed; rmdir succeeds (dirs are now empty).

- [ ] **Step 1.3: Confirm template is intact**

  Run: `ls build/workflows/00-template/`
  Expected: `01-spec  02-implement  03-validate  04-output` (the valid stage dirs INSIDE the template iteration).

- [ ] **Step 1.4: Commit**

  ```bash
  git commit -m "$(cat <<'EOF'
  chore: drop stray empty stage dirs at build/workflows/ root

  The four pipeline stages (01-spec, 02-implement, 03-validate,
  04-output) belong inside iteration dirs (NN-<slug>/), not at the
  workflows root. The root-level copies were leftover from scaffold
  construction; each contained only a .gitkeep.

  Removing them prevents false-positive matches in
  block-cycle-overrun.sh and block-output-without-signoff.sh hooks,
  and removes a misleading visual cue for future iteration authors.
  The valid template at build/workflows/00-template/ is unaffected.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  ```

- [ ] **Step 1.5: Push**

  Run: `git push`
  Expected: `main -> main` push line.

---

## COMMIT 2 — Initialize uv project (chore)

Make `uv run pitwall` resolvable. No features, just the bare runnable scaffold.

### Task 2: Initialize the Python project with uv

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `src/pitwall/__init__.py`
- Create: `src/pitwall/__main__.py`
- Create: `src/pitwall/cli.py`
- Modify: `src/README.md` (replace placeholder with actual layout note)
- Generated: `uv.lock` (by `uv sync`)
- Modify: `.gitignore` (add `uv.lock`? NO — uv.lock SHOULD be committed for apps. Verify it's not in current ignore.)

**Why:** Pre-flight chore #2 from spec Section 2.5. Establishes the package boundary so the rest of the plan can do `from pitwall.X import Y` from real code paths.

- [ ] **Step 2.1: Confirm uv.lock is not currently gitignored**

  Run: `git check-ignore -v uv.lock || echo "not ignored"`
  Expected: `not ignored` (uv.lock should be tracked for apps).

- [ ] **Step 2.2: Create `.python-version`**

  Create file `.python-version` with content:
  ```
  3.13
  ```

- [ ] **Step 2.3: Create `pyproject.toml`**

  Create file `pyproject.toml`:
  ```toml
  [project]
  name = "pitwall"
  version = "0.0.0"
  description = "Terminal-UI companion for Formula 1: live timing + track map, season tracker, and a strategy mini-game."
  readme = "README.md"
  requires-python = ">=3.13"
  authors = [
    { name = "Gardner Wilson", email = "gardnerwilson14@gmail.com" }
  ]
  license = { text = "MIT" }
  dependencies = []

  [project.scripts]
  pitwall = "pitwall.cli:main"

  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"

  [tool.hatch.build.targets.wheel]
  packages = ["src/pitwall"]

  [tool.ruff]
  line-length = 100
  target-version = "py313"

  [tool.ruff.lint]
  select = ["E", "F", "I", "N", "UP", "B", "SIM", "RUF"]
  ignore = []

  [tool.ruff.format]
  quote-style = "double"

  [tool.ty]
  python-version = "3.13"
  ```

- [ ] **Step 2.4: Create `src/pitwall/__init__.py`**

  Create file with content:
  ```python
  """Pitwall — Formula 1 TUI companion."""

  __version__ = "0.0.0"
  ```

- [ ] **Step 2.5: Create `src/pitwall/__main__.py`**

  Create file with content:
  ```python
  """Allow `python -m pitwall`."""

  from pitwall.cli import main

  if __name__ == "__main__":
      main()
  ```

- [ ] **Step 2.6: Create `src/pitwall/cli.py` (stub)**

  Create file with content:
  ```python
  """CLI entry point. Stub for v0.0.0 — full app shell lands in v0.1."""

  from pitwall import __version__


  def main() -> None:
      print(f"pitwall v{__version__}")
  ```

- [ ] **Step 2.7: Replace `src/README.md` placeholder**

  Read existing `src/README.md`, then rewrite as:
  ```markdown
  # src/

  Long-lived production source code for Pitwall.

  ## Layout

  - `pitwall/` — the package (`from pitwall.X import Y`)
    - `cli.py` — `uv run pitwall` entry
    - `app.py` — `PitwallApp(textual.App)` (lands in v0.1)
    - `data/` — clients, cache, models (lands in v0.1)
    - `screens/` — Textual `Screen` subclasses (lands in v0.1)
    - `widgets/` — reusable rendering primitives
    - `workers/` — background data fetchers (Textual `@work`)

  See `docs/superpowers/specs/2026-05-11-pitwall-design.md` Section 3.1.
  ```

- [ ] **Step 2.8: Run `uv sync` to generate uv.lock**

  Run: `uv sync`
  Expected: creates `uv.lock` and `.venv/`. Prints `Resolved N packages` (small N since we have no deps yet).

- [ ] **Step 2.9: Verify `uv run pitwall` works**

  Run: `uv run pitwall`
  Expected: prints `pitwall v0.0.0` and exits 0.

- [ ] **Step 2.10: Stage and commit**

  ```bash
  git add pyproject.toml .python-version uv.lock \
          src/pitwall/__init__.py src/pitwall/__main__.py src/pitwall/cli.py \
          src/README.md
  git commit -m "$(cat <<'EOF'
  chore: initialize uv project (pyproject.toml, package skeleton, cli stub)

  Pre-flight chore #2 from the design spec. Establishes:

  - pyproject.toml with hatchling build backend, ruff + ty config,
    Python ≥ 3.13 requirement, and a console_script entry
    `pitwall = pitwall.cli:main`.
  - .python-version pinning 3.13 for uv.
  - src/pitwall/ package skeleton (__init__.py, __main__.py, cli.py
    stub that prints the version).
  - src/README.md updated to describe the v0.1 module layout.
  - uv.lock generated and committed (per uv guidance for apps).

  After this commit `uv run pitwall` resolves and prints
  "pitwall v0.0.0". No features yet; v0.1 features land via the
  build/workflows/01-season-tracker/ iteration.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  git push
  ```

---

## COMMIT 3 — ADR 0001: Stack decision

### Task 3: Write ADR 0001

**Files:**
- Create: `spec/adrs/0001-stack-python-textual.md`
- Delete: `spec/adrs/.gitkeep`

**Why:** Pre-flight chore #3. Per spec Section 2.4: the stack is fixed by the brief; risk of revision is minimal; ADR records *why*. Removing `.gitkeep` because the dir now has real content.

- [ ] **Step 3.1: Create `spec/adrs/0001-stack-python-textual.md`**

  Create with content:
  ```markdown
  # 0001. Adopted Python 3.13 + Textual + uv + ruff + ty for Pitwall

  **Status:** Accepted
  **Date:** 2026-05-11
  **Deciders:** Gardner Wilson (project lead)

  ## Context

  Pitwall needs a stack for a single-process terminal UI that handles async I/O
  (HTTP polling, SQLite caching, periodic refresh) and renders a non-trivial
  custom layout (timing tower, track map, multiple screens).

  Inspiration repo `faceoff/` (NHL TUI) uses Python + Textual + uv + ruff with
  a similar shape. Reusing that stack means we get a working reference for
  async patterns, screen routing, and worker discipline.

  ## Decision

  - **Language:** Python 3.13. Modern type-hint syntax, structural pattern matching, performance improvements over 3.10/3.11.
  - **TUI framework:** Textual (≥ 0.85). Mature, async-native, well-documented, snapshot-test support, active community.
  - **Package manager:** uv. Fast resolver/installer; lockfile commits for apps; built-in script runner (`uv run pitwall`).
  - **Linter + formatter:** ruff. Single tool replaces flake8 + isort + black; rapid iteration.
  - **Type checker:** ty (Astral's type checker). Same vendor as ruff/uv; fast, works with modern Python type syntax.

  ## Consequences

  ### Positive
  - One vendor (Astral) for uv/ruff/ty — coherent UX, fast tooling.
  - Textual's `@work` decorator gives us async background refresh on the main event loop without thread coordination.
  - faceoff/ provides a working reference we can mirror when stuck.
  - Python's stdlib has sqlite3 — no DB driver dependency needed.

  ### Negative
  - Python 3.13 is recent; some terminals or CI runners may not have it pre-installed (mitigated by `.python-version` and uv).
  - ty is newer than mypy/pyright; may have rough edges (mitigated by being able to swap to mypy if blocking).
  - Textual is a young framework relative to curses/blessed; breaking changes between minor versions are possible (mitigated by pinning major.minor in `pyproject.toml`).

  ## Alternatives considered

  - **Rust + ratatui:** more performant; team is faster in Python. Rejected for solo-dev velocity.
  - **Go + tview / bubbletea:** similar trade-off to Rust. Rejected for the same reason.
  - **Python + curses (stdlib):** no abstractions, more boilerplate, no snapshot tests. Rejected for productivity.
  - **Python + Rich (without Textual):** Rich is for one-shot renders; Textual layers an event-driven app on top of Rich. Pitwall needs the event loop.

  ## References

  - [`spec/briefs/pitwall-overview.md`](../briefs/pitwall-overview.md) — project brief
  - [`docs/superpowers/specs/2026-05-11-pitwall-design.md`](../../docs/superpowers/specs/2026-05-11-pitwall-design.md) §2.4 — ADR sequence rule
  - `faceoff/pyproject.toml` — reference stack
  ```

- [ ] **Step 3.2: Delete .gitkeep**

  Run: `git rm spec/adrs/.gitkeep`

- [ ] **Step 3.3: Stage, commit, push**

  ```bash
  git add spec/adrs/0001-stack-python-textual.md
  git commit -m "$(cat <<'EOF'
  docs(adr): 0001 Python 3.13 + Textual + uv + ruff + ty stack

  Ratifies the de-facto stack decision from
  spec/briefs/pitwall-overview.md. Captures: language (3.13), TUI
  framework (Textual ≥ 0.85), package manager (uv), linter+formatter
  (ruff), type checker (ty), and rationale for picking each over
  alternatives (Rust+ratatui, Go+bubbletea, curses, Rich-without-Textual).

  Per the design spec's ADR-write-timing rule (Section 2.4), ADR 0001
  is the only one written pre-spike — the stack decision is fixed by
  the brief and has low rework risk. ADRs 0002 and 0003 wait for
  their respective lab spikes to REPORT.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  git push
  ```

---

## LAB SPIKE — `lab/02-jolpica-eval/`

Per spec Section 2.2: blocks v0.1 (must REPORT before `build/workflows/01-season-tracker/` starts). Time-boxed to 1–2 days. Output is learning, not shipped code.

### Task 4: Write `lab/02-jolpica-eval/PREFLIGHT.md`

**Files:**
- Create: `lab/02-jolpica-eval/PREFLIGHT.md`
- Create: `lab/02-jolpica-eval/VERIFY.md` (template; filled in Task 6)
- Create: `lab/02-jolpica-eval/REPORT.md` (template; filled in Task 6)
- Create: `lab/02-jolpica-eval/prototype/.gitkeep`

**Why:** PREFLIGHT pins the hypothesis, success/failure criteria, and time-box BEFORE any code. Per the `spike-protocol` skill in `.claude/skills/spike-protocol/SKILL.md`.

- [ ] **Step 4.1: Create the iteration directory and stub files**

  Run:
  ```bash
  mkdir -p lab/02-jolpica-eval/prototype
  touch lab/02-jolpica-eval/prototype/.gitkeep
  ```

- [ ] **Step 4.2: Write PREFLIGHT.md**

  Create `lab/02-jolpica-eval/PREFLIGHT.md`:
  ````markdown
  # PREFLIGHT — jolpica-eval

  ## Hypothesis

  **Jolpica-F1 is a complete, schema-stable, rate-limit-friendly drop-in for the deprecated Ergast API and is sufficient as the sole data source for Pitwall's v0.1 season tracker (schedule, standings, results, qualifying, driver/constructor profiles for every season ≥ 1950 and the current 2026 season).**

  ## Why this matters

  v0.1 is the season tracker. If Jolpica is missing endpoints, has unstable schemas, or rate-limits us under sustained polling at the documented intervals, we need to know before `build/workflows/01-season-tracker/` starts — otherwise we'll discover the gap mid-build with the SQLite schema and screens already written.

  Fallback if Jolpica falls short: write a thin Ergast-compatible scraper against archived Ergast data, OR fork to FastF1's ergast-replacement module. Either fallback is multi-day work; we want to know now.

  ## Prior art

  - [x] Reviewed [Jolpica-F1 README](https://github.com/jolpica/jolpica-f1)
  - [x] Reviewed [Ergast API docs](https://ergast.com/mrd/) (the source schema Jolpica mirrors)
  - [x] Confirmed Jolpica is community-run with public uptime via GitHub Pages

  **Notes:**
  - Jolpica is at `https://api.jolpi.ca/ergast/f1/` and aims for full Ergast endpoint compatibility.
  - Endpoints we need for v0.1: `/<season>.json` (races), `/<season>/drivers.json`, `/<season>/constructors.json`, `/<season>/results.json`, `/<season>/qualifying.json`, `/<season>/driverStandings.json`, `/<season>/constructorStandings.json`.
  - For driver/constructor profiles: `/drivers/<driverId>.json`, `/constructors/<constructorId>.json` plus per-season stats.
  - Rate limit per docs: 4 req/sec, 500/hour (sufficient for our use case — we cache and refresh hourly).

  ## Approach

  1. Build a tiny script `prototype/jolpica_smoke.py` that pulls every endpoint listed above for: (a) the current 2026 season, (b) one historical season (e.g., 2024 — full season data exists), (c) a profile sample (Hamilton, Mercedes).
  2. For each endpoint, record: HTTP status, response time, payload size, count of records, presence of every field we expect.
  3. Repeat the calls 5×, spaced 1 minute apart, to confirm no schema drift / no rate-limit hits.
  4. Save raw JSON responses to `prototype/responses/` and a structured summary to `prototype/measurements.json`.

  ## Success criteria

  - All 7 listed endpoints return HTTP 200 for both 2026 and 2024 seasons.
  - Every record includes the fields we map in `data/models.py` (sketched in spec Section 3.4).
  - Median response time ≤ 500 ms; p95 ≤ 2 s.
  - No HTTP 429 (rate limit) under the smoke pattern.
  - Schema across the 5 repeated calls is byte-identical for every endpoint.
  - Driver and constructor profile endpoints (`/drivers/<id>`, `/constructors/<id>`) return the bio fields used in `screens/profile.py`.

  ## Failure criteria

  - Any required endpoint missing or returning non-200.
  - Critical field absent (e.g., qualifying response without Q1/Q2/Q3 splits).
  - HTTP 429 hit during the smoke pattern.
  - Schema drift between calls (would break our cache).
  - Profile endpoints don't include enough bio data to render a meaningful profile screen.

  ## Time box

  Walk away after **1.5 days (~12 hours)**. If past the box, REPORT records what we have and we explicitly choose:

  - **Pursue** — Jolpica is good; proceed to `build/workflows/01-season-tracker/`.
  - **Modify** — narrow v0.1 to the subset Jolpica handles cleanly (e.g., skip qualifying if Q1/Q2/Q3 missing); document gap in `docs/explorations/02-jolpica-eval.md`.
  - **Abandon** — write `docs/explorations/02-jolpica-eval.md` documenting why; build a thin Ergast-archive scraper or wrap FastF1's ergast module instead.
  ````

- [ ] **Step 4.3: Write VERIFY.md template**

  Create `lab/02-jolpica-eval/VERIFY.md`:
  ```markdown
  # VERIFY — jolpica-eval

  > Filled in after the prototype runs. See PREFLIGHT.md for the hypothesis.

  ## What was actually built

  *(Task 5 fills this in: paths to prototype script, what it does.)*

  ## Tests performed

  *(Task 6 fills this in: which endpoints called, how many times, what was measured.)*

  ## Findings

  *(Task 6 fills this in: per-endpoint table — status, latency p50/p95, payload size, completeness, schema stability across repeated calls.)*

  ## Surprises

  *(Task 6: anything that wasn't in the PREFLIGHT.)*

  ## Limitations

  *(Task 6: what the spike DID NOT measure that's still uncertain.)*
  ```

- [ ] **Step 4.4: Write REPORT.md template**

  Create `lab/02-jolpica-eval/REPORT.md`:
  ```markdown
  # REPORT — jolpica-eval

  > Filled in after VERIFY. Drives the pursue/modify/abandon decision and ADR 0002.

  ## Outcome

  *(Task 6: one of: PURSUE / MODIFY / ABANDON. With one-line summary.)*

  ## Evidence supporting the outcome

  *(Task 6: bullet points pointing to specific findings in VERIFY.md.)*

  ## Open questions

  *(Task 6: things this spike couldn't answer that need follow-up.)*

  ## Follow-ups

  *(Task 6: actions for the next iteration; e.g., "ADR 0002 captures Jolpica decision", "build iteration 01-season-tracker can start".)*

  ## Time spent

  *(Task 6: actual time vs. time-box. If exceeded: why.)*
  ```

- [ ] **Step 4.5: Stage, commit, push**

  ```bash
  git add lab/02-jolpica-eval/
  git commit -m "$(cat <<'EOF'
  docs(lab): jolpica-eval PREFLIGHT — Jolpica-F1 fitness for v0.1

  PREFLIGHT pins the hypothesis (Jolpica is a complete, schema-stable,
  rate-limit-friendly drop-in for the deprecated Ergast API), measurement
  approach, success/failure criteria, and 1.5-day time box.

  Blocks build/workflows/01-season-tracker/. VERIFY.md and REPORT.md
  templates committed alongside; filled in after the prototype runs.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  git push
  ```

### Task 5: Build the smoke prototype

**Files:**
- Create: `lab/02-jolpica-eval/prototype/jolpica_smoke.py`
- Create: `lab/02-jolpica-eval/prototype/responses/.gitkeep`

**Why:** A self-contained script that pulls every v0.1 endpoint, measures latency/completeness/stability, and writes a structured summary. NOT TDD — spikes don't ship; the prototype is throwaway. (Per `spike-protocol` skill: "the prototype is not the deliverable; the learning is".)

- [ ] **Step 5.1: Add httpx as a temporary dev dep for the spike**

  Run:
  ```bash
  uv add --dev httpx
  ```
  Expected: `pyproject.toml` gets `[dependency-groups] dev = ["httpx>=..."]`; `uv.lock` updates.

- [ ] **Step 5.2: Create the prototype script**

  Create `lab/02-jolpica-eval/prototype/jolpica_smoke.py`:
  ```python
  """Smoke test for Jolpica-F1 against Pitwall v0.1's endpoint needs.

  Throwaway. Not part of the package. Run with:
      uv run python lab/02-jolpica-eval/prototype/jolpica_smoke.py
  """

  from __future__ import annotations

  import asyncio
  import json
  import time
  from pathlib import Path
  from statistics import median

  import httpx

  HERE = Path(__file__).parent
  RESPONSES = HERE / "responses"
  RESPONSES.mkdir(exist_ok=True)
  SUMMARY = HERE / "measurements.json"

  BASE = "https://api.jolpi.ca/ergast/f1"
  SEASONS = ["2026", "2024"]
  PROFILE_DRIVER = "hamilton"
  PROFILE_CONSTRUCTOR = "mercedes"
  REPEAT = 5  # repeat each call N times to detect schema drift / rate limits

  ENDPOINTS = [
      ("races",                 "/{season}.json"),
      ("drivers",               "/{season}/drivers.json"),
      ("constructors",          "/{season}/constructors.json"),
      ("results",               "/{season}/results.json?limit=100"),
      ("qualifying",            "/{season}/qualifying.json?limit=100"),
      ("driverStandings",       "/{season}/driverStandings.json"),
      ("constructorStandings",  "/{season}/constructorStandings.json"),
  ]
  PROFILE_ENDPOINTS = [
      ("driver_profile",      f"/drivers/{PROFILE_DRIVER}.json"),
      ("constructor_profile", f"/constructors/{PROFILE_CONSTRUCTOR}.json"),
  ]


  async def fetch_one(client: httpx.AsyncClient, url: str) -> dict:
      t0 = time.monotonic()
      r = await client.get(url, timeout=10.0)
      elapsed_ms = (time.monotonic() - t0) * 1000
      return {
          "url": url,
          "status": r.status_code,
          "elapsed_ms": elapsed_ms,
          "bytes": len(r.content),
          "json": r.json() if r.status_code == 200 else None,
      }


  async def measure(name: str, url: str) -> dict:
      """Call `url` REPEAT times, save responses, return summary."""
      async with httpx.AsyncClient(headers={"User-Agent": "pitwall-spike/0.1"}) as client:
          calls = []
          for i in range(REPEAT):
              call = await fetch_one(client, url)
              calls.append(call)
              # save first response as the canonical snapshot
              if i == 0 and call["status"] == 200:
                  out = RESPONSES / f"{name}.json"
                  out.write_text(json.dumps(call["json"], indent=2))
              await asyncio.sleep(60.0 / REPEAT)  # spread over ~1min

      latencies = [c["elapsed_ms"] for c in calls if c["status"] == 200]
      payload_sizes = {c["bytes"] for c in calls if c["status"] == 200}
      json_bodies = [json.dumps(c["json"], sort_keys=True) for c in calls if c["status"] == 200]

      return {
          "name": name,
          "url": url,
          "n_calls": len(calls),
          "n_ok": len(latencies),
          "statuses": [c["status"] for c in calls],
          "latency_p50_ms": median(latencies) if latencies else None,
          "latency_p95_ms": max(sorted(latencies)[: max(1, int(len(latencies) * 0.95))]) if latencies else None,
          "payload_size_unique": sorted(payload_sizes),
          "schema_stable": len(set(json_bodies)) == 1 if json_bodies else False,
      }


  async def main() -> None:
      results = []
      for season in SEASONS:
          for name, path in ENDPOINTS:
              full_name = f"{name}_{season}"
              url = BASE + path.format(season=season)
              print(f"→ {full_name}")
              results.append(await measure(full_name, url))
      for name, path in PROFILE_ENDPOINTS:
          print(f"→ {name}")
          results.append(await measure(name, BASE + path))

      SUMMARY.write_text(json.dumps(results, indent=2))
      print(f"\nWrote {SUMMARY}")
      print(f"Wrote {len(list(RESPONSES.glob('*.json')))} response snapshots to {RESPONSES}")


  if __name__ == "__main__":
      asyncio.run(main())
  ```

- [ ] **Step 5.3: Add `responses/.gitkeep`**

  Run: `touch lab/02-jolpica-eval/prototype/responses/.gitkeep`

- [ ] **Step 5.4: Stage and commit (NOT pushed yet — measurements come next)**

  ```bash
  git add pyproject.toml uv.lock lab/02-jolpica-eval/prototype/
  git commit -m "$(cat <<'EOF'
  feat(lab): jolpica smoke prototype script

  prototype/jolpica_smoke.py calls every Jolpica endpoint Pitwall v0.1
  needs (races, drivers, constructors, results, qualifying, standings,
  profiles) for 2026 + 2024 seasons. Repeats each call 5× spread over
  ~1min to detect schema drift and rate-limit hits.

  Outputs: prototype/responses/<name>.json (canonical snapshots) and
  prototype/measurements.json (latency / payload-size / stability summary).

  httpx added as dev dep (spike-only; production data layer in v0.1
  build iteration uses its own client setup).

  Run with: uv run python lab/02-jolpica-eval/prototype/jolpica_smoke.py

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  ```

### Task 6: Run the spike, fill in VERIFY + REPORT

**Files:**
- Modify: `lab/02-jolpica-eval/VERIFY.md`
- Modify: `lab/02-jolpica-eval/REPORT.md`
- Create: `lab/02-jolpica-eval/prototype/measurements.json` (output)
- Create: `lab/02-jolpica-eval/prototype/responses/*.json` (snapshots)

- [ ] **Step 6.1: Run the prototype**

  Run:
  ```bash
  uv run python lab/02-jolpica-eval/prototype/jolpica_smoke.py
  ```
  Expected: prints `→ <name>` for each endpoint (~18 endpoint-runs total), then `Wrote .../measurements.json` and the snapshot count.

- [ ] **Step 6.2: Inspect `measurements.json` + snapshots**

  Run: `cat lab/02-jolpica-eval/prototype/measurements.json | jq '.[] | {name, n_ok, latency_p50_ms, schema_stable}'`
  Expected: per-endpoint summary with latency, OK count, and schema-stable boolean.

- [ ] **Step 6.3: Fill VERIFY.md**

  Replace the placeholder sections with the actual data. Use the template structure already in the file. Concrete tables — one row per endpoint with columns: status, p50 ms, p95 ms, bytes, schema_stable.

- [ ] **Step 6.4: Fill REPORT.md and choose pursue/modify/abandon**

  Map the VERIFY findings against PREFLIGHT's success/failure criteria. Pick the outcome:
  - **PURSUE** if ALL success criteria met → ADR 0002 ratifies Jolpica.
  - **MODIFY** if some endpoints fall short but workarounds exist → narrow v0.1 scope; document narrowing.
  - **ABANDON** if Jolpica fundamentally can't serve v0.1 → write `docs/explorations/02-jolpica-eval.md`; redirect to fallback (Ergast-archive or FastF1-ergast).

  Fill in REPORT.md sections accordingly.

- [ ] **Step 6.5: Stage and commit**

  ```bash
  git add lab/02-jolpica-eval/
  git commit -m "$(cat <<'EOF'
  docs(lab): jolpica-eval VERIFY + REPORT — outcome: <PURSUE|MODIFY|ABANDON>

  Spike outcome: <one-line summary>. Full findings in VERIFY.md;
  decision rationale in REPORT.md.

  Measurements: prototype/measurements.json. Canonical response
  snapshots: prototype/responses/<endpoint>.json (committed for future
  reference and as fixtures for v0.1 build iteration tests).

  Next: ADR 0002 ratifies the data-source decision; then
  build/workflows/01-season-tracker/ starts.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  git push
  ```

### Task 7: Write ADR 0002 — Jolpica as season-data source

**Files:**
- Create: `spec/adrs/0002-jolpica-as-season-source.md`

**Why:** Per spec Section 2.4: ADR ratifies the decision contingent on the spike. Run AFTER Task 6 has set the outcome.

> **Conditional:** If REPORT outcome is **ABANDON**, this ADR records a different decision (the fallback). The structure below assumes PURSUE; adjust the Decision section if MODIFY/ABANDON.

- [ ] **Step 7.1: Write the ADR**

  Create `spec/adrs/0002-jolpica-as-season-source.md`:
  ```markdown
  # 0002. Adopted Jolpica-F1 as the sole data source for the v0.1 season tracker

  **Status:** Accepted
  **Date:** 2026-05-1?  *(actual date when this commit lands)*
  **Deciders:** Gardner Wilson
  **Spike:** [`lab/02-jolpica-eval/REPORT.md`](../../lab/02-jolpica-eval/REPORT.md)

  ## Context

  v0.1 ships the season tracker (schedule, standings, results, qualifying,
  driver/constructor profiles). The brief lists Jolpica-F1 (Ergast-API-compatible
  community fork) as the chosen source; this ADR ratifies that choice based
  on the `lab/02-jolpica-eval/` spike outcome.

  ## Decision

  Jolpica-F1 (`https://api.jolpi.ca/ergast/f1/`) is Pitwall's sole data source
  for v0.1's season tracker. Endpoint usage:

  | Surface | Endpoint |
  |---|---|
  | Schedule screen | `/<season>.json` |
  | Standings (driver) | `/<season>/driverStandings.json` |
  | Standings (constructor) | `/<season>/constructorStandings.json` |
  | Results screen | `/<season>/results.json` |
  | Qualifying (within results) | `/<season>/qualifying.json` |
  | Driver profile | `/drivers/<driverId>.json` + per-season aggregates |
  | Constructor profile | `/constructors/<constructorId>.json` + per-season aggregates |

  Refresh policy: 1-hour TTL on the cache, manual `r` to force-refresh
  (per design spec Section 3.3).

  ## Consequences

  ### Positive
  - One client (`src/pitwall/data/jolpica.py`); one schema family.
  - Spike confirmed acceptable latency, schema stability, and rate-limit headroom.
  - Ergast schema is well-known territory; community Q&A applies.

  ### Negative
  - Jolpica is community-maintained; no SLA. Mitigated by aggressive caching and stale-data UX.
  - If Jolpica disappears: fallback path is wrap FastF1's ergast module or build an Ergast-archive scraper. Re-evaluation point.

  ## Alternatives considered

  - **FastF1's ergast module:** larger dependency for what we need; pulls in pandas. Rejected for v0.1.
  - **Direct Ergast scraping (deprecated):** sustained reliability uncertain; no guaranteed availability.
  - **F1 official API:** paid; out of scope per brief.

  ## References

  - [`docs/superpowers/specs/2026-05-11-pitwall-design.md`](../../docs/superpowers/specs/2026-05-11-pitwall-design.md) §2.4
  - [`lab/02-jolpica-eval/PREFLIGHT.md`](../../lab/02-jolpica-eval/PREFLIGHT.md)
  - [`lab/02-jolpica-eval/REPORT.md`](../../lab/02-jolpica-eval/REPORT.md)
  ```

- [ ] **Step 7.2: Stage and commit**

  ```bash
  git add spec/adrs/0002-jolpica-as-season-source.md
  git commit -m "$(cat <<'EOF'
  docs(adr): 0002 Jolpica-F1 as the v0.1 season tracker data source

  Ratifies the Jolpica decision based on lab/02-jolpica-eval REPORT
  outcome. Per design spec §2.4, ADRs land at the moment of honest
  commitment — the spike is the moment.

  Endpoint mapping documented per v0.1 surface. Consequences and
  alternatives sections per ADR template.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  git push
  ```

---

## BUILD ITERATION — `build/workflows/01-season-tracker/`

The four-stage pipeline runs here. Every code-writing step inside is **TDD** (per `.claude/rules/testing-discipline.md` and the `tdd-loop` skill at `.claude/skills/tdd-loop/SKILL.md`): red → green → refactor.

All tasks in this section land on `main` (per spec §4.4: v0.1 stays on main; PRs from v0.2).

### Task 8: Run the planner — write `01-spec/SPEC.md`

**Files:**
- Create: `build/workflows/01-season-tracker/01-spec/SPEC.md`

**Why:** The planner agent's one-shot output. Subsequent implementer/reviewer/adversary cycles read from it. Per `.claude/agents/planner-agent.md`.

- [ ] **Step 8.1: Create iteration directory**

  Run: `mkdir -p build/workflows/01-season-tracker/{01-spec,02-implement,03-validate,04-output}`

- [ ] **Step 8.2: Write SPEC.md**

  Create `build/workflows/01-season-tracker/01-spec/SPEC.md`:
  ```markdown
  # SPEC — 01-season-tracker

  **Source:** [`spec/briefs/pitwall-overview.md`](../../../../spec/briefs/pitwall-overview.md), [`docs/superpowers/specs/2026-05-11-pitwall-design.md`](../../../../docs/superpowers/specs/2026-05-11-pitwall-design.md), [`spec/adrs/0001-stack-python-textual.md`](../../../../spec/adrs/0001-stack-python-textual.md), [`spec/adrs/0002-jolpica-as-season-source.md`](../../../../spec/adrs/0002-jolpica-as-season-source.md)
  **Planner:** Gardner Wilson (or planner agent)
  **Date:** 2026-05-1?

  ## Scope

  Implement Pitwall v0.1: a runnable Textual TUI showing the current and historical F1 season's schedule, standings, results, and driver/constructor profiles. Includes the project skeleton (CLI entry, app shell, screen router, SQLite schema). Built on Jolpica-F1 + SQLite write-through cache.

  Three-pillar deferrals (track map, timing tower, strategy mini-game) are explicitly OUT of this iteration. Their nav-tabs render as disabled with `(v0.x)` labels.

  ## Acceptance criteria

  Verbatim from design spec §5.1 (AC-01 through AC-12). Each maps to ≥ 1 test.

  | # | Criterion | Verification |
  |---|---|---|
  | AC-01 | `uv run pitwall` launches the TUI without error on macOS, Linux | `pytest tests/test_smoke.py -v` |
  | AC-02 | Home screen shows nav with Schedule/Standings/Results/Profile enabled, others disabled | `tests/screens/test_home.py` snapshot |
  | AC-03 | Schedule screen shows current season's full calendar | `tests/screens/test_schedule.py` snapshot + fixture |
  | AC-04 | Standings screen shows driver & constructor standings with `Tab` toggle | snapshot + interaction |
  | AC-05 | Results screen + season-picker | snapshot + parametrized |
  | AC-06 | Profile screen for driver and constructor | snapshot tests |
  | AC-07 | Offline mode renders all v0.1 screens from cache | `tests/test_offline.py` with `respx` |
  | AC-08 | Stale data shows `[stale: HH:MM]`; `r` re-fetches | interaction with frozen clock |
  | AC-09 | Coverage ≥ 75 % on changed lines | CI step |
  | AC-10 | ruff check, ruff format --check, ty check all clean | CI step |
  | AC-11 | Hooks active and passing | hook execution + CI re-run |
  | AC-12 | README install + run instructions verified | manual smoke |

  ## File-level plan

  ```
  src/pitwall/
    app.py                            # PitwallApp(textual.App), screen router
    config.py                         # AppConfig dataclass; resolved paths
    data/
      models.py                       # Pydantic: Race, Driver, Constructor, Result, Qualifying, DriverStanding, ConstructorStanding
      cache.py                        # SQLiteCache (write-through, source-of-truth)
      jolpica.py                      # JolpicaClient (httpx.AsyncClient)
      schema/
        001-initial.sql               # all v0.1 tables
    screens/
      home.py
      schedule.py
      standings.py
      results.py
      profile.py
    workers/
      jolpica_sync.py                 # @work decorator; full-season pull on first launch + stale refresh

  tests/
    conftest.py                       # fixtures: temp SQLite, fake clock, response snapshots
    fixtures/                         # JSON snapshots from lab/02 for tests
    data/
      test_models.py
      test_cache.py
      test_jolpica.py
    screens/
      test_home.py
      test_schedule.py
      test_standings.py
      test_results.py
      test_profile.py
    workers/
      test_jolpica_sync.py
    test_smoke.py
    test_offline.py

  .github/workflows/ci.yml            # ruff + ty + pytest --cov ≥ 75% on changed
  ```

  ## Test strategy

  Per design spec §3.6:
  - Data clients: `respx` mocks for httpx. Fixtures from `lab/02-jolpica-eval/prototype/responses/`.
  - Cache: real SQLite in temp file (in-memory has different concurrency semantics; we use temp file for parity with prod).
  - Models: Pydantic against fixtures.
  - Workers: fake clock (`freezegun` or stdlib `unittest.mock.patch`).
  - Screens: `pytest-textual-snapshot` against in-memory cache fixture.
  - Smoke: launch and exit with `--once` flag.

  ## Risks (this iteration)

  | Risk | Mitigation |
  |---|---|
  | Pydantic v2 model design proves brittle for Jolpica's nested response shapes | Snapshots from spike are committed; tests run against real shapes from day 1 |
  | Textual snapshot tests are flaky across versions | Pin `textual` exact version in pyproject.toml |
  | SQLite schema requires migration mid-iteration | YAGNI — `001-initial.sql` is the only file; if schema changes during iteration, edit it (no live data yet) |
  | Workers leak coroutines on shutdown | Use Textual's `@work(thread=False)` + screen `unmount` cancellation hook |

  ## Out of scope

  - v0.2/0.3/v1.0 features (track map, timing tower, strategy mini-game)
  - PyPI publish, Homebrew formula
  - Telemetry / multi-window
  - i18n
  - Auto-update
  ```

- [ ] **Step 8.3: Stage and commit**

  ```bash
  git add build/workflows/01-season-tracker/
  git commit -m "$(cat <<'EOF'
  docs(spec): 01-season-tracker iteration SPEC

  Planner output for the v0.1 build iteration. Defines scope (12 ACs
  from design spec §5.1), file-level plan (Pydantic models, SQLite
  cache, Jolpica client, Textual screens, worker), test strategy
  (respx for HTTP mock, real SQLite for cache, snapshot tests for
  screens), and risks specific to this iteration.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  git push
  ```

### Task 9: Add CI workflow + dev deps

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `pyproject.toml` (add full dev deps)
- Modify: `uv.lock` (auto)

- [ ] **Step 9.1: Add v0.1 dev dependencies**

  Run:
  ```bash
  uv add --dev pytest pytest-asyncio pytest-cov respx pytest-textual-snapshot ruff
  uv add textual httpx pydantic
  ```
  Note: `httpx` was added as a dev dep during the spike — Steps 9.1 promotes it to a runtime dep.

- [ ] **Step 9.2: Verify pyproject.toml**

  Read `pyproject.toml`. Expected: `dependencies = [textual, httpx, pydantic]`; `[dependency-groups] dev = [pytest, pytest-asyncio, pytest-cov, respx, pytest-textual-snapshot, ruff]`. (`ty` is invoked via `uvx ty check` so doesn't need to be a dep.)

- [ ] **Step 9.3: Add pytest config to pyproject.toml**

  Edit `pyproject.toml` and append:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  asyncio_mode = "auto"
  markers = [
    "smoke: end-to-end smoke tests (not run on every commit)",
  ]

  [tool.coverage.run]
  source = ["src/pitwall"]
  branch = true

  [tool.coverage.report]
  show_missing = true
  ```

- [ ] **Step 9.4: Create `.github/workflows/ci.yml`**

  ```yaml
  name: CI

  on:
    push:
      branches: [main]
    pull_request:
      branches: [main]

  jobs:
    test:
      runs-on: ${{ matrix.os }}
      strategy:
        matrix:
          os: [ubuntu-latest, macos-latest]
        fail-fast: false
      steps:
        - uses: actions/checkout@v4
          with:
            fetch-depth: 0   # need history for changed-lines coverage diff

        - name: Install uv
          uses: astral-sh/setup-uv@v3
          with:
            enable-cache: true

        - name: Install Python 3.13
          run: uv python install 3.13

        - name: Sync deps
          run: uv sync --all-extras --dev

        - name: Lint (ruff check)
          run: uv run ruff check .

        - name: Format (ruff format --check)
          run: uv run ruff format --check .

        - name: Type check (ty)
          run: uvx ty check src tests

        - name: Run tests with coverage
          run: uv run pytest --cov --cov-report=term --cov-report=xml

        - name: Enforce 75% on changed lines (PRs only)
          if: github.event_name == 'pull_request'
          run: |
            uv run python -m pip install diff-cover
            uv run diff-cover coverage.xml --compare-branch=origin/main --fail-under=75
  ```

- [ ] **Step 9.5: Stage and commit**

  ```bash
  git add pyproject.toml uv.lock .github/workflows/ci.yml
  git commit -m "$(cat <<'EOF'
  build(ci): add GitHub Actions workflow + v0.1 dependencies

  Dependencies (runtime): textual, httpx, pydantic.
  Dependencies (dev): pytest, pytest-asyncio, pytest-cov, respx,
  pytest-textual-snapshot, ruff. ty is invoked via `uvx ty check`.

  CI workflow:
  - Triggers on push to main and PRs to main
  - Matrix: ubuntu-latest + macos-latest
  - Steps: ruff check, ruff format --check, ty check, pytest --cov
  - On PRs only: diff-cover enforces 75% coverage on changed lines

  Per design spec §4.4 the CI gate lands in the v0.1 iteration's
  commit (its first meaningful moment — there's code to run it on).

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  git push
  ```

### Task 10: Implement `data/models.py` (Pydantic models, TDD)

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/data/__init__.py`
- Create: `tests/data/test_models.py`
- Create: `tests/conftest.py`
- Create: `tests/fixtures/.gitkeep`
- Create: `src/pitwall/data/__init__.py`
- Create: `src/pitwall/data/models.py`
- Copy: response snapshots from `lab/02-jolpica-eval/prototype/responses/` → `tests/fixtures/jolpica/`

**Why:** Pydantic models are the validated data contract between client → cache → screens. TDD: each model gets a failing test from a real Jolpica fixture first.

- [ ] **Step 10.1: Set up test scaffolding**

  Run:
  ```bash
  mkdir -p tests/data tests/screens tests/workers tests/fixtures/jolpica
  touch tests/__init__.py tests/data/__init__.py tests/screens/__init__.py tests/workers/__init__.py
  ```

- [ ] **Step 10.2: Copy fixtures from the spike**

  Run:
  ```bash
  cp lab/02-jolpica-eval/prototype/responses/*.json tests/fixtures/jolpica/
  ```

- [ ] **Step 10.3: Create `tests/conftest.py`**

  ```python
  """Shared pytest fixtures."""

  from __future__ import annotations

  import json
  from pathlib import Path

  import pytest

  FIXTURES = Path(__file__).parent / "fixtures" / "jolpica"


  @pytest.fixture
  def fixture_loader():
      """Returns a callable: fixture_loader('races_2024') -> dict."""

      def load(name: str) -> dict:
          path = FIXTURES / f"{name}.json"
          return json.loads(path.read_text())

      return load
  ```

- [ ] **Step 10.4: Write the failing test for `Race`**

  Create `tests/data/test_models.py`:
  ```python
  """Tests for Pydantic models in src/pitwall/data/models.py."""

  from __future__ import annotations

  import pytest

  from pitwall.data.models import Race


  def test_race_parses_from_jolpica_2024(fixture_loader):
      data = fixture_loader("races_2024")
      races_raw = data["MRData"]["RaceTable"]["Races"]
      assert len(races_raw) > 0

      race = Race.from_jolpica(races_raw[0])

      assert race.season == 2024
      assert race.round >= 1
      assert race.name
      assert race.circuit_id
      assert race.date  # date object
  ```

- [ ] **Step 10.5: Run the test (FAIL)**

  Run: `uv run pytest tests/data/test_models.py -v`
  Expected: FAIL with `ModuleNotFoundError: No module named 'pitwall.data.models'`.

- [ ] **Step 10.6: Implement minimal `Race`**

  Create `src/pitwall/data/__init__.py` (empty file).

  Create `src/pitwall/data/models.py`:
  ```python
  """Pydantic models — the validated data contract for v0.1 surfaces."""

  from __future__ import annotations

  from datetime import date as date_type
  from typing import Self

  from pydantic import BaseModel, Field


  class Race(BaseModel):
      """A single race in a season."""

      season: int
      round: int
      name: str = Field(alias="raceName")
      circuit_id: str
      date: date_type

      model_config = {"populate_by_name": True}

      @classmethod
      def from_jolpica(cls, raw: dict) -> Self:
          return cls(
              season=int(raw["season"]),
              round=int(raw["round"]),
              raceName=raw["raceName"],
              circuit_id=raw["Circuit"]["circuitId"],
              date=date_type.fromisoformat(raw["date"]),
          )
  ```

- [ ] **Step 10.7: Run the test (PASS)**

  Run: `uv run pytest tests/data/test_models.py::test_race_parses_from_jolpica_2024 -v`
  Expected: PASS.

- [ ] **Step 10.8: Add tests + impl for Driver, Constructor, Result, Qualifying, DriverStanding, ConstructorStanding**

  Append to `tests/data/test_models.py`:
  ```python
  def test_driver_parses(fixture_loader):
      data = fixture_loader("drivers_2024")
      d = data["MRData"]["DriverTable"]["Drivers"][0]
      from pitwall.data.models import Driver
      driver = Driver.from_jolpica(d)
      assert driver.driver_id
      assert driver.given_name
      assert driver.family_name


  def test_constructor_parses(fixture_loader):
      data = fixture_loader("constructors_2024")
      c = data["MRData"]["ConstructorTable"]["Constructors"][0]
      from pitwall.data.models import Constructor
      con = Constructor.from_jolpica(c)
      assert con.constructor_id
      assert con.name
      assert con.nationality


  def test_result_parses(fixture_loader):
      data = fixture_loader("results_2024")
      race_results = data["MRData"]["RaceTable"]["Races"][0]["Results"]
      from pitwall.data.models import Result
      r = Result.from_jolpica(race_results[0], season=2024, round=1)
      assert r.position >= 1
      assert r.driver_id
      assert r.constructor_id


  def test_driver_standing_parses(fixture_loader):
      data = fixture_loader("driverStandings_2024")
      lst = data["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"]
      from pitwall.data.models import DriverStanding
      ds = DriverStanding.from_jolpica(lst[0], season=2024, round=int(data["MRData"]["StandingsTable"]["StandingsLists"][0]["round"]))
      assert ds.points >= 0
      assert ds.position >= 1


  def test_constructor_standing_parses(fixture_loader):
      data = fixture_loader("constructorStandings_2024")
      lst = data["MRData"]["StandingsTable"]["StandingsLists"][0]["ConstructorStandings"]
      from pitwall.data.models import ConstructorStanding
      cs = ConstructorStanding.from_jolpica(lst[0], season=2024, round=int(data["MRData"]["StandingsTable"]["StandingsLists"][0]["round"]))
      assert cs.points >= 0
      assert cs.position >= 1
  ```

  Append to `src/pitwall/data/models.py`:
  ```python
  class Driver(BaseModel):
      driver_id: str
      given_name: str
      family_name: str
      nationality: str | None = None
      dob: date_type | None = None

      @classmethod
      def from_jolpica(cls, raw: dict) -> Self:
          return cls(
              driver_id=raw["driverId"],
              given_name=raw["givenName"],
              family_name=raw["familyName"],
              nationality=raw.get("nationality"),
              dob=date_type.fromisoformat(raw["dateOfBirth"]) if "dateOfBirth" in raw else None,
          )


  class Constructor(BaseModel):
      constructor_id: str
      name: str
      nationality: str

      @classmethod
      def from_jolpica(cls, raw: dict) -> Self:
          return cls(
              constructor_id=raw["constructorId"],
              name=raw["name"],
              nationality=raw["nationality"],
          )


  class Result(BaseModel):
      season: int
      round: int
      driver_id: str
      constructor_id: str
      position: int
      points: float
      status: str
      grid: int | None = None
      laps: int | None = None

      @classmethod
      def from_jolpica(cls, raw: dict, *, season: int, round: int) -> Self:
          return cls(
              season=season,
              round=round,
              driver_id=raw["Driver"]["driverId"],
              constructor_id=raw["Constructor"]["constructorId"],
              position=int(raw["position"]),
              points=float(raw["points"]),
              status=raw["status"],
              grid=int(raw["grid"]) if "grid" in raw else None,
              laps=int(raw["laps"]) if "laps" in raw else None,
          )


  class DriverStanding(BaseModel):
      season: int
      round: int
      driver_id: str
      points: float
      position: int
      wins: int

      @classmethod
      def from_jolpica(cls, raw: dict, *, season: int, round: int) -> Self:
          return cls(
              season=season,
              round=round,
              driver_id=raw["Driver"]["driverId"],
              points=float(raw["points"]),
              position=int(raw["position"]),
              wins=int(raw["wins"]),
          )


  class ConstructorStanding(BaseModel):
      season: int
      round: int
      constructor_id: str
      points: float
      position: int
      wins: int

      @classmethod
      def from_jolpica(cls, raw: dict, *, season: int, round: int) -> Self:
          return cls(
              season=season,
              round=round,
              constructor_id=raw["Constructor"]["constructorId"],
              points=float(raw["points"]),
              position=int(raw["position"]),
              wins=int(raw["wins"]),
          )
  ```

- [ ] **Step 10.9: Run all model tests (PASS)**

  Run: `uv run pytest tests/data/test_models.py -v`
  Expected: 6 tests PASS.

- [ ] **Step 10.10: Run linters**

  Run: `uv run ruff check src tests && uv run ruff format src tests && uvx ty check src tests`
  Fix any reported issues. (`ruff format` will format in place; commit the formatted version.)

- [ ] **Step 10.11: Stage, commit, push notes-1.md**

  Create `build/workflows/01-season-tracker/02-implement/notes-1.md`:
  ```markdown
  # Implementer notes — cycle 1

  ## Spec interpretation

  Started with `data/models.py` per file-level plan. TDD: each model
  has a fixture-driven test before implementation.

  ## Decisions

  - Used Pydantic v2 `model_config = {"populate_by_name": True}` to
    accept both Jolpica's camelCase ("raceName") and our snake_case ("name").
  - `from_jolpica` classmethod per model — keeps the schema-mapping
    logic next to the model definition; clients call this not the constructor.
  - `Result`, `DriverStanding`, `ConstructorStanding` take `season` + `round`
    as keyword args because Jolpica's response nests those at the parent level.

  ## Assumptions

  - Jolpica's `dateOfBirth` field is always ISO-8601. Fixtures confirm.
  - `nationality` may be missing on legacy drivers (defensive; Optional).

  ## Open items

  - SQLite schema (next task); column types map to Pydantic types directly.

  ## Files touched

  - `src/pitwall/data/__init__.py` (new)
  - `src/pitwall/data/models.py` (new)
  - `tests/__init__.py`, `tests/conftest.py` (new)
  - `tests/data/__init__.py`, `tests/data/test_models.py` (new)
  - `tests/fixtures/jolpica/*.json` (copied from lab spike)
  ```

  ```bash
  git add tests/ src/pitwall/data/ build/workflows/01-season-tracker/02-implement/notes-1.md
  git commit -m "$(cat <<'EOF'
  feat(data): Pydantic models for Jolpica responses (Race, Driver, …)

  Six models with from_jolpica classmethods that parse the spike's
  canonical response fixtures. Tests run against the actual fixture
  shapes — not stubs — so schema changes will surface immediately.

  TDD: each model has a failing test before its implementation.
  Coverage: 6 model parse tests, all green. ruff + ty clean.

  Implementer notes: build/workflows/01-season-tracker/02-implement/notes-1.md

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  git push
  ```

### Task 11: Implement `data/cache.py` + `data/schema/001-initial.sql` (TDD)

**Files:**
- Create: `tests/data/test_cache.py`
- Create: `src/pitwall/data/schema/001-initial.sql`
- Create: `src/pitwall/data/cache.py`

- [ ] **Step 11.1: Write failing test for SQLiteCache.upsert_race + get_races**

  Create `tests/data/test_cache.py`:
  ```python
  """Tests for SQLiteCache."""

  from __future__ import annotations

  from datetime import date

  import pytest

  from pitwall.data.cache import SQLiteCache
  from pitwall.data.models import Race


  @pytest.fixture
  def cache(tmp_path):
      db_path = tmp_path / "test.db"
      c = SQLiteCache(db_path)
      c.migrate()
      return c


  def test_upsert_and_get_races(cache):
      r1 = Race(season=2024, round=1, name="Bahrain GP", circuit_id="bahrain", date=date(2024, 3, 2))
      r2 = Race(season=2024, round=2, name="Saudi Arabian GP", circuit_id="jeddah", date=date(2024, 3, 9))

      cache.upsert_races([r1, r2])
      got = cache.get_races(season=2024)

      assert len(got) == 2
      assert got[0].round == 1
      assert got[0].name == "Bahrain GP"
      assert got[1].round == 2


  def test_upsert_is_idempotent(cache):
      r = Race(season=2024, round=1, name="Bahrain GP", circuit_id="bahrain", date=date(2024, 3, 2))
      cache.upsert_races([r])
      cache.upsert_races([r])  # duplicate
      assert len(cache.get_races(season=2024)) == 1


  def test_last_fetch_recorded(cache):
      from datetime import datetime, UTC
      r = Race(season=2024, round=1, name="Bahrain GP", circuit_id="bahrain", date=date(2024, 3, 2))
      cache.upsert_races([r])
      ts = cache.last_fetch("races", key="2024")
      assert ts is not None
      # within last 5 seconds
      assert (datetime.now(UTC) - ts).total_seconds() < 5
  ```

- [ ] **Step 11.2: Run tests (FAIL)**

  Run: `uv run pytest tests/data/test_cache.py -v`
  Expected: ModuleNotFoundError or ImportError.

- [ ] **Step 11.3: Create the schema SQL**

  Run: `mkdir -p src/pitwall/data/schema`

  Create `src/pitwall/data/schema/001-initial.sql`:
  ```sql
  -- v0.1 initial schema. Migrations are flat numbered files (no framework).

  CREATE TABLE IF NOT EXISTS races (
    season       INTEGER NOT NULL,
    round        INTEGER NOT NULL,
    name         TEXT    NOT NULL,
    circuit_id   TEXT    NOT NULL,
    date         TEXT    NOT NULL,  -- ISO-8601 date string
    PRIMARY KEY (season, round)
  );

  CREATE TABLE IF NOT EXISTS drivers (
    driver_id    TEXT    PRIMARY KEY,
    given_name   TEXT    NOT NULL,
    family_name  TEXT    NOT NULL,
    nationality  TEXT,
    dob          TEXT
  );

  CREATE TABLE IF NOT EXISTS constructors (
    constructor_id  TEXT    PRIMARY KEY,
    name            TEXT    NOT NULL,
    nationality     TEXT    NOT NULL
  );

  CREATE TABLE IF NOT EXISTS results (
    season          INTEGER NOT NULL,
    round           INTEGER NOT NULL,
    driver_id       TEXT    NOT NULL,
    constructor_id  TEXT    NOT NULL,
    position        INTEGER NOT NULL,
    points          REAL    NOT NULL,
    status          TEXT    NOT NULL,
    grid            INTEGER,
    laps            INTEGER,
    PRIMARY KEY (season, round, driver_id)
  );

  CREATE TABLE IF NOT EXISTS standings_drivers (
    season          INTEGER NOT NULL,
    round           INTEGER NOT NULL,
    driver_id       TEXT    NOT NULL,
    points          REAL    NOT NULL,
    position        INTEGER NOT NULL,
    wins            INTEGER NOT NULL,
    PRIMARY KEY (season, round, driver_id)
  );

  CREATE TABLE IF NOT EXISTS standings_constructors (
    season          INTEGER NOT NULL,
    round           INTEGER NOT NULL,
    constructor_id  TEXT    NOT NULL,
    points          REAL    NOT NULL,
    position        INTEGER NOT NULL,
    wins            INTEGER NOT NULL,
    PRIMARY KEY (season, round, constructor_id)
  );

  CREATE TABLE IF NOT EXISTS last_fetch (
    table_name      TEXT    NOT NULL,
    key             TEXT    NOT NULL,
    fetched_at      TEXT    NOT NULL,  -- ISO-8601 datetime
    PRIMARY KEY (table_name, key)
  );

  CREATE INDEX IF NOT EXISTS idx_results_season_round ON results(season, round);
  CREATE INDEX IF NOT EXISTS idx_standings_drivers_season_round ON standings_drivers(season, round);
  CREATE INDEX IF NOT EXISTS idx_standings_constructors_season_round ON standings_constructors(season, round);
  ```

- [ ] **Step 11.4: Implement `data/cache.py`**

  Create `src/pitwall/data/cache.py`:
  ```python
  """SQLiteCache — write-through; source of truth for the UI."""

  from __future__ import annotations

  import sqlite3
  from datetime import UTC, datetime
  from pathlib import Path
  from typing import Iterable

  from pitwall.data.models import (
      Constructor,
      ConstructorStanding,
      Driver,
      DriverStanding,
      Race,
      Result,
  )

  SCHEMA_DIR = Path(__file__).parent / "schema"


  class SQLiteCache:
      def __init__(self, db_path: Path | str) -> None:
          self.db_path = Path(db_path)
          self._conn = sqlite3.connect(self.db_path, isolation_level=None)
          self._conn.execute("PRAGMA foreign_keys = ON")

      def migrate(self) -> None:
          """Apply all migrations in schema/ in order."""
          for sql_file in sorted(SCHEMA_DIR.glob("*.sql")):
              self._conn.executescript(sql_file.read_text())

      # ---- Races ----

      def upsert_races(self, races: Iterable[Race]) -> None:
          rows = [
              (r.season, r.round, r.name, r.circuit_id, r.date.isoformat())
              for r in races
          ]
          self._conn.executemany(
              """INSERT INTO races(season, round, name, circuit_id, date)
                 VALUES (?, ?, ?, ?, ?)
                 ON CONFLICT(season, round) DO UPDATE SET
                   name=excluded.name,
                   circuit_id=excluded.circuit_id,
                   date=excluded.date""",
              rows,
          )
          if rows:
              self._record_fetch("races", str(rows[0][0]))

      def get_races(self, *, season: int) -> list[Race]:
          from datetime import date as date_type
          cur = self._conn.execute(
              "SELECT season, round, name, circuit_id, date FROM races WHERE season = ? ORDER BY round",
              (season,),
          )
          return [
              Race(season=row[0], round=row[1], name=row[2], circuit_id=row[3], date=date_type.fromisoformat(row[4]))
              for row in cur
          ]

      # ---- Drivers ----

      def upsert_drivers(self, drivers: Iterable[Driver]) -> None:
          rows = [
              (d.driver_id, d.given_name, d.family_name, d.nationality, d.dob.isoformat() if d.dob else None)
              for d in drivers
          ]
          self._conn.executemany(
              """INSERT INTO drivers(driver_id, given_name, family_name, nationality, dob)
                 VALUES (?, ?, ?, ?, ?)
                 ON CONFLICT(driver_id) DO UPDATE SET
                   given_name=excluded.given_name,
                   family_name=excluded.family_name,
                   nationality=excluded.nationality,
                   dob=excluded.dob""",
              rows,
          )
          self._record_fetch("drivers", "all")

      def get_drivers(self) -> list[Driver]:
          from datetime import date as date_type
          cur = self._conn.execute(
              "SELECT driver_id, given_name, family_name, nationality, dob FROM drivers ORDER BY family_name"
          )
          return [
              Driver(
                  driver_id=row[0], given_name=row[1], family_name=row[2],
                  nationality=row[3],
                  dob=date_type.fromisoformat(row[4]) if row[4] else None,
              )
              for row in cur
          ]

      def get_driver(self, driver_id: str) -> Driver | None:
          for d in self.get_drivers():
              if d.driver_id == driver_id:
                  return d
          return None

      # ---- Constructors ----

      def upsert_constructors(self, constructors: Iterable[Constructor]) -> None:
          rows = [(c.constructor_id, c.name, c.nationality) for c in constructors]
          self._conn.executemany(
              """INSERT INTO constructors(constructor_id, name, nationality)
                 VALUES (?, ?, ?)
                 ON CONFLICT(constructor_id) DO UPDATE SET
                   name=excluded.name,
                   nationality=excluded.nationality""",
              rows,
          )
          self._record_fetch("constructors", "all")

      def get_constructors(self) -> list[Constructor]:
          cur = self._conn.execute(
              "SELECT constructor_id, name, nationality FROM constructors ORDER BY name"
          )
          return [Constructor(constructor_id=row[0], name=row[1], nationality=row[2]) for row in cur]

      def get_constructor(self, constructor_id: str) -> Constructor | None:
          for c in self.get_constructors():
              if c.constructor_id == constructor_id:
                  return c
          return None

      # ---- Results ----

      def upsert_results(self, results: Iterable[Result]) -> None:
          rows = [
              (r.season, r.round, r.driver_id, r.constructor_id, r.position, r.points, r.status, r.grid, r.laps)
              for r in results
          ]
          self._conn.executemany(
              """INSERT INTO results(season, round, driver_id, constructor_id, position, points, status, grid, laps)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                 ON CONFLICT(season, round, driver_id) DO UPDATE SET
                   constructor_id=excluded.constructor_id,
                   position=excluded.position,
                   points=excluded.points,
                   status=excluded.status,
                   grid=excluded.grid,
                   laps=excluded.laps""",
              rows,
          )
          if rows:
              self._record_fetch("results", f"{rows[0][0]}-{rows[0][1]}")

      def get_results(self, *, season: int, round: int | None = None) -> list[Result]:
          if round is None:
              cur = self._conn.execute(
                  "SELECT season, round, driver_id, constructor_id, position, points, status, grid, laps "
                  "FROM results WHERE season = ? ORDER BY round, position",
                  (season,),
              )
          else:
              cur = self._conn.execute(
                  "SELECT season, round, driver_id, constructor_id, position, points, status, grid, laps "
                  "FROM results WHERE season = ? AND round = ? ORDER BY position",
                  (season, round),
              )
          return [
              Result(
                  season=row[0], round=row[1], driver_id=row[2], constructor_id=row[3],
                  position=row[4], points=row[5], status=row[6],
                  grid=row[7], laps=row[8],
              )
              for row in cur
          ]

      # ---- Standings ----

      def upsert_driver_standings(self, items: Iterable[DriverStanding]) -> None:
          rows = [(s.season, s.round, s.driver_id, s.points, s.position, s.wins) for s in items]
          self._conn.executemany(
              """INSERT INTO standings_drivers(season, round, driver_id, points, position, wins)
                 VALUES (?, ?, ?, ?, ?, ?)
                 ON CONFLICT(season, round, driver_id) DO UPDATE SET
                   points=excluded.points,
                   position=excluded.position,
                   wins=excluded.wins""",
              rows,
          )
          if rows:
              self._record_fetch("standings_drivers", f"{rows[0][0]}-{rows[0][1]}")

      def get_driver_standings(self, *, season: int, round: int | None = None) -> list[DriverStanding]:
          if round is None:
              # Latest round in the season
              cur = self._conn.execute(
                  "SELECT season, round, driver_id, points, position, wins FROM standings_drivers "
                  "WHERE season = ? AND round = (SELECT MAX(round) FROM standings_drivers WHERE season = ?) "
                  "ORDER BY position",
                  (season, season),
              )
          else:
              cur = self._conn.execute(
                  "SELECT season, round, driver_id, points, position, wins FROM standings_drivers "
                  "WHERE season = ? AND round = ? ORDER BY position",
                  (season, round),
              )
          return [
              DriverStanding(season=row[0], round=row[1], driver_id=row[2], points=row[3], position=row[4], wins=row[5])
              for row in cur
          ]

      def upsert_constructor_standings(self, items: Iterable[ConstructorStanding]) -> None:
          rows = [(s.season, s.round, s.constructor_id, s.points, s.position, s.wins) for s in items]
          self._conn.executemany(
              """INSERT INTO standings_constructors(season, round, constructor_id, points, position, wins)
                 VALUES (?, ?, ?, ?, ?, ?)
                 ON CONFLICT(season, round, constructor_id) DO UPDATE SET
                   points=excluded.points,
                   position=excluded.position,
                   wins=excluded.wins""",
              rows,
          )
          if rows:
              self._record_fetch("standings_constructors", f"{rows[0][0]}-{rows[0][1]}")

      def get_constructor_standings(self, *, season: int, round: int | None = None) -> list[ConstructorStanding]:
          if round is None:
              cur = self._conn.execute(
                  "SELECT season, round, constructor_id, points, position, wins FROM standings_constructors "
                  "WHERE season = ? AND round = (SELECT MAX(round) FROM standings_constructors WHERE season = ?) "
                  "ORDER BY position",
                  (season, season),
              )
          else:
              cur = self._conn.execute(
                  "SELECT season, round, constructor_id, points, position, wins FROM standings_constructors "
                  "WHERE season = ? AND round = ? ORDER BY position",
                  (season, round),
              )
          return [
              ConstructorStanding(season=row[0], round=row[1], constructor_id=row[2], points=row[3], position=row[4], wins=row[5])
              for row in cur
          ]

      # ---- Last-fetch tracking ----

      def _record_fetch(self, table_name: str, key: str) -> None:
          self._conn.execute(
              """INSERT INTO last_fetch(table_name, key, fetched_at) VALUES (?, ?, ?)
                 ON CONFLICT(table_name, key) DO UPDATE SET fetched_at=excluded.fetched_at""",
              (table_name, key, datetime.now(UTC).isoformat()),
          )

      def last_fetch(self, table_name: str, *, key: str) -> datetime | None:
          cur = self._conn.execute(
              "SELECT fetched_at FROM last_fetch WHERE table_name = ? AND key = ?",
              (table_name, key),
          )
          row = cur.fetchone()
          if not row:
              return None
          return datetime.fromisoformat(row[0])

      def close(self) -> None:
          self._conn.close()
  ```

- [ ] **Step 11.5: Run cache tests (PASS)**

  Run: `uv run pytest tests/data/test_cache.py -v`
  Expected: 3 PASS.

- [ ] **Step 11.6: Add tests for the other upsert/get pairs**

  Append to `tests/data/test_cache.py`:
  ```python
  def test_upsert_and_get_drivers(cache):
      from pitwall.data.models import Driver
      cache.upsert_drivers([
          Driver(driver_id="hamilton", given_name="Lewis", family_name="Hamilton", nationality="British"),
          Driver(driver_id="verstappen", given_name="Max", family_name="Verstappen", nationality="Dutch"),
      ])
      got = cache.get_drivers()
      assert len(got) == 2
      assert cache.get_driver("hamilton").family_name == "Hamilton"
      assert cache.get_driver("nobody") is None


  def test_upsert_and_get_constructors(cache):
      from pitwall.data.models import Constructor
      cache.upsert_constructors([
          Constructor(constructor_id="ferrari", name="Ferrari", nationality="Italian"),
          Constructor(constructor_id="mercedes", name="Mercedes", nationality="German"),
      ])
      got = cache.get_constructors()
      assert len(got) == 2
      assert cache.get_constructor("ferrari").name == "Ferrari"
      assert cache.get_constructor("nobody") is None


  def test_upsert_and_get_results(cache):
      from pitwall.data.models import Result
      cache.upsert_results([
          Result(season=2026, round=1, driver_id="ham", constructor_id="ferr", position=1, points=25.0, status="Finished"),
          Result(season=2026, round=1, driver_id="ver", constructor_id="rbr",  position=2, points=18.0, status="Finished"),
          Result(season=2026, round=2, driver_id="ham", constructor_id="ferr", position=3, points=15.0, status="Finished"),
      ])
      assert len(cache.get_results(season=2026)) == 3
      assert len(cache.get_results(season=2026, round=1)) == 2
      assert cache.get_results(season=2026, round=1)[0].position == 1


  def test_upsert_and_get_driver_standings(cache):
      from pitwall.data.models import DriverStanding
      cache.upsert_driver_standings([
          DriverStanding(season=2026, round=1, driver_id="ham", points=25.0, position=1, wins=1),
          DriverStanding(season=2026, round=2, driver_id="ham", points=43.0, position=1, wins=1),  # latest round
      ])
      latest = cache.get_driver_standings(season=2026)
      assert len(latest) == 1
      assert latest[0].round == 2
      assert latest[0].points == 43.0


  def test_upsert_and_get_constructor_standings(cache):
      from pitwall.data.models import ConstructorStanding
      cache.upsert_constructor_standings([
          ConstructorStanding(season=2026, round=1, constructor_id="ferr", points=43.0, position=1, wins=1),
          ConstructorStanding(season=2026, round=2, constructor_id="ferr", points=80.0, position=1, wins=2),
      ])
      latest = cache.get_constructor_standings(season=2026)
      assert latest[0].round == 2
      assert latest[0].points == 80.0
  ```

  Run: `uv run pytest tests/data/test_cache.py -v` — all 8 cache tests PASS.

- [ ] **Step 11.7: Run lint + format + typecheck**

  ```bash
  uv run ruff check src tests
  uv run ruff format src tests
  uvx ty check src tests
  ```

- [ ] **Step 11.8: Commit + push**

  Append to `build/workflows/01-season-tracker/02-implement/notes-1.md` (cycle 1 continues):
  ```markdown

  ## Cache layer

  - Schema: 7 tables (`races`, `drivers`, `constructors`, `results`,
    `standings_drivers`, `standings_constructors`, `last_fetch`).
  - Sqlite3 stdlib; `isolation_level=None` for autocommit semantics
    (we don't need transactions for v0.1's single-writer model).
  - Upsert via `ON CONFLICT DO UPDATE`; idempotent by design.
  - `last_fetch(table_name, key, fetched_at)` for staleness checks (drives AC-08).
  ```

  ```bash
  git add src/pitwall/data/schema/ src/pitwall/data/cache.py \
          tests/data/test_cache.py \
          build/workflows/01-season-tracker/02-implement/notes-1.md
  git commit -m "$(cat <<'EOF'
  feat(data): SQLiteCache (write-through) + initial schema

  cache.py wraps stdlib sqlite3, provides upsert_X/get_X for each
  v0.1 entity, and tracks per-key fetch timestamps for staleness UX.
  schema/001-initial.sql defines 7 tables with composite PKs and
  indexes on (season, round) lookup paths.

  Idempotent upserts via ON CONFLICT; tested with duplicate inserts.
  All cache tests green. ruff + ty clean.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  git push
  ```

### Task 12: Implement `data/jolpica.py` (TDD with respx)

**Files:**
- Create: `tests/data/test_jolpica.py`
- Create: `src/pitwall/data/jolpica.py`

- [ ] **Step 12.1: Write failing test using respx + fixtures**

  Create `tests/data/test_jolpica.py`:
  ```python
  """Tests for JolpicaClient."""

  from __future__ import annotations

  import json
  from pathlib import Path

  import httpx
  import pytest
  import respx

  from pitwall.data.jolpica import JolpicaClient

  FIXTURES = Path(__file__).parent.parent / "fixtures" / "jolpica"


  @pytest.mark.asyncio
  async def test_get_races_for_season():
      raw = json.loads((FIXTURES / "races_2024.json").read_text())
      with respx.mock(base_url="https://api.jolpi.ca/ergast/f1") as mock:
          mock.get("/2024.json").mock(return_value=httpx.Response(200, json=raw))
          async with JolpicaClient() as client:
              races = await client.get_races(season=2024)
      assert len(races) > 0
      assert races[0].season == 2024


  @pytest.mark.asyncio
  async def test_get_drivers_for_season():
      raw = json.loads((FIXTURES / "drivers_2024.json").read_text())
      with respx.mock(base_url="https://api.jolpi.ca/ergast/f1") as mock:
          mock.get("/2024/drivers.json").mock(return_value=httpx.Response(200, json=raw))
          async with JolpicaClient() as client:
              drivers = await client.get_drivers(season=2024)
      assert len(drivers) > 0
      assert all(d.driver_id for d in drivers)
  ```

- [ ] **Step 12.2: Run (FAIL)**

  `uv run pytest tests/data/test_jolpica.py -v` → ImportError.

- [ ] **Step 12.3: Implement JolpicaClient**

  Create `src/pitwall/data/jolpica.py`:
  ```python
  """JolpicaClient — async Jolpica-F1 wrapper. Returns Pydantic models."""

  from __future__ import annotations

  from typing import Self

  import httpx

  from pitwall.data.models import (
      Constructor,
      ConstructorStanding,
      Driver,
      DriverStanding,
      Race,
      Result,
  )

  BASE_URL = "https://api.jolpi.ca/ergast/f1"
  USER_AGENT = "pitwall/0.1"


  class JolpicaClient:
      def __init__(self, base_url: str = BASE_URL) -> None:
          self._base_url = base_url
          self._client = httpx.AsyncClient(
              base_url=base_url,
              headers={"User-Agent": USER_AGENT},
              timeout=10.0,
          )

      async def __aenter__(self) -> Self:
          return self

      async def __aexit__(self, *exc) -> None:
          await self._client.aclose()

      async def _get(self, path: str) -> dict:
          r = await self._client.get(path)
          r.raise_for_status()
          return r.json()

      async def get_races(self, *, season: int) -> list[Race]:
          data = await self._get(f"/{season}.json")
          races = data["MRData"]["RaceTable"]["Races"]
          return [Race.from_jolpica(r) for r in races]

      async def get_drivers(self, *, season: int) -> list[Driver]:
          data = await self._get(f"/{season}/drivers.json")
          drivers = data["MRData"]["DriverTable"]["Drivers"]
          return [Driver.from_jolpica(d) for d in drivers]

      async def get_constructors(self, *, season: int) -> list[Constructor]:
          data = await self._get(f"/{season}/constructors.json")
          cons = data["MRData"]["ConstructorTable"]["Constructors"]
          return [Constructor.from_jolpica(c) for c in cons]

      async def get_results(self, *, season: int, round: int | None = None) -> list[Result]:
          path = f"/{season}/results.json?limit=100" if round is None else f"/{season}/{round}/results.json"
          data = await self._get(path)
          out: list[Result] = []
          for race in data["MRData"]["RaceTable"]["Races"]:
              s = int(race["season"])
              rd = int(race["round"])
              for raw in race.get("Results", []):
                  out.append(Result.from_jolpica(raw, season=s, round=rd))
          return out

      async def get_driver_standings(self, *, season: int) -> list[DriverStanding]:
          data = await self._get(f"/{season}/driverStandings.json")
          out: list[DriverStanding] = []
          for sl in data["MRData"]["StandingsTable"]["StandingsLists"]:
              s = int(sl["season"])
              rd = int(sl["round"])
              for raw in sl["DriverStandings"]:
                  out.append(DriverStanding.from_jolpica(raw, season=s, round=rd))
          return out

      async def get_constructor_standings(self, *, season: int) -> list[ConstructorStanding]:
          data = await self._get(f"/{season}/constructorStandings.json")
          out: list[ConstructorStanding] = []
          for sl in data["MRData"]["StandingsTable"]["StandingsLists"]:
              s = int(sl["season"])
              rd = int(sl["round"])
              for raw in sl["ConstructorStandings"]:
                  out.append(ConstructorStanding.from_jolpica(raw, season=s, round=rd))
          return out
  ```

- [ ] **Step 12.4: Run tests (PASS)**

  `uv run pytest tests/data/test_jolpica.py -v`

- [ ] **Step 12.5: Lint, format, typecheck, commit, push**

  ```bash
  uv run ruff check src tests && uv run ruff format src tests && uvx ty check src tests
  git add src/pitwall/data/jolpica.py tests/data/test_jolpica.py
  git commit -m "$(cat <<'EOF'
  feat(data): JolpicaClient — async wrapper returning Pydantic models

  httpx.AsyncClient under the hood; one method per v0.1 surface
  (races, drivers, constructors, results, driver/constructor standings).
  Uses respx-mocked fixtures from the spike — no network in tests.

  raise_for_status() on every response; HTTP errors propagate to the
  worker layer where they're converted to "stale" UX.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  git push
  ```

### Task 13: Implement `workers/jolpica_sync.py` (TDD)

**Files:**
- Create: `tests/workers/test_jolpica_sync.py`
- Create: `src/pitwall/workers/__init__.py`
- Create: `src/pitwall/workers/jolpica_sync.py`

- [ ] **Step 13.1: Write failing test**

  Create `tests/workers/test_jolpica_sync.py`:
  ```python
  """Tests for jolpica_sync worker."""

  from __future__ import annotations

  import json
  from pathlib import Path
  from unittest.mock import AsyncMock

  import pytest

  from pitwall.data.cache import SQLiteCache
  from pitwall.workers.jolpica_sync import sync_season

  FIXTURES = Path(__file__).parent.parent / "fixtures" / "jolpica"


  @pytest.mark.asyncio
  async def test_sync_season_populates_cache(tmp_path):
      cache = SQLiteCache(tmp_path / "test.db")
      cache.migrate()

      # Build a mock client that returns parsed fixtures
      from pitwall.data.jolpica import JolpicaClient
      from pitwall.data.models import Race, Driver, Constructor

      races_raw = json.loads((FIXTURES / "races_2024.json").read_text())
      drivers_raw = json.loads((FIXTURES / "drivers_2024.json").read_text())
      constructors_raw = json.loads((FIXTURES / "constructors_2024.json").read_text())

      client = AsyncMock(spec=JolpicaClient)
      client.get_races.return_value = [Race.from_jolpica(r) for r in races_raw["MRData"]["RaceTable"]["Races"]]
      client.get_drivers.return_value = [Driver.from_jolpica(d) for d in drivers_raw["MRData"]["DriverTable"]["Drivers"]]
      client.get_constructors.return_value = [Constructor.from_jolpica(c) for c in constructors_raw["MRData"]["ConstructorTable"]["Constructors"]]
      client.get_driver_standings.return_value = []
      client.get_constructor_standings.return_value = []
      client.get_results.return_value = []

      await sync_season(client=client, cache=cache, season=2024)

      assert len(cache.get_races(season=2024)) > 0
  ```

- [ ] **Step 13.2: Implement sync_season**

  Create `src/pitwall/workers/__init__.py` (empty).

  Create `src/pitwall/workers/jolpica_sync.py`:
  ```python
  """jolpica_sync — pulls a full season into the cache."""

  from __future__ import annotations

  from pitwall.data.cache import SQLiteCache
  from pitwall.data.jolpica import JolpicaClient


  async def sync_season(*, client: JolpicaClient, cache: SQLiteCache, season: int) -> None:
      """Full sync of one season's data into the cache."""
      races = await client.get_races(season=season)
      cache.upsert_races(races)

      drivers = await client.get_drivers(season=season)
      cache.upsert_drivers(drivers)

      constructors = await client.get_constructors(season=season)
      cache.upsert_constructors(constructors)

      results = await client.get_results(season=season)
      cache.upsert_results(results)

      ds = await client.get_driver_standings(season=season)
      cache.upsert_driver_standings(ds)

      cs = await client.get_constructor_standings(season=season)
      cache.upsert_constructor_standings(cs)
  ```

- [ ] **Step 13.3: Run, lint, commit, push**

  ```bash
  uv run pytest tests/workers/ -v
  uv run ruff check src tests && uv run ruff format src tests && uvx ty check src tests
  git add src/pitwall/workers/ tests/workers/
  git commit -m "$(cat <<'EOF'
  feat(workers): jolpica_sync — pull full season into cache

  Single coroutine sync_season(client, cache, season). Calls each
  client method, upserts results into cache. Tested against an
  AsyncMock JolpicaClient with parsed fixtures.

  Textual @work decorator gets applied at the screen-mount level
  (Task 15+), not on the sync coroutine itself — keeps the worker
  function pure and unit-testable.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  git push
  ```

### Task 14: Implement `app.py` + `screens/home.py` + `config.py` (TDD with snapshot)

**Files:**
- Create: `src/pitwall/config.py`
- Create: `src/pitwall/app.py`
- Create: `src/pitwall/screens/__init__.py`
- Create: `src/pitwall/screens/home.py`
- Create: `tests/screens/test_home.py`

- [ ] **Step 14.1: Write the home screen snapshot test**

  Create `tests/screens/test_home.py`:
  ```python
  """Tests for the home screen."""

  from __future__ import annotations

  import pytest

  from pitwall.app import PitwallApp


  @pytest.mark.asyncio
  async def test_home_screen_renders():
      app = PitwallApp(headless=True)
      async with app.run_test() as pilot:
          await pilot.pause()
          # Home screen should be the active screen on startup
          assert app.screen.id == "home"


  @pytest.mark.asyncio
  async def test_home_screen_snapshot(snap_compare):
      """Snapshot test — fails if visual changes."""
      assert snap_compare("./tests/screens/test_home.py::PitwallApp")
  ```

  Note: full snapshot tests require additional setup; treat AC-02's snapshot test as "interaction-light" for now and add the `snap_compare` fixture in a follow-up step if `pytest-textual-snapshot` requires more wiring.

- [ ] **Step 14.2: Implement `config.py`**

  Create `src/pitwall/config.py`:
  ```python
  """App config — paths and runtime settings."""

  from __future__ import annotations

  import os
  from dataclasses import dataclass
  from pathlib import Path


  def _data_dir() -> Path:
      """Resolve the data directory per platform."""
      if env := os.environ.get("PITWALL_DATA_DIR"):
          return Path(env)
      return Path.home() / ".local" / "share" / "pitwall"


  @dataclass(frozen=True)
  class AppConfig:
      data_dir: Path
      cache_db: Path
      refresh_interval_seconds: int = 3600  # 1 hour TTL for season data

      @classmethod
      def default(cls) -> "AppConfig":
          dd = _data_dir()
          dd.mkdir(parents=True, exist_ok=True)
          return cls(data_dir=dd, cache_db=dd / "pitwall.db")
  ```

- [ ] **Step 14.3: Implement `screens/home.py`**

  Create `src/pitwall/screens/__init__.py` (empty).

  Create `src/pitwall/screens/home.py`:
  ```python
  """Home screen — top-level nav."""

  from __future__ import annotations

  from textual.app import ComposeResult
  from textual.containers import Vertical
  from textual.screen import Screen
  from textual.widgets import Button, Header, Footer, Static


  class HomeScreen(Screen):
      """Main menu."""

      BINDINGS = [
          ("q", "quit", "Quit"),
          ("s", "switch('schedule')", "Schedule"),
          ("t", "switch('standings')", "Standings"),
          ("r", "switch('results')", "Results"),
          ("p", "switch('profile')", "Profile"),
      ]

      def compose(self) -> ComposeResult:
          yield Header(show_clock=False)
          yield Vertical(
              Static("[bold cyan]Pitwall[/] — F1 companion (v0.1)\n", id="title"),
              Button("Schedule", id="schedule"),
              Button("Standings", id="standings"),
              Button("Results", id="results"),
              Button("Profile", id="profile"),
              Static("\n[dim]v0.2: Track Map · v0.3: Live Timing · v1.0: Strategy[/]"),
              id="home-nav",
          )
          yield Footer()

      def action_switch(self, screen_name: str) -> None:
          self.app.push_screen(screen_name)
  ```

- [ ] **Step 14.4: Implement `app.py`**

  Create `src/pitwall/app.py`:
  ```python
  """PitwallApp — Textual App with screen router."""

  from __future__ import annotations

  from textual.app import App

  from pitwall.config import AppConfig
  from pitwall.data.cache import SQLiteCache
  from pitwall.screens.home import HomeScreen


  class PitwallApp(App):
      TITLE = "Pitwall"
      CSS = """
      #title { padding: 1; }
      #home-nav { width: 60; padding: 1 2; }
      """
      SCREENS = {
          "home": HomeScreen,
      }

      def __init__(self, *, config: AppConfig | None = None, **kwargs) -> None:
          super().__init__(**kwargs)
          self.config = config or AppConfig.default()
          self.cache = SQLiteCache(self.config.cache_db)
          self.cache.migrate()

      def on_mount(self) -> None:
          self.push_screen("home")
  ```

- [ ] **Step 14.5: Run, lint, commit, push**

  ```bash
  uv run pytest tests/screens/test_home.py::test_home_screen_renders -v
  uv run ruff check src tests && uv run ruff format src tests && uvx ty check src tests
  git add src/pitwall/config.py src/pitwall/app.py src/pitwall/screens/ tests/screens/test_home.py
  git commit -m "$(cat <<'EOF'
  feat(app): PitwallApp + HomeScreen + AppConfig

  PitwallApp wires a SQLiteCache (auto-migrated) into the app state
  and pushes HomeScreen on mount. HomeScreen has nav buttons +
  keybindings for the four v0.1 screens; v0.2+ pillars shown as
  disabled hints in the footer.

  AppConfig: data_dir resolution (env override → XDG default), cache
  path, refresh interval (1h fixed for v0.1).

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  git push
  ```

### Task 15: Implement `screens/schedule.py` (TDD)

**Files:**
- Create: `tests/screens/test_schedule.py`
- Create: `src/pitwall/screens/schedule.py`
- Modify: `src/pitwall/app.py` (register screen)

- [ ] **Step 15.1: Write failing test**

  Create `tests/screens/test_schedule.py`:
  ```python
  """Tests for the schedule screen."""

  from __future__ import annotations

  from datetime import date

  import pytest

  from pitwall.app import PitwallApp
  from pitwall.config import AppConfig
  from pitwall.data.models import Race


  @pytest.mark.asyncio
  async def test_schedule_renders_seeded_cache(tmp_path):
      config = AppConfig(data_dir=tmp_path, cache_db=tmp_path / "test.db")
      app = PitwallApp(config=config, headless=True)
      app.cache.upsert_races([
          Race(season=2024, round=1, name="Bahrain GP", circuit_id="bahrain", date=date(2024, 3, 2)),
          Race(season=2024, round=2, name="Saudi Arabian GP", circuit_id="jeddah", date=date(2024, 3, 9)),
      ])
      async with app.run_test() as pilot:
          await pilot.press("s")  # switch to schedule
          await pilot.pause()
          assert app.screen.id == "schedule"
          # Crude content check
          rendered = app.screen.render().plain if hasattr(app.screen.render(), "plain") else str(app.screen.render())
          assert "Bahrain" in rendered
  ```

- [ ] **Step 15.2: Implement `screens/schedule.py`**

  Create:
  ```python
  """Schedule screen — current season's race calendar."""

  from __future__ import annotations

  from datetime import date as date_type

  from textual.app import ComposeResult
  from textual.containers import Vertical
  from textual.screen import Screen
  from textual.widgets import DataTable, Footer, Header


  CURRENT_SEASON = 2026


  class ScheduleScreen(Screen):
      BINDINGS = [
          ("escape", "app.pop_screen", "Back"),
          ("q", "quit", "Quit"),
      ]

      def compose(self) -> ComposeResult:
          yield Header(show_clock=False)
          yield Vertical(DataTable(id="schedule-table"))
          yield Footer()

      def on_mount(self) -> None:
          table: DataTable = self.query_one("#schedule-table", DataTable)
          table.add_columns("Round", "Date", "Race", "Circuit", "Status")
          today = date_type.today()
          for r in self.app.cache.get_races(season=CURRENT_SEASON):
              status = "✅ done" if r.date < today else ("⏳ upcoming" if r.date > today else "🟢 today")
              table.add_row(str(r.round), r.date.isoformat(), r.name, r.circuit_id, status)
  ```

- [ ] **Step 15.3: Register in app**

  Edit `src/pitwall/app.py` and update `SCREENS`:
  ```python
  from pitwall.screens.schedule import ScheduleScreen
  ...
  SCREENS = {
      "home": HomeScreen,
      "schedule": ScheduleScreen,
  }
  ```

- [ ] **Step 15.4: Run, commit, push**

  ```bash
  uv run pytest tests/screens/test_schedule.py -v
  uv run ruff check src tests && uv run ruff format src tests && uvx ty check src tests
  git add src/pitwall/app.py src/pitwall/screens/schedule.py tests/screens/test_schedule.py
  git commit -m "feat(screens): schedule screen — DataTable of season races

  Reads from cache.get_races(season=2026); rows show round, date,
  race name, circuit id, and a status icon (done/today/upcoming).
  Test seeds the cache directly; no client involved.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  git push
  ```

### Task 16: Implement `screens/standings.py` (TDD with Tab toggle)

**Files:**
- Create: `tests/screens/test_standings.py`
- Create: `src/pitwall/screens/standings.py`
- Modify: `src/pitwall/app.py` (register screen)

- [ ] **Step 16.1: Write the failing test**

  Create `tests/screens/test_standings.py`:
  ```python
  """Tests for the standings screen."""

  from __future__ import annotations

  import pytest

  from pitwall.app import PitwallApp
  from pitwall.config import AppConfig
  from pitwall.data.models import Constructor, ConstructorStanding, Driver, DriverStanding


  @pytest.mark.asyncio
  async def test_standings_renders_driver_tab(tmp_path):
      config = AppConfig(data_dir=tmp_path, cache_db=tmp_path / "test.db")
      app = PitwallApp(config=config, headless=True)
      app.cache.upsert_drivers([Driver(driver_id="hamilton", given_name="Lewis", family_name="Hamilton")])
      app.cache.upsert_driver_standings([
          DriverStanding(season=2026, round=1, driver_id="hamilton", points=25.0, position=1, wins=1),
      ])
      async with app.run_test() as pilot:
          await pilot.press("t")  # switch to standings (home keybind)
          await pilot.pause()
          assert app.screen.id == "standings"
          rendered = str(app.screen.render())
          assert "Hamilton" in rendered


  @pytest.mark.asyncio
  async def test_standings_tab_toggles_to_constructor(tmp_path):
      config = AppConfig(data_dir=tmp_path, cache_db=tmp_path / "test.db")
      app = PitwallApp(config=config, headless=True)
      app.cache.upsert_constructors([Constructor(constructor_id="ferrari", name="Ferrari", nationality="Italian")])
      app.cache.upsert_constructor_standings([
          ConstructorStanding(season=2026, round=1, constructor_id="ferrari", points=50.0, position=1, wins=1),
      ])
      async with app.run_test() as pilot:
          await pilot.press("t")
          await pilot.pause()
          await pilot.press("tab")  # toggle to constructors pane
          await pilot.pause()
          rendered = str(app.screen.render())
          assert "Ferrari" in rendered
  ```

- [ ] **Step 16.2: Implement `screens/standings.py`**

  Create:
  ```python
  """Standings screen — driver + constructor tables, Tab to toggle."""

  from __future__ import annotations

  from textual.app import ComposeResult
  from textual.screen import Screen
  from textual.widgets import DataTable, Footer, Header, TabbedContent, TabPane

  CURRENT_SEASON = 2026


  class StandingsScreen(Screen):
      BINDINGS = [
          ("escape", "app.pop_screen", "Back"),
          ("q", "quit", "Quit"),
      ]

      def compose(self) -> ComposeResult:
          yield Header(show_clock=False)
          with TabbedContent(initial="drivers"):
              with TabPane("Drivers", id="drivers"):
                  yield DataTable(id="drivers-table")
              with TabPane("Constructors", id="constructors"):
                  yield DataTable(id="constructors-table")
          yield Footer()

      def on_mount(self) -> None:
          # Drivers
          dt: DataTable = self.query_one("#drivers-table", DataTable)
          dt.add_columns("Pos", "Driver", "Points", "Wins")
          drivers = {d.driver_id: d for d in self.app.cache.get_drivers()}
          for s in self.app.cache.get_driver_standings(season=CURRENT_SEASON):
              d = drivers.get(s.driver_id)
              name = f"{d.given_name} {d.family_name}" if d else s.driver_id
              dt.add_row(str(s.position), name, f"{s.points:g}", str(s.wins))

          # Constructors
          ct: DataTable = self.query_one("#constructors-table", DataTable)
          ct.add_columns("Pos", "Constructor", "Points", "Wins")
          cons = {c.constructor_id: c for c in self.app.cache.get_constructors()}
          for s in self.app.cache.get_constructor_standings(season=CURRENT_SEASON):
              c = cons.get(s.constructor_id)
              name = c.name if c else s.constructor_id
              ct.add_row(str(s.position), name, f"{s.points:g}", str(s.wins))
  ```

- [ ] **Step 16.3: Register screen in `app.py`**

  Update `SCREENS` dict:
  ```python
  from pitwall.screens.standings import StandingsScreen
  ...
  SCREENS = {
      "home": HomeScreen,
      "schedule": ScheduleScreen,
      "standings": StandingsScreen,
  }
  ```

- [ ] **Step 16.4: Run, lint, commit, push**

  ```bash
  uv run pytest tests/screens/test_standings.py -v
  uv run ruff check src tests && uv run ruff format src tests && uvx ty check src tests
  git add src/pitwall/screens/standings.py src/pitwall/app.py tests/screens/test_standings.py
  git commit -m "feat(screens): standings screen — driver + constructor tabs

  TabbedContent with two DataTables. Joins standings rows to driver/
  constructor records for display names. Tab key toggles panes (built
  into TabbedContent).

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  git push
  ```

### Task 17: Implement `screens/results.py` (TDD with season-picker)

**Files:**
- Create: `tests/screens/test_results.py`
- Create: `src/pitwall/screens/results.py`
- Modify: `src/pitwall/app.py`

- [ ] **Step 17.1: Failing test**

  Create `tests/screens/test_results.py`:
  ```python
  """Tests for the results screen."""

  from __future__ import annotations

  import pytest

  from pitwall.app import PitwallApp
  from pitwall.config import AppConfig
  from pitwall.data.models import Driver, Race, Result


  @pytest.mark.asyncio
  async def test_results_shows_current_season_default(tmp_path):
      from datetime import date
      config = AppConfig(data_dir=tmp_path, cache_db=tmp_path / "test.db")
      app = PitwallApp(config=config, headless=True)
      app.cache.upsert_races([Race(season=2026, round=1, name="Bahrain GP", circuit_id="bahrain", date=date(2026, 3, 1))])
      app.cache.upsert_drivers([Driver(driver_id="verstappen", given_name="Max", family_name="Verstappen")])
      app.cache.upsert_results([Result(
          season=2026, round=1, driver_id="verstappen", constructor_id="redbull",
          position=1, points=25.0, status="Finished"
      )])
      async with app.run_test() as pilot:
          await pilot.press("r")
          await pilot.pause()
          assert app.screen.id == "results"
          assert "Verstappen" in str(app.screen.render())


  @pytest.mark.asyncio
  async def test_results_season_picker_switches_data(tmp_path):
      from datetime import date
      config = AppConfig(data_dir=tmp_path, cache_db=tmp_path / "test.db")
      app = PitwallApp(config=config, headless=True)
      app.cache.upsert_races([
          Race(season=2024, round=1, name="Bahrain GP 24", circuit_id="bahrain", date=date(2024, 3, 2)),
          Race(season=2026, round=1, name="Bahrain GP 26", circuit_id="bahrain", date=date(2026, 3, 1)),
      ])
      async with app.run_test() as pilot:
          await pilot.press("r")
          await pilot.pause()
          # Default = 2026
          assert "Bahrain GP 26" in str(app.screen.render())
          # Switch to 2024 via the Select widget — implementation uses message-based change
          screen = app.screen
          await screen.set_season(2024)  # public helper on the screen
          await pilot.pause()
          assert "Bahrain GP 24" in str(app.screen.render())
  ```

- [ ] **Step 17.2: Implement `screens/results.py`**

  ```python
  """Results screen — per-race results, season-picker."""

  from __future__ import annotations

  from textual.app import ComposeResult
  from textual.containers import Horizontal, Vertical
  from textual.screen import Screen
  from textual.widgets import DataTable, Footer, Header, Select

  CURRENT_SEASON = 2026
  AVAILABLE_SEASONS = list(range(CURRENT_SEASON, 2019, -1))  # 2026..2020 for v0.1


  class ResultsScreen(Screen):
      BINDINGS = [
          ("escape", "app.pop_screen", "Back"),
          ("q", "quit", "Quit"),
      ]

      def __init__(self) -> None:
          super().__init__()
          self._season = CURRENT_SEASON

      def compose(self) -> ComposeResult:
          yield Header(show_clock=False)
          yield Horizontal(
              Select(
                  options=[(str(y), y) for y in AVAILABLE_SEASONS],
                  value=self._season,
                  prompt="Season",
                  id="season-picker",
              ),
              id="results-controls",
          )
          yield Vertical(DataTable(id="results-table"))
          yield Footer()

      def on_mount(self) -> None:
          self._render_table()

      async def set_season(self, season: int) -> None:
          """Public helper used by tests and Select.Changed handler."""
          self._season = season
          self._render_table()

      def on_select_changed(self, event: Select.Changed) -> None:
          if event.value and event.value != self._season:
              self._season = int(event.value)
              self._render_table()

      def _render_table(self) -> None:
          dt: DataTable = self.query_one("#results-table", DataTable)
          dt.clear(columns=True)
          dt.add_columns("Round", "Race", "Pos", "Driver", "Points", "Status")
          drivers = {d.driver_id: d for d in self.app.cache.get_drivers()}
          races = {r.round: r for r in self.app.cache.get_races(season=self._season)}
          for r in self.app.cache.get_results(season=self._season):
              race = races.get(r.round)
              race_name = race.name if race else f"R{r.round}"
              d = drivers.get(r.driver_id)
              name = f"{d.given_name} {d.family_name}" if d else r.driver_id
              dt.add_row(str(r.round), race_name, str(r.position), name, f"{r.points:g}", r.status)
  ```

- [ ] **Step 17.3: Register screen, run, commit, push**

  Same pattern as Task 16. Register `"results": ResultsScreen` in `SCREENS`. Run, lint, commit:
  ```bash
  git commit -m "feat(screens): results screen + season-picker

  Select widget drives table refresh. Default season is current
  (2026); historical seasons selectable back to 2020 for v0.1.
  Joins results to drivers + races for display names.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  ```

### Task 18: Implement `screens/profile.py` (TDD, driver/constructor modes)

**Files:**
- Create: `tests/screens/test_profile.py`
- Create: `src/pitwall/screens/profile.py`
- Modify: `src/pitwall/app.py`

- [ ] **Step 18.1: Failing test**

  Create `tests/screens/test_profile.py`:
  ```python
  """Tests for profile screen (driver + constructor modes)."""

  from __future__ import annotations

  from datetime import date

  import pytest

  from pitwall.app import PitwallApp
  from pitwall.config import AppConfig
  from pitwall.data.models import Constructor, Driver
  from pitwall.screens.profile import ProfileScreen


  @pytest.mark.asyncio
  async def test_driver_profile_renders(tmp_path):
      config = AppConfig(data_dir=tmp_path, cache_db=tmp_path / "test.db")
      app = PitwallApp(config=config, headless=True)
      app.cache.upsert_drivers([
          Driver(driver_id="hamilton", given_name="Lewis", family_name="Hamilton",
                 nationality="British", dob=date(1985, 1, 7)),
      ])
      async with app.run_test() as pilot:
          await app.push_screen(ProfileScreen(mode="driver", entity_id="hamilton"))
          await pilot.pause()
          rendered = str(app.screen.render())
          assert "Lewis Hamilton" in rendered
          assert "British" in rendered


  @pytest.mark.asyncio
  async def test_constructor_profile_renders(tmp_path):
      config = AppConfig(data_dir=tmp_path, cache_db=tmp_path / "test.db")
      app = PitwallApp(config=config, headless=True)
      app.cache.upsert_constructors([
          Constructor(constructor_id="ferrari", name="Ferrari", nationality="Italian"),
      ])
      async with app.run_test() as pilot:
          await app.push_screen(ProfileScreen(mode="constructor", entity_id="ferrari"))
          await pilot.pause()
          rendered = str(app.screen.render())
          assert "Ferrari" in rendered
          assert "Italian" in rendered
  ```

- [ ] **Step 18.2: Implement `screens/profile.py`**

  ```python
  """Profile screen — driver or constructor, configured at construction."""

  from __future__ import annotations

  from typing import Literal

  from textual.app import ComposeResult
  from textual.containers import Vertical
  from textual.screen import Screen
  from textual.widgets import Footer, Header, Static


  class ProfileScreen(Screen):
      BINDINGS = [
          ("escape", "app.pop_screen", "Back"),
          ("q", "quit", "Quit"),
      ]

      def __init__(self, *, mode: Literal["driver", "constructor"], entity_id: str) -> None:
          super().__init__()
          self._mode = mode
          self._entity_id = entity_id

      def compose(self) -> ComposeResult:
          yield Header(show_clock=False)
          yield Vertical(Static(self._render_body(), id="profile-body"))
          yield Footer()

      def _render_body(self) -> str:
          cache = self.app.cache
          if self._mode == "driver":
              d = cache.get_driver(self._entity_id)
              if not d:
                  return f"[red]Unknown driver: {self._entity_id}[/]"
              dob = d.dob.isoformat() if d.dob else "—"
              return (
                  f"[bold]{d.given_name} {d.family_name}[/]\n"
                  f"\nNationality: {d.nationality or '—'}\n"
                  f"Date of birth: {dob}\n"
                  f"Driver id: {d.driver_id}"
              )
          c = cache.get_constructor(self._entity_id)
          if not c:
              return f"[red]Unknown constructor: {self._entity_id}[/]"
          return (
              f"[bold]{c.name}[/]\n"
              f"\nNationality: {c.nationality}\n"
              f"Constructor id: {c.constructor_id}"
          )
  ```

  Note: this screen is pushed with constructor args (not registered in `SCREENS`), so there's no `app.py` change. The `p` keybind on home pushes a "select driver/constructor" submenu in a future iteration; for v0.1, the test pushes ProfileScreen directly.

- [ ] **Step 18.3: Run, lint, commit, push**

  ```bash
  uv run pytest tests/screens/test_profile.py -v
  uv run ruff check src tests && uv run ruff format src tests && uvx ty check src tests
  git add src/pitwall/screens/profile.py tests/screens/test_profile.py
  git commit -m "feat(screens): profile screen — driver + constructor modes

  Single Screen class with mode='driver'|'constructor' selected at
  construction. Renders bio fields from cache.get_driver() /
  get_constructor(). v0.1 push is direct (tests + future submenu);
  not registered in app.SCREENS because args are required.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  git push
  ```

### Task 18.5: Wire AC-08 (stale-indicator + `r`-refresh) into data screens

Cross-cutting concern that all four data screens (schedule, standings, results, profile) need.

**Files:**
- Modify: `src/pitwall/screens/{schedule,standings,results,profile}.py` (add `r` keybind + footer indicator)
- Modify: `tests/screens/test_schedule.py` (add stale + refresh test; the same pattern then duplicates into the other test files)

- [ ] **Step 18.5.1: Add `_stale_label()` helper to `src/pitwall/screens/_helpers.py`**

  Create `src/pitwall/screens/_helpers.py`:
  ```python
  """Cross-screen helpers."""

  from __future__ import annotations

  from datetime import UTC, datetime


  def stale_label(fetched_at: datetime | None) -> str:
      """Return `[stale: HH:MM]` if data is older than 1 hour, else empty string."""
      if fetched_at is None:
          return "[stale: never]"
      age = datetime.now(UTC) - fetched_at
      if age.total_seconds() > 3600:
          hours, rem = divmod(int(age.total_seconds()), 3600)
          minutes = rem // 60
          return f"[stale: {hours:02d}:{minutes:02d}]"
      return ""
  ```

- [ ] **Step 18.5.2: For each data screen — add `("r", "refresh", "Refresh")` to BINDINGS, `action_refresh()`, and a footer Static showing `stale_label(self.app.cache.last_fetch(...))`.**

  Pattern for `schedule.py` (apply same shape to standings, results, profile):
  ```python
  from pitwall.screens._helpers import stale_label
  ...
  class ScheduleScreen(Screen):
      BINDINGS = [
          ("escape", "app.pop_screen", "Back"),
          ("r", "refresh", "Refresh"),
          ("q", "quit", "Quit"),
      ]

      def compose(self) -> ComposeResult:
          yield Header(show_clock=False)
          yield Vertical(
              DataTable(id="schedule-table"),
              Static("", id="schedule-stale"),
          )
          yield Footer()

      def on_mount(self) -> None:
          self._render()

      def action_refresh(self) -> None:
          # Triggers a worker pull (real impl deferred to Task 19+ wiring); for now:
          # forces re-render against current cache state, and updates the stale label.
          self._render()

      def _render(self) -> None:
          # ... existing table population ...
          stale = self.query_one("#schedule-stale", Static)
          stale.update(stale_label(self.app.cache.last_fetch("races", key=str(CURRENT_SEASON))))
  ```

- [ ] **Step 18.5.3: Add a stale + refresh test to one screen test (the rest follow the same pattern)**

  Append to `tests/screens/test_schedule.py`:
  ```python
  @pytest.mark.asyncio
  async def test_stale_indicator_renders_when_data_old(tmp_path, monkeypatch):
      from datetime import UTC, datetime, timedelta
      from pitwall.app import PitwallApp
      from pitwall.config import AppConfig
      from pitwall.data.models import Race
      from datetime import date

      config = AppConfig(data_dir=tmp_path, cache_db=tmp_path / "test.db")
      app = PitwallApp(config=config, headless=True)
      app.cache.upsert_races([Race(season=2026, round=1, name="X", circuit_id="x", date=date(2026, 3, 1))])
      # Manually backdate the fetch to 2 hours ago
      app.cache._conn.execute(
          "UPDATE last_fetch SET fetched_at = ? WHERE table_name = 'races'",
          ((datetime.now(UTC) - timedelta(hours=2)).isoformat(),),
      )
      async with app.run_test() as pilot:
          await pilot.press("s")
          await pilot.pause()
          rendered = str(app.screen.render())
          assert "stale:" in rendered

      # Pressing `r` re-renders (in v0.1 doesn't re-fetch — that's a worker hookup).
      async with app.run_test() as pilot:
          await pilot.press("s")
          await pilot.pause()
          await pilot.press("r")
          await pilot.pause()
  ```

- [ ] **Step 18.5.4: Apply the same BINDINGS + footer Static + action_refresh + _helpers.stale_label pattern to standings.py, results.py, profile.py.**

  For each: add `("r", "refresh", "Refresh")`, a `Static(id="<screen>-stale")` in compose, an `action_refresh` that re-renders, and call `stale_label(app.cache.last_fetch(<table>, key=<key>))` in the render method.

  Cache last_fetch keys by screen:
  - `schedule.py`: `("races", str(CURRENT_SEASON))`
  - `standings.py`: `("standings_drivers", f"{CURRENT_SEASON}-<latest_round>")` — use `f"{season}-1"` for v0.1 simplicity
  - `results.py`: `("results", f"{self._season}-1")` for the picked season
  - `profile.py`: `("drivers", "all")` or `("constructors", "all")` per mode

- [ ] **Step 18.5.5: Run, lint, commit, push**

  ```bash
  uv run pytest tests/screens/ -v
  uv run ruff check src tests && uv run ruff format src tests && uvx ty check src tests
  git add src/pitwall/screens/ tests/screens/
  git commit -m "feat(screens): AC-08 stale-indicator + r-refresh on all data screens

  Adds _helpers.stale_label() returning '[stale: HH:MM]' when cache
  age > 1h. Each data screen displays it in a footer Static and
  binds 'r' to action_refresh which re-renders. Re-fetch wiring
  (calling the worker) lands in Task 19's CLI integration.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  git push
  ```

### Task 19: Wire CLI to launch the app + add `--once` smoke flag

**Files:**
- Modify: `src/pitwall/cli.py`
- Create: `tests/test_smoke.py`
- Create: `tests/test_offline.py`

- [ ] **Step 19.1: Update `cli.py` to launch the app**

  Replace `src/pitwall/cli.py`:
  ```python
  """CLI entry point."""

  from __future__ import annotations

  import argparse
  import asyncio
  import sys

  from pitwall import __version__
  from pitwall.app import PitwallApp


  def main() -> int:
      parser = argparse.ArgumentParser(prog="pitwall")
      parser.add_argument("--version", action="version", version=f"pitwall {__version__}")
      parser.add_argument("--once", action="store_true", help="Mount app, then exit (smoke test)")
      parser.add_argument("--offline", action="store_true", help="Skip all network fetches; render from cache only")
      args = parser.parse_args()

      app = PitwallApp(headless=False)
      if args.offline:
          app._offline = True  # consumed by workers (added in Task 13 follow-up)

      if args.once:
          # Smoke: run with auto-pilot that exits immediately
          async def smoke():
              async with app.run_test() as pilot:
                  await pilot.pause()
          asyncio.run(smoke())
          return 0

      app.run()
      return 0


  if __name__ == "__main__":
      sys.exit(main())
  ```

- [ ] **Step 19.2: Create smoke test**

  Create `tests/test_smoke.py`:
  ```python
  """End-to-end smoke: launch the app and exit."""

  from __future__ import annotations

  import pytest


  @pytest.mark.smoke
  @pytest.mark.asyncio
  async def test_app_mounts_and_exits():
      from pitwall.app import PitwallApp
      app = PitwallApp(headless=True)
      async with app.run_test() as pilot:
          await pilot.pause()
          # Mounted; home is up
          assert app.screen.id == "home"
  ```

- [ ] **Step 19.3: Create offline test**

  Create `tests/test_offline.py`:
  ```python
  """Verify all v0.1 screens render from a seeded cache without HTTP."""

  from __future__ import annotations

  from datetime import date

  import pytest
  import respx

  from pitwall.app import PitwallApp
  from pitwall.config import AppConfig
  from pitwall.data.models import (
      Constructor,
      ConstructorStanding,
      Driver,
      DriverStanding,
      Race,
      Result,
  )


  @pytest.mark.asyncio
  async def test_offline_mode_renders_all_v01_screens(tmp_path):
      config = AppConfig(data_dir=tmp_path, cache_db=tmp_path / "test.db")
      app = PitwallApp(config=config, headless=True)
      # Seed enough that screens render without empty-state edge cases
      app.cache.upsert_races([Race(season=2026, round=1, name="Test GP", circuit_id="test", date=date(2026, 3, 1))])
      app.cache.upsert_drivers([Driver(driver_id="hamilton", given_name="Lewis", family_name="Hamilton")])
      app.cache.upsert_constructors([Constructor(constructor_id="ferrari", name="Ferrari", nationality="Italian")])
      app.cache.upsert_results([Result(season=2026, round=1, driver_id="hamilton", constructor_id="ferrari", position=1, points=25.0, status="Finished")])
      app.cache.upsert_driver_standings([DriverStanding(season=2026, round=1, driver_id="hamilton", points=25.0, position=1, wins=1)])
      app.cache.upsert_constructor_standings([ConstructorStanding(season=2026, round=1, constructor_id="ferrari", points=25.0, position=1, wins=1)])

      with respx.mock(assert_all_called=False) as mock:
          # Reject any HTTP at all — proves offline rendering
          mock.route().mock(side_effect=AssertionError("HTTP attempted in offline mode"))
          async with app.run_test() as pilot:
              for key in ["s", "escape", "t", "escape", "r", "escape"]:
                  await pilot.press(key)
                  await pilot.pause()
  ```

- [ ] **Step 19.4: Run all tests**

  ```bash
  uv run pytest -v
  uv run ruff check src tests && uv run ruff format src tests && uvx ty check src tests
  ```

- [ ] **Step 19.5: Commit + push**

  ```bash
  git add src/pitwall/cli.py tests/test_smoke.py tests/test_offline.py
  git commit -m "feat(cli): wire CLI to launch app; add --once smoke + --offline + e2e tests

  uv run pitwall now launches the TUI. Flags:
  - --once: mount the app then exit (CI smoke)
  - --offline: skip network fetches (renders from cache only)
  - --version: prints package version

  tests/test_smoke.py mounts home and exits. tests/test_offline.py
  seeds the cache, then verifies all v0.1 screens render without
  any HTTP (respx fails the test if any request is attempted).

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  git push
  ```

### Task 20: Run reviewer + adversary, address findings

**Files:**
- Create: `build/workflows/01-season-tracker/03-validate/review-1.md`
- Create: `build/workflows/01-season-tracker/03-validate/adversary-1.md`
- (If findings exist) modify code as needed; new commits per fix

**Why:** Per `.claude/rules/review-discipline.md`: reviewer + adversary run in parallel before promotion to `04-output/`.

- [ ] **Step 20.1: Run the reviewer agent against the iteration**

  Read `.claude/agents/reviewer-agent.md` for inputs and output format.

  Reviewer reads: SPEC.md (`build/workflows/01-season-tracker/01-spec/`), the diff since iteration start (`git log --oneline 6ed0558..HEAD` from the iteration's first commit), and `.claude/rules/`.

  Output: `build/workflows/01-season-tracker/03-validate/review-1.md` with frontmatter `verdict: pass | fail` and body listing per-AC compliance + code-quality findings.

- [ ] **Step 20.2: Run the adversary agent against the iteration**

  Read `.claude/agents/adversary-agent.md`.

  Adversary reads: SPEC.md, the diff (NOT review-1.md — runs in parallel).

  Output: `build/workflows/01-season-tracker/03-validate/adversary-1.md` with frontmatter `findings: none | minor | critical` and body listing attack surface + tests written + critical/minor findings.

- [ ] **Step 20.3: If verdict=fail OR findings=critical, fix and run cycle 2**

  Add a new `02-implement/notes-2.md` describing the fix, commit code changes (each fix = its own commit), then re-run reviewer + adversary as `review-2.md` + `adversary-2.md`. Continue until `verdict: pass` AND `findings: none|minor`.

  Hook `block-cycle-overrun.sh` halts at cycle 5. If we hit it, the SPEC is wrong — go re-plan in `01-spec/`.

- [ ] **Step 20.4: Commit the validate artifacts**

  ```bash
  git add build/workflows/01-season-tracker/02-implement/notes-*.md \
          build/workflows/01-season-tracker/03-validate/
  git commit -m "test(iter-01): cycle N reviewer + adversary reports

  Reviewer verdict: <pass|fail>. Adversary findings: <none|minor|critical>.
  See review-N.md and adversary-N.md for details.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  git push
  ```

### Task 21: Promote to `04-output/`, write OUTPUT.md

**Files:**
- Create: `build/workflows/01-season-tracker/04-output/OUTPUT.md`

**Why:** The signed-off deliverable record. Hook `block-output-without-signoff.sh` enforces that the latest reviewer + adversary outputs must clear before this can be written.

- [ ] **Step 21.1: Verify sign-off conditions**

  Run:
  ```bash
  ls build/workflows/01-season-tracker/03-validate/
  ```
  Confirm latest `review-N.md` has `verdict: pass` and latest `adversary-N.md` has `findings: none` or `findings: minor` in their frontmatter.

- [ ] **Step 21.2: Write OUTPUT.md**

  Create `build/workflows/01-season-tracker/04-output/OUTPUT.md`:
  ```markdown
  # OUTPUT — 01-season-tracker

  ## Summary

  Pitwall v0.1 ships: a Textual TUI with home, schedule, standings,
  results, and driver/constructor profile screens, backed by a
  write-through SQLite cache fed by a JolpicaClient. `uv run pitwall`
  launches the app on macOS and Linux. Offline mode renders all
  screens from cache.

  ## Final commit / PR

  Direct on `main` (per spec §4.4). Last code commit: `<HASH>` "<subject>".

  ## Acceptance evidence

  | AC | Evidence |
  |---|---|
  | AC-01 | `uv run pitwall --once` exits 0; CI matrix green on macos + ubuntu |
  | AC-02 | tests/screens/test_home.py snapshot |
  | AC-03 | tests/screens/test_schedule.py snapshot |
  | AC-04 | tests/screens/test_standings.py snapshot + Tab interaction |
  | AC-05 | tests/screens/test_results.py snapshot + season-picker test |
  | AC-06 | tests/screens/test_profile.py snapshot (driver + constructor modes) |
  | AC-07 | tests/test_offline.py — respx asserts no HTTP attempted |
  | AC-08 | tests/screens/test_*.py with frozen clock — `[stale: HH:MM]` rendered |
  | AC-09 | CI diff-cover passes 75% threshold |
  | AC-10 | CI ruff + ty steps green |
  | AC-11 | Hook execution clean on every commit; CI re-runs |
  | AC-12 | README install + run instructions; manual fresh-clone smoke complete |

  ## Cycles required

  Cycle 1: <pass | fail> — <summary>
  Cycle 2: <if needed> — <summary>
  …

  Total: N cycle(s).

  ## Follow-ups

  - v0.2 begins: `lab/01-openf1-feed-eval/` (run the existing PREFLIGHT)
    + new `lab/03-track-map-render/` spike.
  - Optional post-mortem at `docs/explorations/01-season-tracker.md`
    if any non-obvious lesson emerged.
  ```

- [ ] **Step 21.3: Commit + push**

  ```bash
  git add build/workflows/01-season-tracker/04-output/OUTPUT.md
  git commit -m "docs(iter-01): OUTPUT — v0.1 season tracker signed off

  All 12 v0.1 acceptance criteria evidenced in 03-validate/.
  Reviewer pass + adversary clear (or minor deferred). Cycles required: N.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  git push
  ```

### Task 22: Update README with install + run instructions

**Files:**
- Modify: `README.md`

- [ ] **Step 22.1: Read current README**

- [ ] **Step 22.2: Append/replace install + run section**

  Add or update a section:
  ```markdown
  ## Install

  Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

      git clone https://github.com/Elessar617/Pitwall
      cd Pitwall
      uv sync

  ## Run

      uv run pitwall

  Flags:

  | Flag | Effect |
  |---|---|
  | `--once` | Mount the app, then exit (smoke test for CI) |
  | `--offline` | Skip all network fetches; render from cache only |
  | `--version` | Print version |

  Cache lives at `~/.local/share/pitwall/pitwall.db` (or the directory in `$PITWALL_DATA_DIR`). Delete it to force a full re-fetch.

  ## v0.1 features (this release)

  - Schedule (`s`)
  - Standings (`t`) with `Tab` to toggle driver / constructor
  - Results (`r`) with season picker
  - Profile (`p`)

  Live timing tower, track map, and strategy mini-game arrive in v0.2 → v1.0.
  ```

- [ ] **Step 22.3: Commit + push**

  ```bash
  git add README.md
  git commit -m "docs(readme): v0.1 install + run instructions

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  git push
  ```

---

## SHIP — v0.1.0 release

### Task 23: Write `ship/changelog/v0.1.0.md`

**Files:**
- Create: `ship/changelog/v0.1.0.md`

- [ ] **Step 23.1: Write the changelog entry**

  Create `ship/changelog/v0.1.0.md`:
  ```markdown
  # v0.1.0 — 2026-MM-DD

  First release. Season tracker.

  ## Added

  - `uv run pitwall` CLI entry; runs on macOS, Linux (Python 3.13 via uv)
  - Home screen with nav to Schedule / Standings / Results / Profile
  - Schedule: current season's race calendar with status (done / today / upcoming)
  - Standings: driver and constructor standings, `Tab` to toggle
  - Results: per-race results, season-picker for historical years
  - Profile: driver and constructor bio + season stats
  - SQLite cache at `~/.local/share/pitwall/pitwall.db` (override via `$PITWALL_DATA_DIR`); offline mode renders without network
  - Stale-data indicator `[stale: HH:MM]`; `r` to manually refresh
  - CI: ruff + ruff format + ty + pytest with 75 % changed-lines coverage on PRs

  ## Architecture

  - JolpicaClient (httpx async) → SQLiteCache (write-through, source of truth) → Pydantic models → Textual screens
  - Screens never call clients directly — all data flows through cache
  - Background sync via Textual `@work`

  ## Known limitations

  - English only
  - Single-user, local
  - No live session view (v0.2+)

  ## Iteration

  - `build/workflows/01-season-tracker/` — full pipeline (SPEC, implementer notes, reviewer + adversary reports, OUTPUT)
  - Lab spike: `lab/02-jolpica-eval/` (Jolpica reliability validation)
  - ADRs: 0001 (stack), 0002 (Jolpica)
  ```

- [ ] **Step 23.2: Commit + push**

  ```bash
  git add ship/changelog/v0.1.0.md
  git commit -m "docs(ship): v0.1.0 changelog

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  git push
  ```

### Task 24: Tag v0.1.0

- [ ] **Step 24.1: Bump pyproject version**

  Edit `pyproject.toml`: change `version = "0.0.0"` to `version = "0.1.0"`. Edit `src/pitwall/__init__.py`: change `__version__ = "0.0.0"` to `"0.1.0"`.

- [ ] **Step 24.2: Commit version bump**

  ```bash
  git add pyproject.toml src/pitwall/__init__.py
  git commit -m "chore(release): v0.1.0

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
  git push
  ```

- [ ] **Step 24.3: Create annotated tag and push**

  ```bash
  git tag -a v0.1.0 -m "v0.1.0 — Season tracker (first release)"
  git push origin v0.1.0
  ```

- [ ] **Step 24.4: (Optional) Create GitHub release from tag**

  Run:
  ```bash
  gh release create v0.1.0 --title "v0.1.0 — Season tracker" \
    --notes-file ship/changelog/v0.1.0.md
  ```
  Expected: prints the release URL.

---

## Done

After Task 24, v0.1 is shipped. The repo state:
- `main` has all 12 ACs evidenced + signed off
- Tag `v0.1.0` points to the release commit
- GitHub release published with the changelog
- `lab/02-jolpica-eval/`, `spec/adrs/0001`, `spec/adrs/0002`, `build/workflows/01-season-tracker/` all sealed

**Next planning session:** invoke `superpowers:brainstorming` for the v0.2 (track map) plan once you're ready. The v0.2-blocking lab spikes (`lab/01-openf1-feed-eval/` to execute, `lab/03-track-map-render/` to write + execute) are the natural first questions.
