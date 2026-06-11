# Pitwall roadmap

Pitwall shipped all three planned pillars — season tracker (v0.1.0), live timing + track map (v0.2.0), and the strategy mini-game (v0.3.0) — and passed a full completion audit (security, performance, types, tests). What follows is grounded in real carried work, not a wishlist. Each item is honest about whether it will actually happen.

## Near-term (the carried ledger)

- **Live strategy game.** The mini-game currently plays over a recorded replay; live-mode play is deferred because committing a plan before lights-out conflicts with how the live session discovers and back-fills data. Worth designing properly.
- **Multi-driver live captures.** The track map already renders every car from a recorded session. A repeatable operator workflow for capturing fresh multi-driver fixtures (`scripts/capture_openf1_session.py`, now hardened to fail loudly and never write a misleading fixture) keeps the demo current across the season.
- **First real live-session validation.** The live path is verified against mocked transports; a checklist run during an actual session is the remaining real-world proof.
- **"Gap to car ahead" in battle views.** The data is already in the tower; surfacing it inside the filtered lead/podium/points views is a small, high-value addition.

## Mid-term (if the project keeps growing)

- **Per-stint tyre degradation and undercut/overcut hints** in the strategy game — the original v2 idea, dependent on a degradation data source.
- **Sector colors and mini-sector timing** in the live tower, if OpenF1 exposes them reliably.
- **Configurable theming** beyond the built-in team colors.
- **World Endurance Championship (WEC) expansion** once the F1 core stays stable: identify reliable WEC data sources, model multi-class endurance sessions cleanly, and keep F1 as the reference implementation instead of generalizing prematurely.
- **PyPI release** so `uvx pitwall` works without the `--from git+…` form.

## Won't fix (with reasons)

- **Responsive layout below 80×24.** Pitwall targets a standard terminal; the fixed split is a deliberate design point, not a gap.
- **Sub-second live parity with official feeds.** OpenF1's public data legitimately lags; Pitwall is honest about that rather than faking freshness.
- **Mobile/GUI port.** It's a terminal app on purpose.

## Engineering follow-ups (from the 2026-06-10 completion audit)

The audit confirmed and **closed** the security (terminal markup injection), performance (a leaked ~20 MiB buffer), and type-gate (the type checker was silently skipping all production code) findings. Remaining low-priority, non-user-facing items: relocating the OpenF1 parse-error class into its own taxonomy module (currently bridged), a test harness for the subprocess-only capture script, and the long-noted optional split of the cache module if persistent storage is ever added.
