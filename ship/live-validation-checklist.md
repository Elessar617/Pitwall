# Live Validation Checklist

> [!IMPORTANT]
> This checklist is strictly operator-run at a real, live F1 session and is never executed in CI.

## Purpose

This document provides a manual validation protocol for Pitwall's live-timing capabilities. It ensures that session discovery, UI state transitions, polling cadence, and data degradation paths perform correctly against the live OpenF1 API during an active session.

## Preconditions

1. Active internet connection with access to `api.openf1.org`.
2. Pitwall installed and runnable via `uv`.
3. An active or recently completed F1 session is scheduled or running.

## Launch

Run the following command to start Pitwall in live mode:

```bash
uv run pitwall --live
```

## What to verify

1. **Discovery Semantics Check**: Verify that the first request is issued to `sessions?session_key=latest` to discover the active session. The application must parse the response and extract the actual numeric `session_key` to use in subsequent telemetry requests (e.g., `drivers?session_key=<session_key>`), rather than passing the `"latest"` literal string to those endpoints.
2. **Cadence Bounds**: Ensure that the polling rate maintains a disciplined cadence of under 1 request per second (sustained `< 1 req/s` at the default interval of 10.0 seconds, which performs up to 8 requests per tick, i.e., ~0.8 req/s).
3. **Data-Lag Caveat**: Note that location data (lat/long coordinates) may lag by hours or days compared to telemetry feeds. If so, the braille track map will not display (it requires a minimum span and point count to project the outline) and the UI must gracefully fall back to a tower-only layout with no error. The map may legitimately never appear.
4. **404-as-Empty Handling**: Verify that individual HTTP 404 responses for streams are treated gracefully as empty streams (quiet empty windows yielding `events == ()`) and do not raise errors or crash the application.
5. **State Transition Verification**: Confirm that the UI status transitions match the verbatim strings in the table below:

### Verification Table

| Scenario / State | Expected Status String (Verbatim) | Description / Trigger |
|---|---|---|
| Discovery in flight | `Connecting to live session…` | Initial connection state when starting in live mode. |
| No live session (Replay/No-session regression) | `No live session — start pitwall with --live or --replay <fixtures-dir>.` | App started without live flag or fixtures directory. |
| Open window, no data | `Live: Race — waiting for data…` | Session discovered but no stream records yielded yet. |
| Healthy ticking | `Live · data to 20:32:29 UTC` | Data head exists; updates to match the latest playhead timestamp. |
| Failing poll after healthy tick | `Live · data to 20:32:29 UTC · retrying (1)` | Telemetry stream failed to fetch; suffix scales to `retrying (N)`. |
| Window closed / Loop ended | `Live ended · data to 20:32:29 UTC` | Session is completed and overrun grace period expired. |
| Discovery transport error | `Live unavailable — could not reach OpenF1.` | Network/host down during initial discovery call. |
| Discovery empty/404 | `Live unavailable — no session found.` | API returned empty or 404 response for session list. |
| Upcoming session | `Live: Race has not started — begins 19:00 UTC.` | Clock time is before `date_start` minus pre-session grace. |
| Ended session | `Live unavailable — latest session (Race) ended 21:00 UTC.` | Clock time is past `date_end` plus overrun grace. |

## Known degradations

* **Location Lag**: Map doesn't show because location data is lagging or 404ing (location may lag by days — the map may legitimately never appear).
* **Transient API Failures**: Table or status suffixes with ` · retrying (N)`.
* **Out-of-Order Packets**: Location markers might arrive out of order but are handled gracefully without crashing.

## Failure drill

1. **Disconnect Network**: Disconnect network cable/Wi-Fi. Verify status changes to `Live · data to 20:32:29 UTC · retrying (1)`.
2. **Reconnect Network**: Reconnect network. Verify status returns to healthy `Live · data to 20:32:29 UTC` and the retrying suffix is removed.
3. **Discovery Failure**: Block access to the sessions endpoint, verify the status displays `Live unavailable — could not reach OpenF1.` and a single notification severity error is triggered.

## Post-session fixture capture

After the session concludes, capture the fixture data using the script below:

```bash
python3 scripts/capture_openf1_session.py <meeting_key> <session_key>
```

## Findings record

Use this table to record observations during the live run and route them to the next planner.

| Observed Behavior | Actual String / Output | Pass/Fail | Notes / Next Actions (Route to Next Planner) |
|---|---|---|---|
| Discovery (`latest` semantics) | | | |
| Window check | | | |
| Ticking states | | | |
| Degradation (404/Retries) | | | |
| Location Lag fallback | | | |
| Subprocess execution | | | |
