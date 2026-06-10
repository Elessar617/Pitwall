# Data sources & credits

## Data

- **[Jolpica F1](https://github.com/jolpica/jolpica-f1)** — season data:
  schedule, standings, results, drivers, constructors. The community successor
  to the Ergast API.
- **[OpenF1](https://openf1.org/)** — live and historical telemetry: laps,
  intervals, positions, stints, pit stops, race control, and car location.

Pitwall caches season data locally (SQLite) and polls live data at under one
request per second.

## Built with

- **[Textual](https://textual.textualize.io/)** — the Python TUI framework
  that powers every screen.
- **[faceoff](https://github.com/vgreg/faceoff)** by Vincent Grégoire — the
  NHL terminal app whose structure and spirit inspired this project.

## The logo

The mark is not a stylised squiggle — it is the **actual telemetry trace** of a
car lapping Suzuka at the 2026 Japanese Grand Prix: 1,140 location samples from
the OpenF1 API, figure-8 crossover included.

## Disclaimer

Pitwall is an unofficial, fan-made, open-source project. It is not affiliated
with, endorsed by, or associated with Formula 1, the FIA, or any team. F1 and
related marks are trademarks of their respective owners.

Source code is available under the repository license at
[github.com/Elessar617/Pitwall](https://github.com/Elessar617/Pitwall).
