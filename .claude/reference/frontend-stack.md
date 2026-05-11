# Frontend Stack

**Pitwall is a TUI, not a web app. The Clief Resource Index §2.5 (Frontend, UI, and Design) defaults — shadcn/ui, Tailwind, Lucide, Recharts — do not apply to this project.** This file overrides them.

If a future iteration of this project adds a web frontend (e.g., a settings panel, a public results browser), the original Clief defaults below the line below are the place to start.

---

## TUI stack (in use)

### Framework

[Textual](https://textual.textualize.io/) ≥ 3.0 — async-first Python TUI framework. Same framework as the `faceoff` project this scaffold draws on. Owns the event loop, screen routing, widget rendering.

### Rendering primitives

[Rich](https://rich.readthedocs.io/) — automatically pulled in by Textual. Use Rich `Text`, `Table`, `Panel`, `Tree` for content rendering inside custom widgets. Do not bypass Rich for ANSI escape codes; let it handle terminal differences.

### Widgets

- Built-in Textual widgets (`DataTable`, `Tabs`, `Footer`, `Header`, `Input`, `ListView`, `Static`, `RichLog`) for stock UI.
- Custom widgets in `src/pitwall/widgets/` for project-specific renders: `TimingRow`, `TrackMapCanvas`, `TyreStintBar`, `PitWindowPrompt`.

### Styling

Textual CSS (`.tcss` files) — Tailwind-like, but designed for terminal cells. Co-locate per-screen `.tcss` next to the screen it styles.

### Charts / data viz

No external chart library. For:
- Lap-time / position-over-laps plots → render as a Rich `Table` of ASCII bars, OR use Textual's `plotext` integration when added.
- Tyre stints → bespoke `TyreStintBar` widget (segments per stint, color per compound).

### Color / theming

Textual's theming system. Define a single Pitwall theme in `src/pitwall/app.py`. Tyre compounds use canonical broadcast colors:
- **Soft** — red
- **Medium** — yellow
- **Hard** — white
- **Intermediate** — green
- **Wet** — blue

### Icons

Unicode glyphs only — no icon font. Terminal compatibility matters more than visual richness. Examples in use: `▲` (driver up), `▼` (down), `●` (live), `→` (gap), `⚑` (flag).

### Layout for the track-position map

The track map is rendered cell-by-cell on a Textual canvas. Each Grand Prix has a precomputed circuit outline (a list of (x, y) points). Driver positions arriving from OpenF1 are projected onto the nearest outline cell. See `widgets/track_map_canvas.py` (planned) and `data/circuits/` (planned).

### Cross-platform terminal notes

- Assume a 256-color terminal at minimum. Truecolor preferred. Pitwall does not target legacy 16-color terminals.
- Assume Unicode support for box-drawing and tyre dots. The faceoff convention of using `▶` and `┃` is followed.
- Minimum useful terminal size: 80×24. The track map screen prefers 120×40.

---

## Web frontend (NOT in use)

If Pitwall ever ships a companion web view, the Clief defaults are the starting point. Until then, ignore this section.

<details>
<summary>Original Clief Resource Index §2.5 defaults (for reference)</summary>

- Component library: [shadcn/ui](https://github.com/shadcn-ui/ui) (React + Radix + Tailwind)
- Styling: [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss)
- Icons: [Lucide](https://github.com/lucide-icons/lucide) (`lucide-react`)
- Charts: [Recharts](https://github.com/recharts/recharts)
- Optional flair: [Acternity UI](https://ui.acternity.com), [Magic UI](https://magicui.design)
- Mockup-to-code: [v0.dev](https://v0.dev)

</details>
