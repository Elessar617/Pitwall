<!-- wayfinder asset: resolves ticket #14 (Measure unauthenticated OpenF1 rate limits empirically) on map #2 - resolved 2026-07-12 -->

# Wayfinder #14 — OpenF1 rate limits vs Pitwall polling cadence

## Question
What request rate does api.openf1.org tolerate unauthenticated before 429s, and does Pitwall's replay/live polling cadence fit under it?

## Documented limits (openf1.org, fetched 2026-07)
- **Free/community tier (unauthenticated): "3 req/s and 30 req/min"** — confirms the prior researcher's numbers.
- Paid sponsor tier (EUR 9.90/mo): **6 req/s and 60 req/min**, plus MQTT/WebSocket. **Live (real-time) data requires sponsorship; unauthenticated access is historical data only** — relevant caveat for Pitwall's live mode.
- No published burst/ban policy and no ToS language about probing. License CC BY-NC-SA 4.0, non-commercial.

## Measured behaviour (budget halved to 30 req since docs state numbers; UA `pitwall-research/0.1 (github.com/Elessar617/Pitwall)`, endpoint `/v1/sessions?session_key=latest`)

| Phase | Target rate | Achieved rate | Requests | Outcome |
|---|---|---|---|---|
| 1 | 1 req/s | ~0.66 req/s (curl latency) | 10 | all 200 |
| 2 | 2 req/s | ~1.0 req/s (latency-bound) | 20 | all 200 |

- **30 requests completed in ~34.6 s — i.e. >30 req within a 60 s window — with zero 429s.**
- **No rate-limit headers whatsoever** (no `Retry-After`, no `x-ratelimit-*`); response headers were plain nginx + security headers only.
- Conclusion: enforcement is laxer than the documented 30 req/min at this rate, but the probe stopped at budget without ever finding the actual 429 threshold. Design to the documented numbers, not the observed leniency.

## Pitwall cadence fit
Code read (all paths under `/Users/gardnerwilson/workspace/github.com/elessar617/Pitwall`):
- `src/pitwall/openf1/live.py:19` — `LIVE_POLL_INTERVAL_S = 10.0`; `src/pitwall/screens/live_timing.py:392-397` constructs `LiveSource` **without** overriding it, so config's `refresh_interval_s` (default 30, min 5, `src/pitwall/config.py:13-14`) does **not** govern live polling.
- Per tick (`live.py:267-282`): 5 stream endpoints (`position`, `intervals`, `laps`, `pit`, `race_control` in `_collect_tick_events`, live.py:224-239) + `location` = **6 requests/tick**; +1 `stints` every 6th tick; +1 `drivers` on tick 0. Requests are sequential awaits (no burst fan-out).
- **Steady state: 6 ticks/min × 6 + 1 stints = 37 req/min ≈ 0.62 req/s** (first minute 38).
- Burst: sequential requests with ~0.5 s observed latency ≈ 2 req/s momentary — under the 3 req/s cap, but a fast server could push it near the line.
- 429 handling (`src/pitwall/openf1/client.py:100-122`): up to 3 retries with 1/2/4 s backoff, then `OpenF1RateLimitedError`; retries add load during a limit episode; `Retry-After` is not honored (none observed in practice).
- **Replay: zero network.** `src/pitwall/openf1/replay.py:72-105` reads local JSON fixtures (`open`/`json.load`); no httpx usage.

**Verdict: live mode does NOT fit the documented free tier** — 37 req/min vs 30 req/min limit (~23% over). It fits the paid tier (60 req/min) with 38% headroom. Empirically the free tier tolerated our probe's pace, so live mode may work in practice today, but it is out of documented spec — and OpenF1 says real-time data itself requires sponsorship anyway. Replay mode is trivially fine (0 req).

## Recommendation
1. Raise `LIVE_POLL_INTERVAL_S` from 10 s to **15 s** → 4 ticks/min × 6 + 1 = **25 req/min**, ~17% headroom under the documented free limit (and comfortably under paid).
2. Add a client-side token-bucket limiter in `OpenF1Client._request` (30/min and 3/s, configurable) so cadence changes elsewhere can't silently exceed the budget; honor `Retry-After` if it ever appears.
3. Note in `.claude/reference/` that OpenF1's real-time feed is sponsor-gated; unauthenticated "live" polling serves delayed/historical data at best.
4. Replay requires no guard — fully offline.

## Sources
- https://openf1.org (fetched this session): free tier "3 req/s and 30 req/min"; sponsor tier "6 req/s and 60 req/min"; live data requires sponsorship; no burst/ban/probing policy published.
- Empirical probe transcript (this session): 30/30 HTTP 200 over 34.6 s, no rate-limit headers.
- Code: `src/pitwall/openf1/live.py`, `src/pitwall/openf1/client.py`, `src/pitwall/openf1/replay.py`, `src/pitwall/config.py`, `src/pitwall/screens/live_timing.py`.
