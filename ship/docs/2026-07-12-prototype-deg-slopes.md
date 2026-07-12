<!-- wayfinder asset: resolves ticket #11 (Deg-slope prototype) on map #2 - resolved 2026-07-12 -->

## Tyre-deg slope fit - session 1285/11291

Verdict: **noise-dominated** - ordering=VIOLATED (SOFT:-0.049 > MEDIUM:+0.005 > HARD:+0.002); min |slope|/stderr ratio=0.21

Stints fit: 45 of 56 | laps kept: 850 | dropped: null=1, pit-out=34, in-lap=33, SC/VSC/yellow=187, outlier=90 | neutralization windows: 12

### Per-compound aggregate (s/lap; fuel-adj = raw + 0.05 assumed fuel gain)

| compound | stints | median raw | median fuel-adj | IQR (raw) | share>0 (adj) | median stderr |
|---|---|---|---|---|---|---|
| SOFT | 21 | -0.0988 | -0.0488 | [-0.3476, -0.0585] | 19% | 0.0534 |
| MEDIUM | 22 | -0.0449 | +0.0051 | [-0.1295, -0.0324] | 59% | 0.0196 |
| HARD | 2 | -0.0476 | +0.0024 | [-0.0504, -0.0449] | 50% | 0.0113 |

### Compound deltas (fuel-free: the fuel term cancels between compounds)

- SOFT - MEDIUM: -0.0539 s/lap
- MEDIUM - HARD: +0.0027 s/lap

### Per-stint fits

| driver | stint | compound | n | age0 | slope raw | slope adj | stderr | ratio |
|---|---|---|---|---|---|---|---|---|
| 1 | 2 | MEDIUM | 8 | 0 | -0.4322 | -0.3822 | 0.1300 | 3.3 |
| 1 | 3 | MEDIUM | 17 | 3 | -0.0415 | +0.0085 | 0.0335 | 1.2 |
| 3 | 1 | SOFT | 23 | 5 | -0.0863 | -0.0363 | 0.0203 | 4.3 |
| 3 | 2 | MEDIUM | 29 | 0 | -0.0387 | +0.0113 | 0.0069 | 5.6 |
| 5 | 2 | SOFT | 10 | 0 | -0.2102 | -0.1602 | 0.0554 | 3.8 |
| 5 | 3 | MEDIUM | 35 | 0 | -0.0289 | +0.0211 | 0.0071 | 4.1 |
| 6 | 1 | SOFT | 23 | 4 | -0.0945 | -0.0445 | 0.0186 | 5.1 |
| 6 | 2 | MEDIUM | 15 | 0 | -0.0449 | +0.0051 | 0.0293 | 1.5 |
| 6 | 3 | SOFT | 7 | 4 | -0.3476 | -0.2976 | 0.1354 | 2.6 |
| 10 | 1 | MEDIUM | 21 | 0 | -0.1330 | -0.0830 | 0.0176 | 7.6 |
| 10 | 2 | HARD | 28 | 0 | -0.0532 | -0.0032 | 0.0126 | 4.2 |
| 11 | 2 | SOFT | 8 | 0 | -0.3483 | -0.2983 | 0.1063 | 3.3 |
| 11 | 3 | MEDIUM | 10 | 0 | -0.1188 | -0.0688 | 0.0524 | 2.3 |
| 11 | 4 | SOFT | 6 | 0 | -0.6921 | -0.6421 | 0.2774 | 2.5 |
| 12 | 1 | SOFT | 23 | 4 | -0.0585 | -0.0085 | 0.0201 | 2.9 |
| 12 | 2 | MEDIUM | 29 | 0 | -0.0337 | +0.0163 | 0.0065 | 5.2 |
| 14 | 1 | SOFT | 12 | 0 | -0.1343 | -0.0843 | 0.0589 | 2.3 |
| 16 | 1 | SOFT | 23 | 4 | -0.0988 | -0.0488 | 0.0185 | 5.3 |
| 16 | 2 | MEDIUM | 29 | 0 | +0.0234 | +0.0734 | 0.0102 | 2.3 |
| 18 | 1 | SOFT | 10 | 0 | -0.4429 | -0.3929 | 0.1298 | 3.4 |
| 18 | 2 | SOFT | 22 | 0 | -0.0162 | +0.0338 | 0.0267 | 0.6 |
| 18 | 3 | MEDIUM | 10 | 0 | -0.0972 | -0.0472 | 0.0531 | 1.8 |
| 23 | 1 | SOFT | 10 | 0 | -0.7627 | -0.7127 | 0.1399 | 5.5 |
| 27 | 2 | SOFT | 10 | 4 | -0.2183 | -0.1683 | 0.0876 | 2.5 |
| 27 | 3 | MEDIUM | 33 | 0 | -0.0273 | +0.0227 | 0.0058 | 4.7 |
| 30 | 1 | MEDIUM | 21 | 0 | -0.1335 | -0.0835 | 0.0216 | 6.2 |
| 30 | 2 | SOFT | 27 | 0 | -0.0489 | +0.0011 | 0.0097 | 5.0 |
| 31 | 1 | SOFT | 10 | 0 | -0.5781 | -0.5281 | 0.1632 | 3.5 |
| 31 | 2 | MEDIUM | 10 | 0 | -0.0349 | +0.0151 | 0.0402 | 0.9 |
| 31 | 3 | SOFT | 27 | 0 | -0.0544 | -0.0044 | 0.0138 | 3.9 |
| 43 | 1 | MEDIUM | 20 | 0 | -0.1423 | -0.0923 | 0.0221 | 6.4 |
| 43 | 2 | HARD | 28 | 0 | -0.0421 | +0.0079 | 0.0100 | 4.2 |
| 44 | 1 | SOFT | 23 | 3 | -0.0886 | -0.0386 | 0.0219 | 4.0 |
| 44 | 2 | MEDIUM | 29 | 0 | -0.0253 | +0.0247 | 0.0054 | 4.7 |
| 55 | 2 | MEDIUM | 19 | 8 | -0.0752 | -0.0252 | 0.0169 | 4.4 |
| 55 | 3 | MEDIUM | 29 | 0 | -0.0483 | +0.0017 | 0.0135 | 3.6 |
| 63 | 1 | SOFT | 23 | 3 | -0.0806 | -0.0306 | 0.0262 | 3.1 |
| 77 | 3 | MEDIUM | 12 | 0 | +0.0205 | +0.0705 | 0.0887 | 0.2 |
| 77 | 4 | SOFT | 13 | 0 | +0.0713 | +0.1213 | 0.0535 | 1.3 |
| 77 | 5 | MEDIUM | 12 | 0 | -0.3501 | -0.3001 | 0.0595 | 5.9 |
| 81 | 2 | MEDIUM | 8 | 0 | -0.5659 | -0.5159 | 0.1450 | 3.9 |
| 81 | 3 | MEDIUM | 26 | 0 | -0.0320 | +0.0180 | 0.0098 | 3.3 |
| 81 | 4 | SOFT | 11 | 4 | -0.0406 | +0.0094 | 0.0534 | 0.8 |
| 87 | 1 | SOFT | 21 | 5 | -0.1771 | -0.1271 | 0.0245 | 7.2 |
| 87 | 2 | MEDIUM | 30 | 0 | -0.0449 | +0.0051 | 0.0110 | 4.1 |

## Resolution

Verdict **noise-dominated** accepted; thread continues as **prototype v2** with a session-time
(track-evolution) regressor, cross-stint/driver pooling, and a HIGH-deg venue fixture (requires a
fresh multi-driver capture). If v2 also fails, deg hints are dropped with two honest datapoints.

## Appendix — reproduction script (stdlib only)

Run: `python3 deg_fit.py <repo>/data/fixtures/1285_11291` — deterministic, byte-identical output.

```python
#!/usr/bin/env python3
"""Wayfinder #11 prototype: per-driver per-compound tyre-degradation slopes.

Fits ordinary least squares (closed form, stdlib only) of
lap_duration ~ tyre_age per (driver, stint), then aggregates per compound.

Usage: python3 deg_fit.py <fixture_dir>   # dir with laps.json, stints.json, race_control.json

Deterministic: no randomness, stable sort orders, pure stdlib (Python 3.13).
Writes results.json and results.md next to this script and prints the markdown.

Exclusion rules:
  E1  lap_duration null/missing              -> dropped
  E2  is_pit_out_lap == true                 -> dropped (out-lap)
  E3  last lap of a stint that is followed by another stint for the same
      driver (stint ended in a pit stop)     -> dropped (in-lap)
  E4  lap interval [date_start, date_start + lap_duration) overlaps a
      neutralization window derived from race_control.json:
        - category "SafetyCar": message containing "DEPLOYED" opens a window;
          closed by the first later Flag/CLEAR with scope "Track"
          ("TRACK CLEAR") within 60s of the "ENDING" message, else at ENDING.
        - category "Flag", flag YELLOW / DOUBLE YELLOW with a sector: opens a
          per-sector window closed by the next CLEAR for that sector
          (a Track-scope CLEAR closes all open sector windows).
        - category "Flag", flag RED: track window closed by the next GREEN.
      BLUE and CHEQUERED flags are NOT excluded (blue flags are routine
      traffic notices; excluding them would delete half the race).
  E5  outliers: after a first OLS pass per stint, laps whose |residual|
      exceeds max(1.5 s, P90 of the stint's |residuals|) are dropped and the
      stint refit once (traffic / errors not captured by flags).

Fits require >= 5 clean laps (MIN_LAPS).

Fuel collinearity: within one stint tyre age and fuel load are perfectly
collinear, so a per-stint fit CANNOT separate tyre deg from fuel burn-off.
We report raw slopes AND fuel-adjusted slopes = raw + FUEL_GAIN_S_PER_LAP
(assumed 0.05 s/lap gained per lap of fuel burned; the car gets faster, so
the observed slope understates true tyre deg by that amount). Only the
compound-to-compound DELTAS are fuel-free (the fuel term cancels).
"""

import json
import math
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

MIN_LAPS = 5
FUEL_GAIN_S_PER_LAP = 0.05  # assumed lap-time gain per lap from fuel burn
OUTLIER_FLOOR_S = 1.5  # never drop residuals smaller than this (E5)
COMPOUND_ORDER = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]


def parse_ts(s):
    return datetime.fromisoformat(s)


def load(fixture_dir):
    d = Path(fixture_dir)
    laps = json.loads((d / "laps.json").read_text())
    stints = json.loads((d / "stints.json").read_text())
    rc = json.loads((d / "race_control.json").read_text())
    return laps, stints, rc


def neutralization_windows(rc):
    """Derive [start, end) datetime windows per exclusion rule E4."""
    events = sorted(rc, key=lambda r: r["date"])
    windows = []  # (start, end, label)
    open_sectors = {}  # sector -> start
    sc_open = None
    red_open = None
    for ev in events:
        t = parse_ts(ev["date"])
        cat, flag, scope, sector = ev["category"], ev["flag"], ev["scope"], ev["sector"]
        msg = (ev.get("message") or "").upper()
        if cat == "SafetyCar":
            if "DEPLOYED" in msg and sc_open is None:
                sc_open = t
            elif sc_open is not None and ("ENDING" in msg or "IN THIS LAP" in msg):
                windows.append((sc_open, t, "SC/VSC"))  # may be extended by TRACK CLEAR
                sc_open = None
        elif cat == "Flag":
            if flag in ("YELLOW", "DOUBLE YELLOW") and sector is not None:
                open_sectors.setdefault(sector, t)
            elif flag == "CLEAR":
                if scope == "Track":
                    for sec, start in sorted(open_sectors.items()):
                        windows.append((start, t, "yellow-s%s" % sec))
                    open_sectors.clear()
                    if windows and windows[-1][2] == "SC/VSC" and (t - windows[-1][1]).total_seconds() <= 60:
                        s0, _, lbl = windows.pop()
                        windows.append((s0, t, lbl))
                elif sector is not None and sector in open_sectors:
                    windows.append((open_sectors.pop(sector), t, "yellow-s%s" % sector))
            elif flag == "RED":
                red_open = red_open or t
            elif flag == "GREEN" and red_open is not None:
                windows.append((red_open, t, "red"))
                red_open = None
    if events:
        t_end = parse_ts(events[-1]["date"])
        for sec, start in sorted(open_sectors.items()):
            windows.append((start, t_end, "yellow-s%s" % sec))
        if sc_open is not None:
            windows.append((sc_open, t_end, "SC/VSC"))
        if red_open is not None:
            windows.append((red_open, t_end, "red"))
    return sorted(windows)


def overlaps_any(start, end, windows):
    # bounded linear scan over ~30 windows per lap; fine at this size
    return any(ws < end and start < we for ws, we, _ in windows)


def in_lap_numbers(stints):
    """E3: last lap of every stint that is followed by another stint."""
    by_driver = {}
    for s in stints:
        by_driver.setdefault(s["driver_number"], []).append(s)
    inlaps = set()
    for drv, ss in by_driver.items():
        ss.sort(key=lambda s: s["stint_number"])
        for cur, nxt in zip(ss, ss[1:]):
            if cur["lap_end"] is not None:
                inlaps.add((drv, cur["lap_end"]))
    return inlaps


def ols(points):
    """Closed-form OLS y ~ a + b*x -> (slope, intercept, stderr_slope, n, residuals)."""
    n = len(points)
    xbar = sum(x for x, _ in points) / n
    ybar = sum(y for _, y in points) / n
    sxx = sum((x - xbar) ** 2 for x, _ in points)
    if sxx == 0:
        return None
    sxy = sum((x - xbar) * (y - ybar) for x, y in points)
    b = sxy / sxx
    a = ybar - b * xbar
    resid = [y - (a + b * x) for x, y in points]
    sse = sum(r * r for r in resid)
    se = math.sqrt((sse / (n - 2)) / sxx) if n > 2 else float("nan")
    return b, a, se, n, resid


def percentile(sorted_vals, p):
    """Linear-interpolation percentile on a pre-sorted list (deterministic)."""
    if not sorted_vals:
        return float("nan")
    k = (len(sorted_vals) - 1) * p
    f, c = math.floor(k), math.ceil(k)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def fit_stints(laps, stints, windows):
    lap_index = {(l["driver_number"], l["lap_number"]): l for l in laps}
    inlaps = in_lap_numbers(stints)
    drops = {"null_duration": 0, "pit_out": 0, "in_lap": 0, "neutralized": 0, "outlier": 0, "kept": 0}
    fits = []
    for s in sorted(stints, key=lambda s: (s["driver_number"], s["stint_number"])):
        drv, comp = s["driver_number"], s["compound"]
        if s["lap_start"] is None or s["lap_end"] is None or comp is None:
            continue
        pts = []
        for lap_no in range(s["lap_start"], s["lap_end"] + 1):
            lap = lap_index.get((drv, lap_no))
            if lap is None or lap.get("lap_duration") is None:
                drops["null_duration"] += 1
                continue
            if lap.get("is_pit_out_lap"):
                drops["pit_out"] += 1
                continue
            if (drv, lap_no) in inlaps:
                drops["in_lap"] += 1
                continue
            t0 = parse_ts(lap["date_start"])
            t1 = t0 + timedelta(seconds=lap["lap_duration"])
            if overlaps_any(t0, t1, windows):
                drops["neutralized"] += 1
                continue
            age = s["tyre_age_at_start"] + (lap_no - s["lap_start"])
            pts.append((age, lap["lap_duration"]))
        if len(pts) < MIN_LAPS:
            continue
        first = ols(pts)
        if first is None:
            continue
        resid = first[4]
        abs_r = sorted(abs(r) for r in resid)
        cut = max(OUTLIER_FLOOR_S, percentile(abs_r, 0.90))
        kept = [p for p, r in zip(pts, resid) if abs(r) <= cut]
        drops["outlier"] += len(pts) - len(kept)
        if len(kept) < MIN_LAPS:
            continue
        final = ols(kept)
        if final is None:
            continue
        b, a, se, n, _ = final
        drops["kept"] += n
        fits.append({
            "driver": drv, "stint": s["stint_number"], "compound": comp,
            "laps_fit": n, "tyre_age_start": s["tyre_age_at_start"],
            "slope_raw": round(b, 4), "slope_fuel_adj": round(b + FUEL_GAIN_S_PER_LAP, 4),
            "intercept": round(a, 3), "stderr_slope": round(se, 4),
        })
    return fits, drops


def aggregate(fits):
    agg = {}
    for comp in COMPOUND_ORDER:
        rows = [f for f in fits if f["compound"] == comp]
        if not rows:
            continue
        slopes = sorted(f["slope_raw"] for f in rows)
        ses = sorted(f["stderr_slope"] for f in rows)
        med = statistics.median(slopes)
        q1, q3 = percentile(slopes, 0.25), percentile(slopes, 0.75)
        agg[comp] = {
            "n_stints": len(rows),
            "median_slope_raw": round(med, 4),
            "median_slope_fuel_adj": round(med + FUEL_GAIN_S_PER_LAP, 4),
            "iqr": [round(q1, 4), round(q3, 4)],
            "share_positive_raw": round(sum(1 for v in slopes if v > 0) / len(slopes), 3),
            "share_positive_fuel_adj": round(sum(1 for v in slopes if v + FUEL_GAIN_S_PER_LAP > 0) / len(slopes), 3),
            "median_stderr": round(statistics.median(ses), 4),
        }
    return agg


def verdict_of(agg):
    """Rubric: signal-usable / signal-marginal / noise-dominated."""
    dry = [c for c in ("SOFT", "MEDIUM", "HARD") if c in agg]
    if len(dry) < 2:
        return "noise-dominated", "fewer than 2 dry compounds fit"
    meds = {c: agg[c]["median_slope_fuel_adj"] for c in dry}
    ordered = all(meds[a] >= meds[b] for a, b in zip(dry, dry[1:]))
    ratios = {c: (abs(agg[c]["median_slope_fuel_adj"]) / agg[c]["median_stderr"]
                  if agg[c]["median_stderr"] > 0 else float("inf")) for c in dry}
    min_ratio = min(ratios.values())
    detail = ("ordering=%s (%s); min |slope|/stderr ratio=%.2f"
              % ("OK" if ordered else "VIOLATED",
                 " > ".join("%s:%+.3f" % (c, meds[c]) for c in dry), min_ratio))
    if ordered and min_ratio >= 2.0:
        return "signal-usable", detail
    if ordered and min_ratio >= 1.0:
        return "signal-marginal", detail
    return "noise-dominated", detail


def render_md(agg, fits, drops, verdict, detail, n_windows):
    L = []
    L.append("## Tyre-deg slope fit - session 1285/11291")
    L.append("")
    L.append("Verdict: **%s** - %s" % (verdict, detail))
    L.append("")
    L.append("Stints fit: %d of 56 | laps kept: %d | dropped: null=%d, pit-out=%d, "
             "in-lap=%d, SC/VSC/yellow=%d, outlier=%d | neutralization windows: %d"
             % (len(fits), drops["kept"], drops["null_duration"], drops["pit_out"],
                drops["in_lap"], drops["neutralized"], drops["outlier"], n_windows))
    L.append("")
    L.append("### Per-compound aggregate (s/lap; fuel-adj = raw + 0.05 assumed fuel gain)")
    L.append("")
    L.append("| compound | stints | median raw | median fuel-adj | IQR (raw) | share>0 (adj) | median stderr |")
    L.append("|---|---|---|---|---|---|---|")
    for comp in COMPOUND_ORDER:
        if comp not in agg:
            continue
        a = agg[comp]
        L.append("| %s | %d | %+.4f | %+.4f | [%+.4f, %+.4f] | %.0f%% | %.4f |"
                 % (comp, a["n_stints"], a["median_slope_raw"], a["median_slope_fuel_adj"],
                    a["iqr"][0], a["iqr"][1], 100 * a["share_positive_fuel_adj"], a["median_stderr"]))
    L.append("")
    dry = [c for c in ("SOFT", "MEDIUM", "HARD") if c in agg]
    if len(dry) >= 2:
        L.append("### Compound deltas (fuel-free: the fuel term cancels between compounds)")
        L.append("")
        for a, b in zip(dry, dry[1:]):
            d = agg[a]["median_slope_raw"] - agg[b]["median_slope_raw"]
            L.append("- %s - %s: %+.4f s/lap" % (a, b, d))
        L.append("")
    L.append("### Per-stint fits")
    L.append("")
    L.append("| driver | stint | compound | n | age0 | slope raw | slope adj | stderr | ratio |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for f in fits:
        ratio = abs(f["slope_raw"]) / f["stderr_slope"] if f["stderr_slope"] > 0 else float("inf")
        L.append("| %d | %d | %s | %d | %d | %+.4f | %+.4f | %.4f | %.1f |"
                 % (f["driver"], f["stint"], f["compound"], f["laps_fit"], f["tyre_age_start"],
                    f["slope_raw"], f["slope_fuel_adj"], f["stderr_slope"], ratio))
    return "\n".join(L) + "\n"


def main():
    if len(sys.argv) != 2:
        print("usage: python3 deg_fit.py <fixture_dir>", file=sys.stderr)
        return 2
    laps, stints, rc = load(sys.argv[1])
    windows = neutralization_windows(rc)
    fits, drops = fit_stints(laps, stints, windows)
    agg = aggregate(fits)
    verdict, detail = verdict_of(agg)
    md = render_md(agg, fits, drops, verdict, detail, len(windows))
    out = Path(__file__).resolve().parent
    results = {
        "session": "1285_11291", "verdict": verdict, "verdict_detail": detail,
        "assumptions": {"fuel_gain_s_per_lap": FUEL_GAIN_S_PER_LAP, "min_laps": MIN_LAPS,
                        "outlier_rule": "drop |resid| > max(1.5s, P90 of stint |resid|), one refit"},
        "neutralization_windows": [[str(a), str(b), lbl] for a, b, lbl in windows],
        "drop_counts": drops, "per_compound": agg, "per_stint": fits,
    }
    (out / "results.json").write_text(json.dumps(results, indent=1) + "\n")
    (out / "results.md").write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
