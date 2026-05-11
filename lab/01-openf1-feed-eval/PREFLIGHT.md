# PREFLIGHT — openf1-feed-eval

## Hypothesis

**OpenF1's REST + WebSocket endpoints are reliable, low-latency (≤ 10 s end-to-end), and complete enough to serve as the primary data source for Pitwall's live timing tower and track-position map across all session types (FP1-3 / Quali / Sprint Quali / Sprint / Race).**

## Why this matters

Pitwall's live-session view is the headline feature. If OpenF1 is unreliable, rate-limited, or missing position data, we need to know BEFORE we build screens against it. The fallback option is FastF1's live-timing client, which has heavier dependencies and a different access pattern. The whole `build/workflows/01-project-skeleton/` iteration depends on this answer.

## Prior art

- [x] Searched for existing OpenF1 client libraries
- [x] Reviewed OpenF1 API docs (https://openf1.org/)
- [x] Identified `faceoff`'s `NHLClient` as the structural pattern to mirror

**Notes:**

- OpenF1 publishes a REST API at `https://api.openf1.org/v1/` with endpoints for `sessions`, `drivers`, `position`, `intervals`, `laps`, `pit`, `stints`, `weather`, `race_control`, `team_radio`, etc. WebSocket streams also exist but the documentation is thinner than REST.
- The `position` endpoint provides per-driver `x` / `y` coordinates updated every ~3.7 s per their docs — this is what powers the track map.
- Faceoff polls its NHL endpoint on a refresh interval (default 30 s, min 5 s). For F1 live timing, 5 s feels like the right floor; lower is unnecessary given the data update cadence.
- No pre-existing Python OpenF1 wrapper appears widely adopted; a thin async `httpx` wrapper is the right shape (mirrors faceoff's `NHLClient`).
- OpenF1 is community-run; SLA expectations should be modest. Caching + graceful degradation matters.

## Approach

1. Build a thin async OpenF1 client in `prototype/openf1.py`, wrapping `httpx.AsyncClient`. Single-flight + last-response cache.
2. Pick a **concluded** session (e.g., the 2026 Bahrain GP race, or the most recent at the time the spike runs) and pull every endpoint we expect to need: `sessions`, `drivers`, `position`, `intervals`, `laps`, `stints`, `weather`, `race_control`.
3. Measure for each endpoint: response time, payload size, completeness (do we get every driver every tick?).
4. If a session is live during the spike window, repeat against the live stream and measure end-to-end latency (race-clock → arrival in our local cache).
5. Build a tiny terminal sketch: project `position` x/y onto a static circuit outline (Bahrain or whatever session we use) and render driver markers cell-by-cell.

## Success criteria

- Pulled every listed endpoint from at least one concluded session without errors.
- Position data covers every driver on the grid for ≥ 95 % of ticks across the session.
- End-to-end latency from API to local cache is ≤ 5 s median, ≤ 10 s p95, across a 5-minute live window.
- Track-map projection produces a visually identifiable circuit shape with driver markers in plausible positions when rendered with one cell per driver.

## Failure criteria

- Endpoint returns HTTP 429 (rate limit) more than once per minute under polling at the documented intervals.
- Position data has > 10 % missing ticks per driver across a session.
- End-to-end latency exceeds 15 s median — too slow to feel "live."
- Track-map projection produces noise (no recognizable circuit shape) despite reasonable coordinate normalization.
- The free OpenF1 service is down for > 1 hour during the spike window with no documented status.

## Time box

Walk away after **2 days (~16 hours)**. If we're past the box, the REPORT records what we have and we decide explicitly:
- **Pursue** — OpenF1 is good enough, proceed to `build/workflows/01-project-skeleton/`.
- **Modify** — add FastF1 as a fallback for the failing endpoints, narrow the spike, run `lab/02-`.
- **Abandon** — replace OpenF1 with FastF1's live-timing client; write `docs/explorations/01-openf1-feed-eval.md`.
