# Brief: Pitwall — Formula 1 TUI Companion

## Goal

Ship a terminal-UI application for following live F1 sessions, tracking the season, and playing a small strategy mini-game alongside an in-progress race. Inspired by F1 MultiViewer (live timing UX), Golden Lap (strategy-sim feel), and the `faceoff` NHL TUI (structural reference for screens, async workers, and the Python + Textual stack).

## Why now

There is no good open-source CLI/TUI companion for Formula 1. F1 MultiViewer is paid and GUI-only; the OpenF1 + Jolpica-F1 + FastF1 trio now provides a complete public-data path that didn't exist a few years ago. A fan-oriented terminal tool that combines live data with a small interactive strategy element is a natural fit and a fun project.

## In scope (v1)

- **Live session view** for FP1 / FP2 / FP3 / Qualifying / Sprint Qualifying / Sprint / Race
  - Live timing tower (gap, last lap, sector colors, tyre, age, pit count)
  - Track-position map (driver locations rendered on the circuit outline)
  - Race control messages, weather, flag state
- **Season tracker** — schedule, drivers' standings, constructors' standings, results history, driver / constructor profiles
- **Strategy mini-game**
  - Pre-race plan commit (tyre choice + pit-lap targets)
  - Live pit-window prompts during the race (`pit now` / `stay out` / `wait one`)
  - End-of-race player-vs-actual delta score
- SQLite cache so the season tracker works offline once seeded, and so tyre-degradation curves don't refit every launch

## Out of scope (v1 — deferred to v2 or later)

- Full live race strategist with safety-car reactions, weather changes, and undercut/overcut logic
- Telemetry charts (throttle/brake traces, gear, RPM)
- Onboard video feeds
- F1 TV integration (paid)
- Mobile or web frontend

## Success criteria

- During a live session, the TUI renders timing + positions for every driver, refreshing at the user-selected interval (default 30 s, min 5 s).
- Between sessions / off-season, the TUI shows the next race, current standings, and the last race's results **without network calls** (using the SQLite cache).
- A user can commit a strategy before a race, get pit-window prompts during it, and see a player-vs-actual score at the end.
- Tests cover ≥ 75 % of changed lines on every PR (per `.claude/rules/testing-discipline.md`).
- `uv run pitwall` works on macOS, Linux, and Windows (modern terminal required).

## Constraints

- **Publicly available F1 data only** — OpenF1, Jolpica-F1, FastF1. No paid sources, no scraping of restricted endpoints.
- **Python 3.13 + Textual + uv + ruff + ty**, matching the faceoff reference.
- Stay within `.claude/rules/portability-discipline.md` — F1 facts in `.claude/reference/`, not in `.claude/rules/` or `.claude/skills/`.

## Downstream work this seeds

- [`lab/01-openf1-feed-eval/`](../../lab/01-openf1-feed-eval/) — validate OpenF1 reliability / latency / completeness during a live session before committing to it as the primary live source.
- `spec/adrs/0001-stack-python-textual.md` — ADR recording the Python + Textual decision (created during Part C of the project plan).
- `spec/adrs/0002-data-sources.md` — ADR recording the OpenF1 / Jolpica / FastF1 triad (created during Part C).
- `build/workflows/01-project-skeleton/` — first build iteration (CLI entry, app shell, screen router, SQLite schema).

## Open questions to resolve in `lab/`

- OpenF1's real-time latency profile and rate limits under sustained polling.
- FastF1's offline curve-fitting cost (time + memory) and the right re-fit cadence (per-race? per-season?).
- Track outline data — does FastF1's `Session.get_circuit_info()` give enough fidelity for an ASCII / Unicode track map, or do we need per-circuit static data files?
- Cross-platform Textual rendering at typical terminal sizes (80×24 minimum, 120×40 preferred for the track map).
