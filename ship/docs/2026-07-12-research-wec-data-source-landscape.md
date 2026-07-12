<!-- wayfinder asset: resolves ticket #5 (WEC data source landscape) on map #2 (Future roadmap spec) - resolved 2026-07-12 -->

# Research: WEC data source landscape (ticket #5)

## Question
What reliable data sources exist for FIA WEC sessions (live timing, entry lists, multi-class results, schedules), and how far do they diverge from the Jolpica/OpenF1 shapes Pitwall already models? Go/no-go on WEC expansion hangs on this.

## Findings (with evidence)

### 1. Official timing: Alkamel Systems — sole provider, no public API
- Al Kamel Systems has been WEC's timing provider since 2012; its results portal (https://fiawec.alkamelsystems.com/) is the official archive. Fetched 2026-07-12: current-season (São Paulo 2026) session results are publicly downloadable — **PDF + CSV**, no login — covering classifications, fastest laps, sectors, top speeds, weather, track-limit violations, per session (FP1-3, per-class Qualifying + Hyperpole, Race).
- **ToS is explicitly hostile to redistribution.** Verbatim from the portal: "the data contained on this page is wholly owned by Al Kamel Systems S.L. Any attempt by 3rd parties to distribute and/or disseminate any data contained on this page without the previous express consent by Al Kamel Systems S.L. will lead to legal action taken by the company." Personal/local use is not addressed; redistribution (e.g., a Pitwall-run proxy or cache service) is clearly out.
- **Live feed is credentialed and paid.** HH Timing's timekeeper docs (https://help.hhtiming.com/timekeeper-specific-info/alkamel-v2/): Alkamel V2 is "a JSON protocol that Al Kamel introduced in 2017"; WEC cloud host `fiawec.datapublisher.alkamelcloud.com`; users "must obtain a user name and password from Al Kamel." From **2026 Al Kamel filters sessions by credential** — purchasers see only championships they've paid for. This is a team/professional product, not a fan API.

### 2. Historical CSV shape (the one machine-readable asset)
- f1datajunkie/WEC (Apache-2.0, https://github.com/f1datajunkie/WEC) demonstrates the archive CSV pattern:
  `http://fiawec.alkamelsystems.com/Results/<season>/<round>/<champ>/<timestamp>_Race/Hour N/23_Analysis_Race_Hour N.CSV`
- Confirmed columns from the raw notebook (fetched this session): `NUMBER, DRIVER_NUMBER, LAP_NUMBER, LAP_TIME, LAP_IMPROVEMENT, CROSSING_FINISH_LINE_IN_PIT, S1..S3 (+improvements, +large), KPH, ELAPSED, HOUR, TOP_SPEED, DRIVER_NAME, PIT_TIME, CLASS, GROUP, TEAM, MANUFACTURER`. Rich lap-by-lap data with driver rotation and class baked in — but flat CSV per session/segment, not a queryable API.

### 3. Community landscape: thin and legally constrained
- **Timing71** (https://info.timing71.org/opensource.html) — the serious endurance live-timing aggregator. Core (`livetiming-core`, AGPL-3.0) is open, but it deliberately ships **no provider plugins**: they "contain reverse-engineered proprietary or commercial code which cannot be distributed." I.e., the one mature project in this space concluded the WEC connector itself cannot be published.
- **hankscorpio83/better-timing** (https://github.com/hankscorpio83/better-timing) — browser extension that watched the FIA live-timing page's XHR JSON; **archived 2021-08-05** ("the FIA timing website has been redesigned, this extension no longer works"); it deliberately stored nothing "to avoid potential intellectual property concerns." A cautionary precedent for scraping the live page.
- Searches for an unofficial WEC REST API / "OpenWEC" community service returned nothing viable (searched this session; only entry-list news pages and PDFs).

### 4. Entry lists & schedules
- fiawec.com publishes entry lists and calendars as web pages and **PDFs** (e.g., https://press.fiawec.com provisional entry list PDFs) — no structured feed. Wikipedia is the usual community-structured fallback. Nothing comparable to Jolpica's clean REST season endpoints.

### 5. Modelling deltas vs Pitwall's Jolpica/OpenF1 shapes
- **Car-centric, not driver-centric:** WEC entry = car `NUMBER` with 2-3 rotating drivers (`DRIVER_NUMBER` is per-car). OpenF1/Jolpica assume driver_number ↔ driver 1:1; Pitwall would need a Car/Crew entity plus stint→driver attribution.
- **Multi-class:** Hypercar + LMGT3 (LMP2 at Le Mans). Every classification, gap, quali (per-class Hyperpole), and championship table is per-class as well as overall — Pitwall's single classification model doesn't hold.
- **Session structure:** time-based 6/8/10/24h races; results segmented by "Hour N" files; lap counts differ wildly per class; safety-car/slow-zone regimes differ. Replay/live pacing assumptions from OpenF1 (short fixed-format sessions, per-driver telemetry endpoints) don't transfer.
- **No live positional/telemetry analog:** OpenF1's location/car_data endpoints have no public WEC counterpart at all.

## Options compared
| Option | Coverage | Licence/ToS | Freshness | Effort |
|---|---|---|---|---|
| Alkamel V2 live feed | Full live timing + GPS | Paid, credentialed, team-oriented; 2026 credential filtering | Live | Blocked (commercial) |
| Scrape FIA live-timing page | Live leaderboard only | Explicit legal-action ToS; precedent (better-timing) died on redesign | Live | High + fragile + hostile |
| Alkamel archive CSVs | Lap/sector/class/driver, post-session | Download works today, no login; redistribution forbidden — local-use-only | Post-session (hours) | Moderate (CSV ingester + new multi-class model) |
| fiawec.com pages/PDFs | Schedule, entry lists, news | Website ToS; PDFs | Days | Scraping/PDF parsing, brittle |
| Community API | — | — | — | None exists (searched this session) |

## Recommendation
**No-go on WEC live-session parity.** The load-bearing fact: F1's community ecosystem (OpenF1, Jolpica) has no WEC equivalent, and the sole timing provider's ToS plus the 2026 credential tightening point the wrong direction. Timing71's decision not to publish provider plugins is strong independent evidence that a clean-room public connector isn't distributable.

If WEC appetite remains, the only defensible slice is a **local-only, post-session Alkamel CSV analysis mode** (user downloads CSVs; Pitwall never redistributes) — but that requires a genuinely new multi-class/car-crew data model, so it should be treated as a separate product decision, not an incremental data-source add.

## Sources (all fetched this session)
- https://fiawec.alkamelsystems.com/ (portal contents, ToS quote)
- https://help.hhtiming.com/timekeeper-specific-info/alkamel-v2/ (V2 protocol, hosts, credentials, 2026 filtering)
- https://github.com/f1datajunkie/WEC + raw `notebooks/Simple demo.ipynb` (CSV URL pattern, columns)
- https://info.timing71.org/opensource.html (open-source scope, no provider plugins)
- https://github.com/hankscorpio83/better-timing (archived scraper precedent)
- Web searches for community WEC APIs (fiawec.com results/entry-list pages, press PDFs; no API found)