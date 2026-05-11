# Pitwall

<p align="center">
  <em>An open-source terminal companion for following Formula 1, from a fan's pit wall.</em>
</p>

A terminal user interface (TUI) for live F1 sessions, season tracking, and a strategy mini-game played alongside an in-progress race. Inspired by [F1 MultiViewer](https://multiviewer.app/), [Golden Lap](https://store.steampowered.com/app/2261910/), and the excellent [`faceoff`](https://github.com/vgreg/faceoff) (NHL TUI), which lives at `faceoff/` in this repo as a structural reference.

## Features (planned for v1)

- **Live session view** for FP1 / FP2 / FP3 / Qualifying / Sprint Qualifying / Sprint / Race
  - Leaderboard-style live timing tower (gap, last lap, sector colors, tyre, age, pit count)
  - Real-time **track-position map** rendering every driver's location on the circuit
  - Race control messages, weather, flag state
- **Season tracker**
  - Schedule with next-session countdown in your local timezone
  - Drivers' and Constructors' standings
  - Driver and constructor profiles (career stats + season-to-date)
  - Race results history
- **Strategy mini-game**
  - Commit a tyre + pit-lap plan for any driver before lights out
  - Live pit-window prompts during the race (`pit now` / `stay out` / `wait one`)
  - End-of-race player-vs-actual delta score
- **v2 (planned):** full live strategist — safety-car reactions, weather changes, undercut/overcut logic.

## Installation

Pitwall is not yet on PyPI. Install from source for now:

```bash
git clone https://github.com/<you>/pitwall.git
cd pitwall
uv sync
uv run pitwall
```

Once published:

```bash
uvx pitwall                  # run without installing
uv tool install pitwall      # install as a tool, then `pitwall`
```

## Development

```bash
uv sync                  # install all dev deps (incl. dev group)
uv run pytest            # tests (incl. doctests)
uv run ruff check .      # lint
uv run ruff format .     # format
uv run ty check          # type check
uv build                 # produce wheel + sdist
```

See [`START-HERE.md`](START-HERE.md) for contributor onboarding and the layout of the four-workspace agent-native development scaffold this repo uses.

## Data sources

Pitwall relies only on publicly available F1 data:

- [**OpenF1**](https://openf1.org/) — REST + WebSocket relay of the F1 live timing feed. Driver positions for the track map.
- [**Jolpica-F1**](https://github.com/jolpica/jolpica-f1) — direct successor to the Ergast API. Schedule, standings, results, history.
- [**FastF1**](https://github.com/theOehrly/Fast-F1) — telemetry + tyre data; powers the strategy sim's degradation curves.

## Acknowledgments

- Structurally inspired by [`faceoff`](https://github.com/vgreg/faceoff) (NHL TUI) — same Python + Textual stack, same async-worker pattern. A read-only copy lives at `faceoff/` for ongoing reference.
- Spiritual nods to [F1 MultiViewer](https://multiviewer.app/) for live timing UX, and [Golden Lap](https://store.steampowered.com/app/2261910/) for the strategy-sim feel.
- Built on the **workspace-blueprint** agent-native scaffold. See [`docs/teaching/`](docs/teaching/) for the scaffold story; [`docs/teaching/bootstrap.md`](docs/teaching/bootstrap.md) for how to use it for a new project.

## Disclaimer

This project is not affiliated with, endorsed by, or in any way officially connected with Formula 1, the FIA, FOM, any Formula 1 team, or any of their affiliates. All Formula 1 names, logos, and trademarks are the property of their respective owners.

Pitwall uses publicly available F1 data for informational and educational purposes only.

## License

MIT — see `LICENSE` (shipping with the `v0.1.0` release).
