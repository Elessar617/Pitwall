<!-- wayfinder asset: resolves ticket #3 (Tyre-degradation data source survey) on map #2 (Future roadmap spec) - resolved 2026-07-12 -->

# Research: Tyre-degradation data source for strategy game v2

## Question
Which data source can feed per-stint tyre-degradation curves and undercut/overcut hints for
strategy game v2 — OpenF1 derivations, third-party datasets (FastF1, community), or curves
self-derived from Pitwall's own recorded laps?

## Findings

### What the repo already has (checked first)
- `data/` ships **no pre-fit degradation curves**. It contains OpenF1 **fixtures** for one
  session (`data/fixtures/1285_11291/`): `laps.json` (1,212 laps: `lap_duration`, sector
  durations, `is_pit_out_lap`), `stints.json` (56 stints: `compound`, `lap_start`,
  `lap_end`, `tyre_age_at_start`), plus `pit.json` (pit durations) and `race_control.json`
  (SC/VSC flags for lap filtering).
- The CLAUDE.md map's "tyre-deg curves" entry is aspirational: `spec/briefs/pitwall-overview.md:22`
  says the SQLite cache exists "so tyre-degradation curves don't refit every launch" — i.e.
  the design intent was always *fit-and-cache*, not *ship a dataset*.
- `ROADMAP.md:14`: per-stint degradation + undercut/overcut hints is "the original v2 idea,
  dependent on a degradation data source."
- Game code (`src/pitwall/game/`) currently scores compound/pit-lap matching only; no lap-time
  model exists yet.

### Option A — OpenF1 derivation (stints + laps)
Verified live this session (`curl api.openf1.org/v1/stints`, `/v1/laps`): stints give
`compound`, `lap_start/end`, `tyre_age_at_start`; laps give per-lap `lap_duration` + sector
times + `is_pit_out_lap`. That is the complete input for fitting a per-driver-per-compound
lap-time-vs-tyre-age slope. Per https://openf1.org/: historical data **free since 2023**;
live updates "about 3 seconds after live events"; free tier "3 req/s and 30 req/min";
licence **CC BY-NC-SA 4.0**, "intended for … non-commercial fan engagement" — the licence
posture Pitwall already accepted by building live timing on it.

### Option B — FastF1
MIT-licensed wrapper over the official F1 live-timing streams; `Session.laps` includes
`Compound` and `TyreLife` (https://docs.fastf1.dev/, http://docs.fastf1.dev/core.html).
But: "All data is provided in the form of extended Pandas DataFrames" — a hard **pandas
dependency**, which Pitwall's stack explicitly excludes absent measured justification. For
degradation specifically it carries the *same* lap/compound/stint signal OpenF1 already
provides; its extra value (car telemetry) is not needed for deg curves. Net: dependency
cost, no marginal signal.

### Option C — Community / academic datasets
- **TUMFTM/race-simulation** (https://github.com/TUMFTM/race-simulation): LGPL-3.0; ships
  "exemplary parameter files for the 121 Formula 1 races in the seasons from 2014 to 2019."
  Companion **f1-timing-database** covers 2014–2019 only. Two regulation eras stale
  (pre-ground-effect, pre-18" tyres); useless for current-season hints. Its *model shape*
  (lap-wise deg + fuel-burn correction) is still a good design reference.
- Kaggle/Ergast-derived sets: Ergast/Jolpica carries no tyre compound or stint data, so
  these cannot feed deg curves at all (Jolpica is Pitwall's season-data source; laps there
  lack compounds).

### Option D — "Pitwall's own recorded laps"
Collapses into Option A: Pitwall's recorded laps *are* OpenF1 payloads (the fixtures prove
it). Recording sessions locally is the caching layer for A, not a separate source.

## Comparison

| Source | Coverage | Licence | Freshness | Integration effort |
|---|---|---|---|---|
| OpenF1 stints+laps | 2023→now, all sessions | CC BY-NC-SA 4.0 (already accepted) | ~3 s live | Low — client, models, fixtures already exist |
| FastF1 | 2018→now (timing) | MIT (lib) | Post-session load | Medium-high — adds pandas/numpy stack against repo policy |
| TUMFTM params | 2014–2019 only | LGPL-3.0 | Frozen | Low to copy, but data is obsolete |
| Kaggle/Ergast | No tyre data | varies | n/a | n/a — cannot answer the question |

## Recommendation
**Self-derive from OpenF1** (Option A/D). Fit per-compound linear deg slopes from
`lap_duration` vs tyre age per stint, filtering `is_pit_out_lap`, in-laps, and SC/VSC laps
(via `race_control`), with a simple constant fuel-burn correction (TUMFTM's model shape).
Persist fitted curves in the existing SQLite cache keyed by `(session_key, driver_number,
compound)`, matching the spec brief's stated intent. Undercut/overcut hints derive from the
same inputs: rival deg slopes + pit-loss estimated from `pit.json` durations. Zero new
dependencies; the fixture session is a ready-made offline test bed. Signal quality (noise
from traffic/fuel) is the open risk — a small prototype should validate slope
signal-to-noise before speccing v2.

## Sources
- Repo: `data/fixtures/1285_11291/{laps,stints,pit,race_control}.json`, `ROADMAP.md:14`,
  `spec/briefs/pitwall-overview.md:22`, `src/pitwall/game/`
- https://openf1.org/ (licence, rate limits, freshness, 2023+ coverage)
- https://api.openf1.org/v1/stints?session_key=9939&driver_number=1 and
  https://api.openf1.org/v1/laps?session_key=9939&driver_number=1&lap_number>=10&lap_number<=13 (live payloads)
- https://docs.fastf1.dev/ and http://docs.fastf1.dev/core.html (FastF1 data/pandas; MIT per search results)
- https://github.com/TUMFTM/race-simulation (LGPL-3.0; 2014–2019 parameter files)