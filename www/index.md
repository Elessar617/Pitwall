---
hide:
  - navigation
---

<div class="pitwall-hero" markdown>
![Pitwall — the real Suzuka Circuit telemetry trace](assets/logo.svg){ width="220" }

# Formula 1, from your terminal

**Pitwall** is an open-source TUI companion for following F1 — live timing with a
braille track-position map, a full season tracker, and a strategy mini-game you
play against the actual race.
</div>

```console
$ uvx --from git+https://github.com/Elessar617/Pitwall pitwall
```

<figure class="pitwall-shot" markdown>
![Pitwall's live timing screen: a 22-driver timing tower with team-coloured driver codes beside a large bordered braille Circuit Gilles Villeneuve track map, every car a team-coloured marker, captioned with the circuit and session time](assets/demo.svg)
<figcaption>Replay of the 2026 Canadian Grand Prix — the timing tower beside the track map, drawn live from real car telemetry.</figcaption>
</figure>

## What it does

- **Season tracker** — the full calendar with session times in UTC, drivers' and
  constructors' standings, per-round results, and team/driver profiles, served
  cache-first from the [Jolpica F1 API](https://github.com/jolpica/jolpica-f1).
- **Live timing & track map** — a timing tower and a track outline drawn from
  [OpenF1](https://openf1.org/) car telemetry, in braille characters at terminal
  resolution — every car a marker in its team colour, with battle views that
  focus the lead fight, the podium, or the points. Works live or against a
  recorded replay that ships in the repo.
- **Strategy mini-game** — commit a tyre + pit plan before lights out, answer
  pit-window prompts as the race unfolds, and get scored against what the
  driver actually did.

## Why you might like it

- **It's honest about data.** Everything renders from real public telemetry and
  timing APIs; when data lags (OpenF1 location data can trail a session), the
  app says so instead of pretending.
- **It's tested like it matters.** 351 offline-deterministic tests; every
  feature shipped through an adversarial review gate.
- **It's a terminal app.** Starts in about a second, runs over SSH, and the
  track map is drawn in braille glyphs.

[Get started](getting-started.md){ .md-button .md-button--primary }
[See the features](features/season.md){ .md-button }
