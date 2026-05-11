# Glossary

Domain-specific terms agents need to use correctly when planning, implementing, or reviewing Pitwall changes. Sorted alphabetically within each group.

## Formula 1 terms

- **Apex** — geometric inside of a corner; the line a driver tries to clip.
- **Blue flag** — waved at a backmarker about to be lapped; must yield within three corners.
- **Box / boxes** — radio call for "pit this lap." "Box, box, box" = confirmed instruction.
- **Chequered flag** — race / session finish.
- **Compound** — Pirelli tyre type for the weekend. Three slick compounds (`Soft`, `Medium`, `Hard`) plus `Intermediate` and `Wet`. The slick set is selected per-event from Pirelli's `C1`-`C5` family (C1 = hardest, C5 = softest).
- **Constructor** — the team (e.g., Red Bull Racing, Ferrari). The Constructors' Championship runs in parallel to the Drivers' Championship.
- **Delta** — time difference. Used both for gap-to-leader and for predicted vs actual outcomes in the sim.
- **DRS** (Drag Reduction System) — moveable rear-wing flap; opens within a marked DRS zone if you're within 1.0 s of the car ahead at the detection line. Not available in the first two race laps or under yellow/red flag conditions.
- **FP1 / FP2 / FP3** — three free-practice sessions on a standard race weekend. Approximately one hour each. Sprint weekends replace FP2 and FP3 with the sprint format.
- **FIA** — governing body (Fédération Internationale de l'Automobile).
- **FOM** — Formula One Management; the commercial rights holder.
- **Formation lap** — sighting lap before the race start; cars line up on the grid afterwards.
- **Fastest lap (FL)** — fastest valid race lap. 1 championship point if the driver finishes in the top 10 (current rules).
- **Free practice** — non-competitive session before qualifying. Three on a standard weekend, one on a sprint weekend.
- **In-lap / out-lap** — the lap entering the pits (worn tyres, slow) / the lap leaving the pits (cold tyres, slow).
- **Parc fermé** — period from the end of qualifying to the race start during which the car setup is locked. Setup changes incur a pit-lane start.
- **Pit lane** — the road parallel to the start/finish straight where pit stops happen. Speed-limited (typically 80 km/h).
- **Pit window** — the lap range during which a stop is strategically optimal.
- **Pole position** — front of the grid, inside line. Awarded to the fastest Q3 driver.
- **Podium** — top three finishers.
- **Quali (Q1 / Q2 / Q3)** — three-stage knockout qualifying. Q1 (18 min, 5 eliminated), Q2 (15 min, 5 eliminated), Q3 (12 min, top 10 fight for pole).
- **Safety Car (SC)** — full-course neutralization with a physical safety car leading the pack at ~80 % pace. Bunches the field; opens cheap pit windows.
- **Sprint** — short race (~100 km) on sprint weekends. Points awarded top 8 (`8,7,6,5,4,3,2,1`). Separate from main race.
- **Sprint Qualifying (SQ1 / SQ2 / SQ3)** — sprint-weekend shootout; sets the sprint grid only. Main race grid is still set by main qualifying.
- **Tyre age** — number of laps a set of tyres has run, including the out-lap.
- **Undercut** — pitting earlier than a rival so fresh tyres let you leapfrog them on the next out-lap. Standard 2-stop tactic.
- **Overcut** — staying out longer than a rival, gaining time while they struggle on their out-lap on cold tyres.
- **VSC** (Virtual Safety Car) — full-course neutralization enforced by lap-time deltas (no bunching). Less cheap than SC for pit stops but still useful.

## Pitwall-specific terms

- **App shell** — the `Textual.App` subclass in `src/pitwall/app.py`. Owns the worker lifecycle.
- **Cache tick** — a Textual message a worker emits after writing to SQLite, telling subscribed screens part of the cache changed.
- **Live timing tower** — leaderboard-style screen showing P1-Pn with gap, last lap, sector colors, tyre, age, and pit count. See `screens/live_timing.py`.
- **Pit-window prompt** — the mid-race overlay during the open pit window for the user's plan. Offers `[P]it now`, `[S]tay out`, `[W]ait one lap`.
- **Plan** — user-committed strategy object: starting compound, planned pit lap(s), planned compound at each stop. Stored in the `plans` table.
- **Player-vs-actual score** — end-of-race scoring (0-100) comparing the player's plan outcome against the driver's actual outcome.
- **Sim delta** — predicted race-finish gap (in seconds and positions) for a given plan, computed by `sim/predict.py`.
- **Track-position map** — terminal-rendered circuit outline with each driver shown as a styled cell at their current x/y on track. See `screens/track_map.py`.
- **Tyre-deg curve** — fitted per-compound, per-track lap-time degradation model derived from historical FastF1 data; used by the sim. Stored in `data/curves/`.
- **Worker** — async background task in `src/pitwall/workers/` that fetches from an external API and writes to the cache. Screens never call the network directly.
