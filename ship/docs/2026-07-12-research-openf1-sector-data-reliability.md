<!-- wayfinder asset: resolves ticket #4 (OpenF1 sector and mini-sector data reliability) on map #2 (Future roadmap spec) - resolved 2026-07-12 -->

# Research: OpenF1 sector / mini-sector data reliability (Ticket #4)

## Question
Does OpenF1 expose sector and mini-sector timing reliably enough (session coverage, latency, schema stability, free-tier limits) to add sector colours to Pitwall's live tower?

## Findings (with evidence)

### 1. Schema — stable and sufficient
The `laps` endpoint carries, per lap: `duration_sector_1/2/3` (float seconds), `segments_sector_1/2/3` (arrays of mini-sector colour codes), plus `i1_speed`, `i2_speed`, `st_speed`, `is_pit_out_lap`, `lap_duration`. Verified identical key set in 2025 (Melbourne race, session 9693) and 2026 (Silverstone race, session 11326) via live `curl` this session.

Documented segment colour codes (openf1.org/docs): `0` = not available, `2048` = yellow, `2049` = green, `2051` = purple, `2064` = pitlane; `2050/2052/2068` = "unknown". Observed values in real payloads matched exactly: `{2048, 2049, 2051, 2064}` in 2026 Silverstone quali/race, plus `0` and one `2052` occurrence in 2026 Spielberg race. Docs warn segment values "may not always align perfectly with the colors shown on TV".

Deprecations announced for end of 2026 season affect only `country_code` and `pit_duration` — no sector fields.

### 2. Coverage — observed across session types, including races
Sampled real payloads (api.openf1.org, fetched this session):
- **2025 Australian GP Race (9693)**: segments populated lap-by-lap; SC laps show all-2048 (yellow); pit entry shows 2064.
- **2026 Silverstone Qualifying (11322)**: 309 laps, **309** with segments; 208 with `duration_sector_1` (out-laps/aborted laps lack durations — expected in quali).
- **2026 Silverstone Race (11326)**: 1114 laps, 1113 with segments, 1112 with sector durations.
- **2026 Austrian GP Race (11315)**: 1342 laps, 1340 with segments.

**Docs conflict (flagged, not resolved):** openf1.org/docs states "Segments are not available during races", yet every race payload sampled (2025 and 2026) has fully populated segment arrays for historical data. Either the note is stale or refers only to the live feed during races — needs a live-session probe to settle.

### 3. Null pattern — narrow and handleable
In the 2026 Silverstone race: 826 null/0 entries out of 30,004 segment values (**2.8%**). Position analysis: **822 of 826 are segment index 0 of sector 1** (the start-line mini-sector), spread evenly across lap numbers. So: render "no colour" for a null mini-sector and the degradation is one dead cell at the start line, not random holes.

### 4. Access tier / latency — the real constraint
Per openf1.org/docs and openf1.org/auth.html:
- **Unauthenticated (free):** historical data from 2023 onward only. No rate-limit numbers published.
- **Authenticated (paid, Stripe sponsorship model):** real-time data, MQTT/WebSocket streaming, "increased rate limits" (unquantified). Tokens expire after 1 hour — client must refresh.
- No documented latency figure for `laps`; sector data plausibly lands at sector boundaries. (`intervals` is documented at ~4 s update cadence, races only.)

This matches Pitwall's existing OpenF1 live/replay split: **replay mode gets sector colours for free; true live sector colours require the paid tier** — same constraint the live tower already has for any OpenF1 live data, so it adds no *new* dependency.

## Options compared
| Option | Coverage | Licence/cost | Freshness | Effort |
|---|---|---|---|---|
| OpenF1 `laps` sector fields (recommended) | All session types sampled; 2023→2026 | Free historical; paid real-time | Historical: post-hoc; live: paid, per-sector cadence | Low — one endpoint Pitwall already consumes |
| FastF1 | Rich sector data | Free | Post-session only; heavy deps (pandas) — against repo policy | High (new dep, no live) |
| Jolpica-F1 | No mini-sector data | Free | n/a | n/a — doesn't cover this |

## Recommendation
Proceed. Build sector colours on `segments_sector_1/2/3` + `duration_sector_1/2/3` from the `laps` endpoint. Map `{2049: green, 2051: purple, 2048: yellow, 2064: pit}`; treat `0`, `null`, and unknown codes (2050/2052/2068) as "no colour". Design for the observed null-at-start-line quirk. Gate the *live* path on authenticated OpenF1 access (already the live tower's posture); replay/post-session works free today. Before shipping the live path, probe one actual live session to resolve the "segments not available during races" docs conflict.

## Sources (all fetched this session)
- https://openf1.org/docs/ — laps endpoint, segment colour table, tier notes, deprecations
- https://openf1.org/auth.html — auth, MQTT/WebSocket, token expiry, real-time paywall
- https://api.openf1.org/v1/laps?session_key=9693&driver_number=1&lap_number<4 (2025 Australia race sample)
- https://api.openf1.org/v1/laps?session_key=11322 / 11326 / 11315 (2026 Silverstone quali+race, Spielberg race — aggregate analysis)
- https://api.openf1.org/v1/sessions?year=2025 / year=2026 (session keys)