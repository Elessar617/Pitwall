# Graph Report - .  (2026-06-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 705 nodes · 1765 edges · 30 communities (23 shown, 7 thin omitted)
- Extraction: 65% EXTRACTED · 35% INFERRED · 0% AMBIGUOUS · INFERRED: 622 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4524e9bc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]

## God Nodes (most connected - your core abstractions)
1. `DataParseError` - 81 edges
2. `PitwallScreen` - 47 edges
3. `SeasonSnapshot` - 43 edges
4. `JolpicaClient` - 40 edges
5. `JolpicaError` - 37 edges
6. `Race` - 37 edges
7. `RaceResult` - 32 edges
8. `Driver` - 30 edges
9. `Constructor` - 30 edges
10. `DriverStanding` - 30 edges

## Surprising Connections (you probably didn't know these)
- `JolpicaClient` --uses--> `DataParseError`  [INFERRED]
  src/pitwall/api/jolpica.py → src/pitwall/errors.py
- `JolpicaClient` --uses--> `JolpicaHttpError`  [INFERRED]
  src/pitwall/api/jolpica.py → src/pitwall/errors.py
- `JolpicaClient` --uses--> `JolpicaNetworkError`  [INFERRED]
  src/pitwall/api/jolpica.py → src/pitwall/errors.py
- `JolpicaClient` --uses--> `RateLimitedError`  [INFERRED]
  src/pitwall/api/jolpica.py → src/pitwall/errors.py
- `JolpicaClient` --uses--> `Constructor`  [INFERRED]
  src/pitwall/api/jolpica.py → src/pitwall/models.py

## Import Cycles
- 1-file cycle: `src/pitwall/config.py -> src/pitwall/config.py`
- 1-file cycle: `src/pitwall/openf1/models.py -> src/pitwall/openf1/models.py`
- 1-file cycle: `src/pitwall/openf1/live.py -> src/pitwall/openf1/live.py`
- 1-file cycle: `src/pitwall/openf1/location.py -> src/pitwall/openf1/location.py`
- 1-file cycle: `src/pitwall/openf1/replay.py -> src/pitwall/openf1/replay.py`

## Communities (30 total, 7 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (95): Verify that the retrieved list of records covers the total count in the envelope, Fetch the schedule of races for the specified season.          Invariant: Retrie, Fetch the driver standings for the specified season.          Invariant: Retriev, Fetch the constructor standings for the specified season.          Invariant: Re, Fetch race results for a specific season and round.          Invariant: Retrieva, Fetch the list of drivers registered for the specified season.          Invarian, Fetch the list of constructors registered for the specified season.          Inv, Perform a GET request to the given URL, handling rate limits and exceptions. (+87 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (57): JolpicaClient, Async client for the Jolpica-F1 API., Close the underlying HTTP client session., AppConfig, Helper to execute the read-through logic for caching and staleness.          Fai, Fetch the schedule of races for the season (scope schedule:season)., Fetch driver standings for the season (scope driver_standings:season)., Fetch constructor standings for the season (scope constructor_standings:season). (+49 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (59): Decision, Decision, GamePrompt, Strategy-game plan model (SPEC-12 D1): frozen, loudly validated., StrategyPlan, actual_outcome(), ActualOutcome, advance() (+51 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (45): LocationFeed, MapProjection, Screen, PitwallScreen, Base screen composing the chassis around a subclass-provided body., The owning app, typed: every screen seam (config/store/clock/...) resolves., Body hook — placeholders keep the SPEC-02 contract Static., fold_events() (+37 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (16): Exception, OpenF1DataError, OpenF1Error, OpenF1HttpError, OpenF1NetworkError, OpenF1RateLimitedError, Exception raised for non-200 HTTP responses from the OpenF1 API., Exception raised when the client is rate-limited (HTTP 429) after retries are ex (+8 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (46): coerce_float(), coerce_optional_int(), coerce_position(), coerce_required_string(), _parse_circuit(), _parse_constructor(), _parse_constructor_standing(), parse_constructor_standings() (+38 more)

### Community 6 - "Community 6"
Cohesion: 0.10
Nodes (45): _gap_value(), get_required(), IntervalPoint, Lap, LocationPoint, _openf1_parse_boundary(), _optional_float(), _optional_string() (+37 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (28): RuntimeError, format_points(), Shared cell formatting primitives., Wrap string cells in rich Text so API data never parses as markup (SEC-1)., Locale-free championship points: whole floats drop the trailing .0.      >>> for, safe_row(), build_result_rows(), build_round_rows() (+20 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (18): Lap, build_query(), OpenF1Client, Fetch stints for a session., Fetch laps for a session., Fetch pit stops for a session., Fetch race control messages for a session., Fetch sessions matching the session key. (+10 more)

### Community 9 - "Community 9"
Cohesion: 0.15
Nodes (21): build_tower_rows(), build_view_rows(), driver_styles(), filter_markers(), format_interval(), format_lap_time(), Build view rows filtered by position bounds, Drv cell styled as rich.text.Text., Filter markers to only include those admitted by the view. (+13 more)

### Community 10 - "Community 10"
Cohesion: 0.17
Nodes (8): build_constructor_rows(), build_driver_rows(), ProfilesScreen, Exception raised when the store is not initialized on the app., Screen for displaying driver and constructor profiles (D1)., StoreNotInitializedError, Constructor, Driver

### Community 11 - "Community 11"
Cohesion: 0.18
Nodes (11): LiveSource, Wrap request in exception containment and record failures., Fetch drivers wholesale on first tick., Fetch stints wholesale on STINTS_REFRESH_TICKS interval., Poll one cursor-windowed stream and dedupe into ReplayEvents.          The four, Poll laps and synthesize lap_started and lap_completed events., Poll and store locations in outline buffer and latest marker mapping., Fetch events across all stream endpoints and compile a sorted list. (+3 more)

### Community 12 - "Community 12"
Cohesion: 0.19
Nodes (11): Namespace, build_app(), main(), parse_args(), Construct and configure the PitwallApp instance.      The app import is lazy so, Run the command line interface., Parse command-line arguments for the pitwall application.      Raises:         S, default_season() (+3 more)

### Community 13 - "Community 13"
Cohesion: 0.28
Nodes (12): Determine the status of the session window based on current time., session_window(), ReplayEvent, ReplayTick, TickSource, Protocol, ReplayTick, Any (+4 more)

### Community 14 - "Community 14"
Cohesion: 0.19
Nodes (11): build_rows(), _format_session(), next_race_index(), Real schedule screen: season calendar DataTable (SPEC-03 scope 3)., Pure row builder; defensively sorted by round (D3)., First round whose race start is >= now; None when the season is over (D4)., Season calendar view driven by the app's watchable load state (D1)., ScheduleScreen (+3 more)

### Community 15 - "Community 15"
Cohesion: 0.23
Nodes (10): load_location(), load_location_all(), LocationFeed, Load and parse location points from location.json in the directory., Load and parse location points from location_all.json if present, falling back t, Monotonic feed over timestamp-sorted location points., Advance cursor to playhead, returning latest LocationPoint per driver., datetime (+2 more)

### Community 16 - "Community 16"
Cohesion: 0.67
Nodes (3): is_stale(), Determine cache staleness based on calendar-keyed events and fallback age., datetime

## Knowledge Gaps
- **12 isolated node(s):** `AsyncBaseTransport`, `SessionDriver`, `Stint`, `Lap`, `PositionUpdate` (+7 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DataParseError` connect `Community 4` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.438) - this node is a cross-community bridge._
- **Why does `PitwallScreen` connect `Community 3` to `Community 1`, `Community 2`, `Community 7`, `Community 10`, `Community 12`, `Community 14`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Why does `StrategyScreen` connect `Community 2` to `Community 3`, `Community 4`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 52 inferred relationships involving `DataParseError` (e.g. with `JolpicaClient` and `LocationFeed`) actually correct?**
  _`DataParseError` has 52 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `PitwallScreen` (e.g. with `LocationFeed` and `MapProjection`) actually correct?**
  _`PitwallScreen` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `SeasonSnapshot` (e.g. with `AppConfig` and `PitwallApp`) actually correct?**
  _`SeasonSnapshot` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `JolpicaClient` (e.g. with `DataParseError` and `JolpicaHttpError`) actually correct?**
  _`JolpicaClient` has 26 INFERRED edges - model-reasoned connections that need verification._