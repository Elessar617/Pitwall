# Pitwall — Consolidated Design Spec

**Status:** Draft (pending user approval)
**Author:** Claude (Opus 4.7) with Gardner Wilson
**Date:** 2026-05-11
**References:** [`spec/briefs/pitwall-overview.md`](../../../spec/briefs/pitwall-overview.md), [`lab/01-openf1-feed-eval/PREFLIGHT.md`](../../../lab/01-openf1-feed-eval/PREFLIGHT.md)

---

## 1. Context

Pitwall is the Formula 1 TUI companion described in [`spec/briefs/pitwall-overview.md`](../../../spec/briefs/pitwall-overview.md). The brief ratifies **what** we're building (live session view, season tracker, strategy mini-game) and the constraints (Python 3.13 + Textual + uv + ruff + ty; public-data sources only).

This spec ratifies **how**: the release sequencing, the long-lived architecture, the process discipline, and the acceptance criteria for v0.1 and v1.0. It is the single source of truth that every downstream artifact (ADRs in `spec/adrs/`, lab-spike PREFLIGHTs in `lab/`, build-iteration SPECs in `build/workflows/`, ship notes in `ship/`) refers back to.

The spec is the output of a brainstorming session (per `superpowers:brainstorming`) that explored sequencing, milestones, architecture, and discipline before any production code lands. It supersedes the narrower "Part C" sketch referenced in the previous session's `.remember/remember.md`.

---

## 2. Sequencing & milestones

### 2.1 Release roadmap

| Milestone | Pillar | Why this position |
|---|---|---|
| **v0.1** | Season tracker (schedule, standings, results, profiles) — folded with project skeleton | Off-season-friendly. Validates Jolpica + SQLite cache + Textual screen-building before touching real-time async. The skeleton (CLI entry, app shell, screen router, SQLite schema) ships inside this iteration so v0.1 is independently demo-able. |
| **v0.2** | Track map (ASCII/Unicode circuit + driver markers) | Visualization de-risked separately from the timing display. Renders only when a session is live. |
| **v0.3** | Live timing tower (gap, lap, sectors, tyre, age, pits) + race-control / weather panels | Adds the data-display layer alongside the track map. By this point both OpenF1 and the rendering loop are validated. |
| **v1.0** | Strategy mini-game (pre-race commit + live pit-window prompts + score) | Top of the dependency stack — needs live session state from v0.3 and tyre-degradation curves from FastF1. |

### 2.2 Lab spikes

Sequenced before each spike's dependent build iteration. Numbering is append-only; the existing `lab/01-openf1-feed-eval/` keeps its number even though it executes after `lab/02-jolpica-eval/`.

| ID | Spike | Blocks | PREFLIGHT status |
|---|---|---|---|
| `lab/01-openf1-feed-eval/` | OpenF1 reliability + completeness + latency | v0.2, v0.3 | **Already written.** Re-positioned to also block v0.2 (track map needs OpenF1 position data). |
| `lab/02-jolpica-eval/` | Jolpica endpoint coverage, schema stability, rate limits, historical depth | v0.1 | **To write.** First new lab artifact. |
| `lab/03-track-map-render/` | Circuit-outline data source + projection algorithm + terminal cell density | v0.2 | **To write.** Can run in parallel with `lab/01`. |
| `lab/04-fastf1-tyre-curves/` | FastF1 offline curve-fitting cost + cadence | v1.0 | **To write.** Defer until after v0.3 ships. |

### 2.3 Build iterations

| ID | Iteration | Output |
|---|---|---|
| `build/workflows/01-season-tracker/` | Skeleton + season tracker | v0.1 |
| `build/workflows/02-track-map/` | Track-map screen + position polling | v0.2 |
| `build/workflows/03-live-timing-tower/` | Timing tower + race-control / weather feeds | v0.3 |
| `build/workflows/04-strategy-mini-game/` | Pre-race commit screen + live pit-window prompts + score | v1.0 |

### 2.4 ADR sequence

**Rule:** an ADR ratifies a decision *at the moment of honest commitment*. Whichever comes first:
- the lab spike's REPORT (if a spike preceded the decision), OR
- the build iteration's `01-spec/SPEC.md` planning step (if no spike, or the decision is a build-time architectural choice).

Never write an ADR speculatively. If you'd have to use words like "we'll probably" or "TBD", you're too early.

| ADR | Written when | Rationale |
|---|---|---|
| `0001-stack-python-textual.md` | **Pre-flight** (before any build) | Stack is fixed by the brief; risk of revision is minimal. ADR records *why* (matching faceoff, mature TUI ecosystem, ty/ruff/uv). |
| `0002-jolpica-as-season-source.md` | After `lab/02-jolpica-eval/` REPORTs | Decision contingent on spike outcome. |
| `0003-openf1-as-live-source.md` | After `lab/01-openf1-feed-eval/` REPORTs | Spike's failure criteria explicitly include "abandon OpenF1, use FastF1 live-timing instead." Premature ADR risks rework. |
| `0004-sqlite-cache-strategy.md` | Inside `build/workflows/01-season-tracker/01-spec/` | Cache shape (write-through vs source-of-truth) becomes concrete when implementing. |
| `0005-async-strategy.md` | Inside `build/workflows/02-track-map/01-spec/` | Real-time async requirements crystallize when polling + rendering merge. |
| `0006-fastf1-tyre-curve-cadence.md` | After `lab/04-fastf1-tyre-curves/` REPORTs | Cadence + storage decisions contingent on spike. |

### 2.5 Pre-flight chores (before v0.1 work begins)

Three small `chore:` commits, in order, on `main`:

1. `chore: drop stray empty stage dirs at build/workflows/ root` — removes the four `.gitkeep`-only dirs (`01-spec/`, `02-implement/`, `03-validate/`, `04-output/`) that exist as siblings of `00-template/`. Per `build/workflows/CONTEXT.md`, those four stages live *inside* iteration dirs only. Leaving them in place would mislead future iterations and risk false-positive matches in the cycle/sign-off hooks.
2. `chore: initialize uv project (pyproject.toml, src/pitwall/__init__.py, cli.py stub)` — makes `uv run pitwall` resolvable. Empty `__init__.py`, `cli.py` prints "pitwall v0.0.0", `.python-version` pins Python 3.13.
3. `docs(adr): 0001 Python + Textual + uv + ruff + ty stack` — ratifies the brief's de-facto stack decision.

---

## 3. Architecture

### 3.1 Module layout (`src/pitwall/`)

```
src/pitwall/
├─ __main__.py          # `python -m pitwall` → cli.main()
├─ cli.py               # `uv run pitwall` entry, arg parsing, app launch
├─ app.py               # PitwallApp(textual.App) — screen router
├─ config.py            # settings (refresh interval, cache path, paths)
│
├─ data/                # Data layer (the durable contract)
│  ├─ models.py         # Pydantic models: Race, Driver, Constructor, Standings, Result, …
│  ├─ cache.py          # SQLiteCache — write-through; source-of-truth for UI
│  ├─ schema/           # *.sql migrations (flat, numbered)
│  ├─ jolpica.py        # JolpicaClient (httpx.AsyncClient) — v0.1
│  ├─ openf1.py         # OpenF1Client (httpx.AsyncClient) — v0.2/v0.3
│  └─ fastf1.py         # FastF1Adapter (wraps the fastf1 library) — v1.0
│
├─ screens/             # One Textual Screen per top-level view
│  ├─ home.py           # nav + "what's next" widget
│  ├─ schedule.py       # v0.1
│  ├─ standings.py      # v0.1
│  ├─ results.py        # v0.1
│  ├─ profile.py        # v0.1: driver/constructor (one screen, two modes)
│  ├─ track_map.py      # v0.2
│  ├─ timing_tower.py   # v0.3
│  └─ strategy.py       # v1.0
│
├─ widgets/             # Reusable rendering primitives (introduced as needed; YAGNI)
│
└─ workers/             # Background data fetchers (Textual @work)
   ├─ jolpica_sync.py   # full-season pull on first launch + stale refresh
   └─ session_poller.py # polls OpenF1 every N seconds while a live screen is mounted
```

### 3.2 Data flow

```
External APIs ──┐
  Jolpica       │  fetched by → data/{jolpica,openf1,fastf1}.py
  OpenF1        │       ↓
  FastF1        │   data/cache.py  (SQLite write-through)
                │       ↓
                │   data/models.py (validated Pydantic objects)
                │       ↓
                │  workers/* enqueue refresh, screens/* read latest cached
                ↓
           Textual UI (screens/widgets)
```

**Rule:** screens MUST NOT call clients directly. Screens read from `cache.py`; workers refresh `cache.py`. This keeps screens render-time-fast and testable without HTTP, and isolates data-source swaps to one file.

### 3.3 Async + caching strategy

| Surface | Refresh policy | Worker | Cache TTL |
|---|---|---|---|
| Season tracker (Jolpica) | On screen mount + manual `r` pull | `jolpica_sync` | 1 h (fixed in v0.1; configurable later) |
| Track map / timing tower (OpenF1) | Poll every 5–30 s while screen mounted | `session_poller` | stale-while-revalidate; never block UI |
| Tyre curves (FastF1) | Per-race or per-season (decided in `lab/04`) | (decided in `lab/04`) | persisted in SQLite as serialized curve params |

Textual's `@work(thread=False)` decorator runs coroutines on the same event loop as the UI — no thread coordination, no GIL anxiety, automatic cancellation on screen unmount. `httpx.AsyncClient` is the HTTP primitive across all three clients.

### 3.4 Cache as source of truth

SQLite at `data/pitwall.db` (gitignored). Every UI read goes through cache. Initial table sketch (exact columns nailed in `build/workflows/01-season-tracker/01-spec/SPEC.md`):

```
races(season, round, name, date, circuit_id, …)
drivers(driver_id, given_name, family_name, dob, nationality, …)
constructors(constructor_id, name, nationality, …)
results(season, round, driver_id, constructor_id, position, points, status, …)
qualifying(season, round, driver_id, q1, q2, q3, …)
standings_drivers(season, round, driver_id, points, position, wins)
standings_constructors(season, round, constructor_id, points, position, wins)
last_fetch(table_name, key, fetched_at)   -- for staleness checks
```

Migrations as plain `src/pitwall/data/schema/NNN-<slug>.sql` files (the Python module's `schema/` subdir, NOT the repo-root `data/` runtime dir), applied on app start. Migration framework: none (YAGNI — flat numbered SQL is enough for v1.0).

### 3.5 Error handling (boundary-only, per CLAUDE.md)

| Failure | Surface |
|---|---|
| Network down | Show cached data with `[stale: HH:MM]` indicator; manual refresh prompts retry |
| API 4xx / 5xx | Same as network down + log to `~/.local/state/pitwall/log` (or platform equivalent) |
| API schema drift (new field) | Log + ignore; never crash |
| API schema drift (missing required field) | "Data partially unavailable" on the affected widget; rest of screen still renders |
| SQLite locked / corrupt | Fail-fast at startup with actionable message ("rm data/pitwall.db; we'll re-fetch") |
| FastF1 not installed (v1.0) | Strategy screen disabled with install hint |

No retries, no backoff loops, no silent fallbacks. The user sees the truth.

### 3.6 Testing strategy

| Layer | Tool | Mocked? |
|---|---|---|
| Data clients (`data/jolpica.py`, etc.) | `pytest` + `pytest-asyncio` + `respx` (httpx mock) | HTTP only |
| Cache (`data/cache.py`) | `pytest` + temp SQLite file | Nothing — real DB |
| Models (`data/models.py`) | `pytest` against fixtures | Nothing |
| Workers | `pytest-asyncio` + fake clock | Clients yes, cache no |
| Screens | Textual snapshot tests (`pytest-textual-snapshot`) | Cache fixtures injected |
| End-to-end | Smoke: `uv run pitwall --once` opens, hits home, exits 0 | None |

Per `.claude/rules/testing-discipline.md`: TDD enforced by `pre-commit-tdd.sh`. ≥ 75 % coverage on changed lines (per brief). The `tdd-loop` skill is the loop discipline inside each build iteration.

---

## 4. Process discipline

### 4.1 Per-pillar flow

```
For each release pillar (v0.1, v0.2, v0.3, v1.0):

  spec/briefs/         lab/NN-<spike>/         spec/adrs/
  pitwall-overview     PREFLIGHT → VERIFY      NNNN-<decision>.md
  (already done)       → REPORT  (or skip)     (post-spike or
         ↓                    ↓                  pre-build)
         └────────────────────┴──────────────┐  ↓
                                             ▼
                          build/workflows/NN-<iteration>/
                          01-spec → 02-implement →
                          03-validate → 04-output
                                ↓
                          src/pitwall/* (the code)
                                ↓
                          ship/changelog/vX.Y.Z.md
                                ↓
                          docs/explorations/NN-<lesson>.md
                          (post-mortem, optional)
```

### 4.2 ADR write-timing rule

See Section 2.4. Restated: ADRs ratify decisions at the moment of honest commitment, never speculatively.

### 4.3 Skip-the-spike escape hatch

A lab spike is required when there's a **genuine unknown** that, if wrong, would force a redesign. It is not required when:
- the answer is mechanically derivable from public docs (no behavioral surprises possible)
- the cost of "find out during build" is small (≤ 1 day of wasted work)
- the planner agent's smoke pass in `01-spec/` resolves the question in under 2 hours

When skipping, document the skip in the iteration's `01-spec/SPEC.md` under "Unknowns acknowledged". The reviewer agent flags any unknown that should have been a spike.

For Pitwall, **all four currently-listed spikes (jolpica, openf1, track-map, fastf1) are required** — each has a real unknown the brief documents. No skips planned.

### 4.4 Branching & commit policy

| Phase | Branch model | Why |
|---|---|---|
| Pre-flight chores + v0.1 (`build/workflows/01-season-tracker/`) | All work on `main` | Fast iteration while we're proving the stack. Reviewer + adversary agents are the real review at this stage; PRs would just add ceremony. |
| **v0.2 onward** (`build/workflows/02-track-map/` and beyond) | One feature branch per build iteration (e.g., `feat/02-track-map`). Opened as PR against `main` once `04-output/OUTPUT.md` is signed off. Self-merge after CI passes. | Once the foundation is shipped, the cost of regressing v0.1 grows. PRs give: (a) atomic per-iteration changelog entry, (b) GitHub-level CI gate before merge, (c) easy rollback (revert PR), (d) practice for if collaborators join later. |
| Lab spikes | Always on `main` | Exploratory, low-blast-radius. PREFLIGHT/VERIFY/REPORT are docs, not production. |
| Hotfixes (post-release) | Branch `fix/<slug>` → PR → merge → patch tag (`v0.X.Y`) | Standard. |
| Doc-only changes | `main` direct | No iteration; trivial. |

**Branch naming:** `<type>/<NN>-<slug>` matching the iteration. Examples: `feat/02-track-map`, `feat/03-live-timing-tower`, `fix/standings-pagination`.

**PR merge style:** squash-merge for build iterations (one commit per iteration on `main`, message = the iteration's `04-output/OUTPUT.md` summary line). The full per-cycle commit history is preserved on the branch and accessible via the PR. Direct commits to `main` (chores, docs, lab spikes) keep their individual SHAs.

**CI gate** (added to PRs): `uv run ruff check`, `uv run ruff format --check`, `uv run ty check`, `uv run pytest --cov` enforcing the 75 % changed-lines threshold from `.claude/rules/testing-discipline.md`. The GitHub Actions workflow lands in `build/workflows/01-season-tracker/` (its first meaningful moment, since there's code to run it on).

**Hard rules** (per `.claude/rules/commit-discipline.md`):
- Conventional Commits format on every commit
- Never `--no-verify` (if a hook fails, fix the cause)
- Never force-push to `main`
- Never include sensitive files (`.env`, credentials, large binaries, OS metadata)

### 4.5 Cycle gate (per build iteration)

Already enforced by `block-cycle-overrun.sh` and `block-output-without-signoff.sh`. Stated for visibility:

| Cycle | Behavior |
|---|---|
| 1–4 | Implementer writes → reviewer + adversary run in parallel → orchestrator decides pass/fail |
| 5 (cap) | If cycle 5 doesn't sign off, **halt and re-spec.** The spec is wrong, not the implementer. |

### 4.6 Lessons & post-mortems

Per `docs/iteration-process.md`: every completed iteration may produce a `docs/explorations/NN-<slug>.md`. Required when:
- A spike's outcome is "abandon" or "modify" (not "pursue")
- A build iteration consumed > 3 cycles before sign-off
- A bug found in production traces back to a missed-then-decided trade-off

Optional otherwise. Don't write post-mortems for iterations that went smoothly — there's nothing to teach.

---

## 5. Acceptance criteria

### 5.1 v0.1 (season tracker)

Each item maps to at least one test (per `.claude/rules/testing-discipline.md`):

| # | Criterion | Verification |
|---|---|---|
| AC-01 | `uv run pitwall` launches the TUI without error on macOS, Linux | `pytest -m smoke` runs `pitwall --once` (mounts home, exits 0) |
| AC-02 | Home screen shows nav to Schedule, Standings, Results, Profile (other tabs disabled with "v0.x" labels) | Textual snapshot test |
| AC-03 | Schedule screen shows current season's full calendar (date, round, name, circuit, status: past/upcoming) | Snapshot test against fixture cache |
| AC-04 | Standings screen shows current driver & constructor standings with `Tab` toggle between them | Snapshot + interaction test |
| AC-05 | Results screen shows results for any past race in current season + season-picker for historical | Snapshot + parametrized over multiple seasons |
| AC-06 | Profile screen shows driver bio + current-season stats; same for constructor | Snapshot tests |
| AC-07 | After first launch (Jolpica seeded), all v0.1 screens render with `--offline` flag | E2E test with `respx` raising on every HTTP call |
| AC-08 | Stale data shows `[stale: HH:MM]` indicator; manual `r` refresh re-fetches | Interaction test with frozen clock |
| AC-09 | Test coverage ≥ 75 % on changed lines | `pytest --cov` in CI; PR fails if below |
| AC-10 | `uv run ruff check`, `uv run ruff format --check`, `uv run ty check` all clean | CI step; PR fails on any issue |
| AC-11 | `pre-commit-tdd.sh` and `enforce-portability.sh` hooks active and passing on every commit | Hook execution in development; CI re-runs |
| AC-12 | README has install + run instructions verified by a fresh-machine smoke test | Manual: clone fresh, follow README, confirm `uv run pitwall` works |

### 5.2 v1.0 (cumulative)

All of v0.1, plus:

| # | Criterion |
|---|---|
| AC-13 | Live track-position map renders during any active session type (FP1–3 / Quali / Sprint Quali / Sprint / Race) with refresh ≥ 5 s |
| AC-14 | Live timing tower shows for every driver: position, gap to leader, last lap, sector colors, current tyre + age, pit count |
| AC-15 | Race-control messages, weather, and flag state update live |
| AC-16 | User can commit a strategy pre-race (tyre + pit-lap targets) |
| AC-17 | User receives `pit now` / `stay out` / `wait one` prompts at decision moments |
| AC-18 | End-of-race screen shows player-vs-actual delta score and a brief summary |
| AC-19 | All v1.0 features behave correctly when network is degraded (cached fall-through, stale indicator) |

---

## 6. Risks & open questions

### 6.1 Risks

| Risk | Mitigation |
|---|---|
| Jolpica deprecates or schema-drifts a critical endpoint | Cache is already an abstraction layer. Migration is one client file. Explorations doc captures the swap if it happens. |
| OpenF1 rate-limits or downtime ruins live UX | The `lab/01` spike's failure criteria explicitly cover this; documented fallback is FastF1's live-timing client. ADR 0003 chooses based on REPORT. |
| FastF1 tyre-curve fitting too slow at startup | `lab/04` spike measures cost; ADR 0006 picks cadence (per-race, per-season, on-demand). |
| Textual rendering glitches at small terminal sizes (< 100 cols) | AC tests at 80×24, 100×30, 120×40. Smaller terminals get a "minimum size" splash, not broken UI. |
| Solo-dev burnout / stalls between releases | Each release ships independently. v0.1 alone is useful; if v0.2+ stalls, v0.1 still earns its place. |
| Premature v1.0 architecture commitment forces rework | Section 3.2's "screens never call clients directly" rule is the structural insurance: any data-source swap is one-file. ADRs ratified post-spike (Section 4.2) prevents speculative commitment. |

### 6.2 Open questions (resolved during the listed iteration's spec phase)

| Question | Resolved in |
|---|---|
| Exact SQLite schema (column types, indexes) | `build/workflows/01-season-tracker/01-spec/SPEC.md` |
| Refresh interval default + per-screen overrides | Same |
| Theme / color palette (`App.CSS` inline vs. separate `pitwall.tcss`) | Same |
| Track-outline data source (FastF1 `get_circuit_info()` vs. static per-circuit files) | `lab/03-track-map-render/PREFLIGHT.md` |
| Tyre-curve serialization format (Pydantic JSON vs. binary numpy) | `lab/04-fastf1-tyre-curves/PREFLIGHT.md` |
| Strategy scoring algorithm (delta to optimal pit-lap, weighted by tyre type) | `build/workflows/04-strategy-mini-game/01-spec/SPEC.md` |

---

## 7. Out of scope

Beyond the brief's v2 deferrals (full live race strategist, telemetry charts, onboard video, F1 TV integration, mobile/web frontend), this spec **also** explicitly excludes:

- **Telemetry / multi-window layouts** beyond the headline screens listed in Section 3.1.
- **User accounts / multi-user state** — Pitwall is single-user, local-only.
- **Notifications / alerts outside the TUI** — no native macOS notifications, no audio cues.
- **Internationalization** — English only.
- **Accessibility audit beyond Textual's defaults** — Textual's defaults are enough for v1.0; a formal a11y pass is post-v1.
- **Alternative data sources for non-F1 series** (W Series, F2, F3, IndyCar, etc.) — explicit non-goal.
- **Auto-update / package distribution beyond `uv add pitwall`** — no Homebrew formula, no DMG, no PyPI publish before v0.2.
- **Persistent strategy game state across sessions** — no leaderboards, no streaks, no save files beyond the one in-progress race.

---

## 8. Downstream artifacts the spec spawns

Once the spec is approved and committed, these get written next, in order:

```
Pre-flight (chore commits on main):
  1. chore: drop stray empty stage dirs at build/workflows/ root
  2. chore: initialize uv project (pyproject.toml, src/pitwall/__init__.py, cli.py stub)
  3. docs(adr): 0001 Python + Textual + uv + ruff + ty stack

v0.1 (lab + build + ship, all on main):
  4. lab/02-jolpica-eval/ — PREFLIGHT, prototype, VERIFY, REPORT
  5. docs(adr): 0002 Jolpica as season-data source
  6. build/workflows/01-season-tracker/ — full pipeline + CI workflow
  7. ship/changelog/v0.1.0.md, git tag v0.1.0

v0.2+ (lab on main, build on feature branches via PR):
  8. lab/01-openf1-feed-eval/ — execute the existing PREFLIGHT
  9. lab/03-track-map-render/ — new spike
 10. docs(adr): 0003 live-data source + 0005 async strategy
 11. feat/02-track-map → PR → squash-merge → tag v0.2.0
 12. feat/03-live-timing-tower → PR → squash-merge → tag v0.3.0
 13. lab/04-fastf1-tyre-curves/
 14. docs(adr): 0006 FastF1 tyre-curve cadence
 15. feat/04-strategy-mini-game → PR → squash-merge → tag v1.0.0
```

ADRs `0004-sqlite-cache-strategy.md` and `0005-async-strategy.md` are written inside the iteration spec phases that produce them (see Section 2.4); they're not separate sequence items.

---

## 9. Approval

This spec is approved for execution when:
- The user signs off on this document, AND
- The pre-flight chores from Section 2.5 are committed.

Approval triggers the transition to `superpowers:writing-plans`, which converts this spec into the implementation plan at `docs/superpowers/plans/2026-05-11-pitwall-implementation-plan.md`. The plan, in turn, breaks Section 8's downstream-artifacts list into the per-step bite-sized tasks the implementer agent (or the user) executes.
