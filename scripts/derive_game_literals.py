#!/usr/bin/env python3
# ruff: noqa: C901, B007  (verification script: enumerated checks + asserts are the design)
"""Derive strategy-game literals from the committed excerpt — STDLIB-ONLY.

F11-clean by construction (SPEC-12 D9.4): every value below is DERIVED from
fixture JSON plus the D3 scoring constants; the EXPECTED table is a separate
copy of the SPEC literals, never fed into the derivation.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXCERPT_DIR = REPO_ROOT / "tests/fixtures/openf1/1285_11291_excerpt"

# D3 constants (mirrors of the spec, used by the derivation).
COMPOUND_MATCH = 10
STINT_PENALTY = 5
PIT_EXACT = 10
PIT_CLOSE = 5
DECISION_MATCH = 5
DECISION_MISS = 5
CLASS_EXACT = 10
CLASS_CLOSE = 5
PIT_TOLERANCE = 1

# EXPECTED literals (SPEC AC-4/5/6 verbatim) — comparison side only.
EXPECTED = {
    "outcome": (("INTERMEDIATE", "MEDIUM", "MEDIUM"), (1, 14), (15,), 14),
    "plan_a_breakdown": (30, 20, 0, 5, 55),
    "plan_b_breakdown": (5, 0, 5, 10, 20),
    "tick_count": 6,
    "final_playhead": "20:32:30",
    "window_prompt_tick": 0,
    "pit_event_tick": 1,
    "plan_summary": "Plan — NOR · MEDIUM → MEDIUM · pit 16 · P14",
    "panel_a": (
        "Final score: 55",
        "Tyres: +30 (planned INTERMEDIATE, MEDIUM, MEDIUM · actual INTERMEDIATE, MEDIUM, MEDIUM)",
        "Pit laps: +20 (planned 1, 14 · actual 1, 14)",
        "Decisions: 0 (0 of 0 matched)",
        "Finish: +5 (predicted P12 · actual P14)",
    ),
    "panel_b": (
        "Final score: 20",
        "Tyres: +5 (planned MEDIUM, MEDIUM · actual INTERMEDIATE, MEDIUM, MEDIUM)",
        "Pit laps: 0 (planned 16 · actual 1, 14)",
        "Decisions: +5 (1 of 1 matched)",
        "Finish: +10 (predicted P14 · actual P14)",
    ),
    "tick0_status_ts": "20:30:00",
    "tick1_status_ts": "20:30:30",
}

PLAN_A = {"compounds": ("INTERMEDIATE", "MEDIUM", "MEDIUM"), "pit_laps": (1, 14), "predicted": 12}
PLAN_B = {"compounds": ("MEDIUM", "MEDIUM"), "pit_laps": (16,), "predicted": 14}


def _load(name: str) -> list | dict:
    return json.loads((EXCERPT_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _parse_ts(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def derive_outcome(driver: int) -> tuple:
    stints = sorted(
        (s for s in _load("stints") if s.get("driver_number") == driver),
        key=lambda s: s["stint_number"],
    )
    compounds = tuple(s.get("compound") or "?" for s in stints)
    boundary = tuple(s["lap_end"] for s in stints[:-1])
    pits = tuple(
        p["lap_number"] for p in _load("pit") if p.get("driver_number") == driver and p.get("lap_number") is not None
    )
    positions = [
        (
            _parse_ts(p["date"]),
            p["position"],
        )
        for p in _load("position")
        if p.get("driver_number") == driver
    ]
    final = max(positions)[1] if positions else None
    return compounds, boundary, pits, final


def score(plan: dict, outcome: tuple, decisions: tuple, prompts_total: int) -> tuple:
    compounds, boundary, pits, final = outcome
    tyres = sum(
        COMPOUND_MATCH
        for i in range(min(len(plan["compounds"]), len(compounds)))
        if plan["compounds"][i] == compounds[i]
    ) - STINT_PENALTY * abs(len(plan["compounds"]) - len(compounds))
    pit_pts = 0
    for a, b in zip(plan["pit_laps"], boundary, strict=False):
        delta = abs(a - b)
        pit_pts += PIT_EXACT if delta == 0 else (PIT_CLOSE if delta == 1 else 0)
    dec_pts = 0
    for planned, choice in decisions:
        pitted = any(abs(e - planned) <= PIT_TOLERANCE for e in pits)
        dec_pts += DECISION_MATCH if (choice == "pit") == pitted else -DECISION_MISS
    if final is None:
        finish = 0
    else:
        d = abs(plan["predicted"] - final)
        finish = CLASS_EXACT if d == 0 else (CLASS_CLOSE if d <= 2 else 0)
    return tyres, pit_pts, dec_pts, finish, tyres + pit_pts + dec_pts + finish


def derive_ticks() -> tuple[int, str, int | None, int | None]:
    """Tick count/final playhead from the replay window; prompt ticks for PLAN_B."""
    manifest = _load("manifest")
    t0 = _parse_ts(manifest["replay_window"]["start"])
    span = timedelta(seconds=30)  # speed 60 x interval 0.5

    events: list[tuple[datetime, str, int | None]] = []
    for lap in _load("laps"):
        if lap.get("date_start") is not None:
            events.append((_parse_ts(lap["date_start"]), "lap_started", lap.get("lap_number")))
    for pit in _load("pit"):
        if pit.get("date") is not None and pit.get("driver_number") == 1:
            events.append((_parse_ts(pit["date"]), "pit", pit.get("lap_number")))
    for stream, kind in (("position", "x"), ("intervals", "x"), ("race_control", "x")):
        for r in _load(stream):
            if r.get("date") is not None:
                events.append((_parse_ts(r["date"]), kind, None))
    for lap in _load("laps"):
        if lap.get("date_start") is not None and lap.get("lap_duration") is not None:
            events.append((_parse_ts(lap["date_start"]) + timedelta(seconds=lap["lap_duration"]), "x", None))

    def tick_of(ts: datetime) -> int:
        if ts <= t0:
            return 0
        offset = (ts - t0).total_seconds()
        return int(-(-offset // 30))

    last = max(ts for ts, _, _ in events)
    tick_count = tick_of(last) + 1
    final_playhead = (t0 + (tick_count - 1) * span).strftime("%H:%M:%S")

    window_tick = None
    for ts, kind, lap in sorted(events):
        if kind == "lap_started" and lap in (15, 16):
            window_tick = tick_of(ts)
            break
    pit_tick = None
    for ts, kind, lap in sorted(events):
        if kind == "pit":
            pit_tick = tick_of(ts)
            break
    return tick_count, final_playhead, window_tick, pit_tick


def _signed(n: int) -> str:
    return f"{n:+d}" if n else "0"


def _seq(values: tuple) -> str:
    return ", ".join(str(v) for v in values) if values else "—"


def render_panel(plan: dict, outcome: tuple, breakdown: tuple, matched: int, prompts_total: int) -> tuple:
    """Reimplements the D4 five-line panel from raw values (no pitwall imports)."""
    tyres, pit_pts, dec_pts, finish, total = breakdown
    compounds, boundary, _pits, final = outcome
    finish_actual = f"actual P{final}" if final is not None else "no classification observed"
    return (
        f"Final score: {total}",
        f"Tyres: {_signed(tyres)} (planned {_seq(plan['compounds'])} · actual {_seq(compounds)})",
        f"Pit laps: {_signed(pit_pts)} (planned {_seq(plan['pit_laps'])} · actual {_seq(boundary)})",
        f"Decisions: {_signed(dec_pts)} ({matched} of {prompts_total} matched)",
        f"Finish: {_signed(finish)} (predicted P{plan['predicted']} · {finish_actual})",
    )


def derive_acronym(driver: int) -> str:
    for d in _load("drivers"):
        if d.get("driver_number") == driver:
            return d["name_acronym"]
    return "?"


def main() -> None:
    outcome = derive_outcome(1)
    print("--- AC-4 actual outcome (driver 1) ---")
    print(f"  compounds: {outcome[0]}")
    print(f"  boundary pit laps: {outcome[1]}")
    print(f"  pit event laps: {outcome[2]}")
    print(f"  final position: {outcome[3]}")
    print()

    plan_a = score(PLAN_A, outcome, (), 0)
    plan_b = score(PLAN_B, outcome, ((16, "pit"),), 1)
    print("--- AC-5 breakdowns (tyres, pit, decisions, finish, total) ---")
    print(f"  PLAN_A: {plan_a}")
    print(f"  PLAN_B: {plan_b}")
    print()

    tick_count, final_playhead, window_tick, pit_tick = derive_ticks()
    print("--- Tick mapping (speed 60, interval 0.5) ---")
    print(f"  ticks: {tick_count}; final playhead: {final_playhead} UTC")
    print(f"  window prompt tick: {window_tick}; pit event tick: {pit_tick}")
    print()

    acronym = derive_acronym(1)
    summary = (
        f"Plan — {acronym} · {' → '.join(PLAN_B['compounds'])} · "
        f"pit {', '.join(str(lap) for lap in PLAN_B['pit_laps'])} · P{PLAN_B['predicted']}"
    )
    print("--- Plan summary ---")
    print(f"  {summary}")
    print()

    panel_a = render_panel(PLAN_A, outcome, plan_a, 0, 0)
    panel_b = render_panel(PLAN_B, outcome, plan_b, 1, 1)
    print("--- AC-6 score panels (derived) ---")
    for line in panel_a:
        print(f"  A| {line}")
    for line in panel_b:
        print(f"  B| {line}")
    print()

    manifest = _load("manifest")
    t0 = _parse_ts(manifest["replay_window"]["start"])
    tick0_ts = t0.strftime("%H:%M:%S")
    tick1_ts = (t0 + timedelta(seconds=30)).strftime("%H:%M:%S")
    print("--- AC-9 tick status timestamps ---")
    print(f"  tick 0: {tick0_ts}; tick 1: {tick1_ts}")
    print()

    print("--- Verification Verdict ---")
    checks = [
        ("AC-6 panel A", panel_a == EXPECTED["panel_a"]),
        ("AC-6 panel B", panel_b == EXPECTED["panel_b"]),
        ("tick-0 status ts", tick0_ts == EXPECTED["tick0_status_ts"]),
        ("tick-1 status ts", tick1_ts == EXPECTED["tick1_status_ts"]),
        ("AC-4 outcome", outcome == EXPECTED["outcome"]),
        ("PLAN_A breakdown", plan_a == EXPECTED["plan_a_breakdown"]),
        ("PLAN_B breakdown", plan_b == EXPECTED["plan_b_breakdown"]),
        ("tick count", tick_count == EXPECTED["tick_count"]),
        ("final playhead", final_playhead == EXPECTED["final_playhead"]),
        ("window prompt tick", window_tick == EXPECTED["window_prompt_tick"]),
        ("pit event tick", pit_tick == EXPECTED["pit_event_tick"]),
        ("plan summary", summary == EXPECTED["plan_summary"]),
    ]
    ok = True
    for label, passed in checks:
        print(f"  [{'OK' if passed else 'FAIL'}] {label}")
        ok = ok and passed
    print(f"MATCH VERDICT: {'SUCCESS' if ok else 'FAILED'}")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
