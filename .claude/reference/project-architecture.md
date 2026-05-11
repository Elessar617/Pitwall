# Project Architecture

## Overview

Pitwall is a terminal-UI companion for Formula 1. It runs in three modes that share a single Textual app: a **live session view** (timing tower + real-time track map for FP1-3 / Quali / Sprint Quali / Sprint / Race), a **season tracker** (schedule, standings, results, driver and constructor profiles), and a **strategy mini-game** the user plays alongside an in-progress race (commit a tyre + pit plan pre-race, react to pit-window prompts mid-race, see a player-vs-actual delta score at the end). The full live strategist — safety-car reactions, weather, undercut logic — is deferred to v2.

## Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Textual App  (src/pitwall/app.py)                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Screens  (src/pitwall/screens/)                                   │  │
│  │   season · live_timing · track_map · driver · strategy            │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                        ▲ read              ▲ subscribe                  │
└────────────────────────│────────────────────│───────────────────────────┘
                         │                    │
        ┌────────────────┴────────────────────┴─────────────────────────┐
        │ SQLite cache  (data/pitwall.db)                                │
        │   sessions · drivers · constructors · standings · positions   │
        │   laps · plans · scores                                        │
        └────────────────▲─────────────────────▲─────────────────────────┘
                         │ write               │ write
        ┌────────────────┴────┐ ┌──────────────┴───────────────────────┐
        │ Async workers  (src/pitwall/workers/)                         │
        │   live (OpenF1 WS) · season (Jolpica) · telemetry (FastF1)   │
        │   sim (plan prediction + scoring)                             │
        └───────────────────────────────────────────────────────────────┘
```

- **App shell** (`app.py`, `cli.py`) — launches Textual, parses CLI flags, owns the worker lifecycle.
- **Screens** — pure renderers. Read from the SQLite cache; subscribe to worker push messages for live data. Each screen is a single file under `screens/`.
- **Workers** — async background tasks that fetch from APIs and write to the cache. They are the only code that touches the network.
- **Strategy sim** (`src/pitwall/sim/`) — fits tyre-degradation curves from FastF1 history, predicts finish position for a plan, scores player vs actual at race end.
- **SQLite cache** (`data/pitwall.db`) — the only shared mutable state between workers and screens. Schema lives in `cache/db.py`.

## Data flow

1. CLI parses flags (e.g., `--refresh-interval`, `--year`) and starts the Textual app.
2. App spawns workers. The **season worker** fetches once per launch (schedule + standings). The **live worker** only starts when a session is in progress (detected via the schedule).
3. Workers fetch → write to SQLite → emit a Textual message ("season updated", "live tick", "position update").
4. Screens subscribe to the messages they care about; on receipt they re-query the cache and re-render.
5. Strategy plans are written by the user to the `plans` table. The **sim worker** computes predictions on commit, on each pit-window event, and writes the final score to the `scores` table at race end.

## External dependencies

- **OpenF1** (`api.openf1.org`) — REST + WebSocket relay of the F1 live timing feed. Free, no auth. Provides driver positions (the source of the track map), gaps, sector times, lap data during sessions.
- **Jolpica-F1** (`api.jolpi.ca/ergast/`) — direct successor to the now-frozen Ergast API. Free REST. Powers schedule, standings, drivers, constructors, results history.
- **FastF1** (Python lib) — wraps the official F1 timing API plus Ergast. Used for tyre compound history and telemetry to fit tyre-degradation curves for the sim. Heavier install (`pandas`, `numpy`); used in batch and cached.
- **SQLite** (stdlib `sqlite3`) — local cache. No external server.

## Deployment topology

Single Python process. No daemon, no server. The user runs `uvx pitwall` and quits when done. The SQLite cache persists in `data/pitwall.db` across runs; deleting the file is a clean reset.

## Folder layout

```
src/pitwall/
├── __init__.py            # version
├── cli.py                 # entrypoint (the `pitwall` command + arg parsing)
├── app.py                 # Textual App; owns workers
├── api/                   # thin HTTP clients (one per source)
│   ├── openf1.py
│   ├── jolpica.py
│   └── fastf1_wrap.py     # narrow wrapper around the fastf1 lib
├── workers/               # async background tasks
│   ├── live.py
│   ├── season.py
│   ├── telemetry.py
│   └── sim.py
├── cache/                 # SQLite schema + access
│   └── db.py
├── screens/               # one file per screen
│   ├── season.py
│   ├── live_timing.py
│   ├── track_map.py
│   ├── driver.py
│   └── strategy.py
├── widgets/               # reusable widgets (timing row, track-map canvas, etc.)
└── sim/                   # tyre-deg model + plan prediction + scoring
    ├── curves.py
    ├── predict.py
    └── score.py

shared/                    # cross-cutting infrastructure (logging, config, error types)
data/                      # runtime data
├── pitwall.db             # SQLite cache (created on first run)
└── curves/                # pre-fit tyre-deg curves keyed by track + compound (optional)
```
