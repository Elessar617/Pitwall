<!-- wayfinder asset: resolves ticket #18 (Deg-slope prototype v2) on map #2 - resolved 2026-07-12 -->

# Wayfinder #18 - deg-slope prototype v2 (pooled model + track-evolution regressor)

**Overall verdict: noise-dominated** (rubric is Catalunya-based; see below).

Model: `lap_duration = stint_intercept[j] + beta_evo*f(session_minutes) + beta_deg[c]*tyre_age`, pooled across stints/drivers, hand-rolled normal equations (Gauss-Jordan), stdlib only. Cleaning reused from v1 (null/pit-out/in-lap/SC-VSC-yellow windows/per-stint P90-residual trim, min 5 clean laps per stint). f tried linear and log1p; lower-SSE form used per fixture (log1p won on both).

## Catalunya 1287_11307 (HIGH-deg venue, the rubric fixture)

## Pooled deg-slope fit v2 (evolution-adjusted) - session 1287_11307

Verdict (log1p evolution model): **noise-dominated** - ordering=VIOLATED (SOFT:+0.0580 > MEDIUM:+0.1195 > HARD:+0.1066); band[0.02,0.15]=OK; 2-sigma=OK

Laps pooled: 977 across 63 stints (67 params) | dropped: null=0, pit-out=48, in-lap=48, SC/VSC/yellow=86, outlier=58 | neutralization windows: 8

Within-stint demeaned corr(tyre_age, session_minutes) = 0.9997 (identification of deg vs evolution rests on cross-stint contrast)

### Evolution term and model comparison (SSE)

| model | beta_evo | se(evo) | SSE | residual s |
|---|---|---|---|---|
| linear | -0.62038 | 0.09474 | 240.71 | 0.514 |
| log1p (best) | +0.63797 | 0.08246 | 236.50 | 0.510 |
| no-evolution | - | - | 252.06 | 0.526 |

(beta_evo units: s/lap per minute for linear; s/lap per log1p-minute for log1p. SSE improvement of best vs no-evolution: 252.06 -> 236.50, -6.2%)

### Per-compound deg slopes, log1p evolution model (s/lap of tyre age)

| compound | n_stints | n_laps | beta raw | beta fuel-adj (+0.05) | stderr | ratio adj/se |
|---|---|---|---|---|---|---|
| SOFT | 10 | 115 | +0.0080 | +0.0580 | 0.0102 | 5.7 |
| MEDIUM | 18 | 238 | +0.0695 | +0.1195 | 0.0095 | 12.5 |
| HARD | 35 | 624 | +0.0566 | +0.1066 | 0.0042 | 25.1 |

### Compound deltas (fuel-free: the fuel term cancels)

- SOFT - MEDIUM: -0.0615 s/lap (se 0.0120, ratio 5.1)
- MEDIUM - HARD: +0.0130 s/lap (se 0.0088, ratio 1.5)

### Verdicts per evolution model

- linear: **noise-dominated** - ordering=VIOLATED (SOFT:+0.9796 > MEDIUM:+1.0417 > HARD:+0.9954); band[0.02,0.15]=MISS; 2-sigma=OK
- log1p: **noise-dominated** - ordering=VIOLATED (SOFT:+0.0580 > MEDIUM:+0.1195 > HARD:+0.1066); band[0.02,0.15]=OK; 2-sigma=OK


## Montreal 1285_11291 (v1 fixture, rerun for contrast)

## Pooled deg-slope fit v2 (evolution-adjusted) - session 1285_11291

Verdict (log1p evolution model): **signal-usable** - ordering=OK (SOFT:+0.0907 > MEDIUM:+0.0690 > HARD:+0.0440); band[0.02,0.15]=OK; 2-sigma=OK

Laps pooled: 850 across 45 stints (49 params) | dropped: null=1, pit-out=34, in-lap=33, SC/VSC/yellow=187, outlier=90 | neutralization windows: 12

Within-stint demeaned corr(tyre_age, session_minutes) = 0.9998 (identification of deg vs evolution rests on cross-stint contrast)

### Evolution term and model comparison (SSE)

| model | beta_evo | se(evo) | SSE | residual s |
|---|---|---|---|---|
| linear | +0.24138 | 0.12638 | 650.83 | 0.901 |
| log1p (best) | -2.03582 | 0.09895 | 427.74 | 0.731 |
| no-evolution | - | - | 653.80 | 0.903 |

(beta_evo units: s/lap per minute for linear; s/lap per log1p-minute for log1p. SSE improvement of best vs no-evolution: 653.80 -> 427.74, -34.6%)

### Per-compound deg slopes, log1p evolution model (s/lap of tyre age)

| compound | n_stints | n_laps | beta raw | beta fuel-adj (+0.05) | stderr | ratio adj/se |
|---|---|---|---|---|---|---|
| SOFT | 21 | 342 | +0.0407 | +0.0907 | 0.0078 | 11.6 |
| MEDIUM | 22 | 452 | +0.0190 | +0.0690 | 0.0047 | 14.7 |
| HARD | 2 | 56 | -0.0060 | +0.0440 | 0.0095 | 4.6 |

### Compound deltas (fuel-free: the fuel term cancels)

- SOFT - MEDIUM: +0.0217 s/lap (se 0.0068, ratio 3.2)
- MEDIUM - HARD: +0.0250 s/lap (se 0.0100, ratio 2.5)

### Verdicts per evolution model

- linear: **noise-dominated** - ordering=VIOLATED (SOFT:-0.3485 > MEDIUM:-0.3108 > HARD:-0.3149); band[0.02,0.15]=MISS; 2-sigma=MISS
- log1p: **signal-usable** - ordering=OK (SOFT:+0.0907 > MEDIUM:+0.0690 > HARD:+0.0440); band[0.02,0.15]=OK; 2-sigma=OK


## Reading

- **Catalunya fails the rubric on ordering**: fuel-adjusted SOFT +0.0580 < MEDIUM +0.1195 > HARD +0.1066.
  The SOFT-MEDIUM delta (-0.0615, se 0.0120, 5.1 sigma) is confidently the WRONG sign. Diagnostic: 7 of the
  10 fit SOFT stints start at lap 1 (naive within-stint slopes +0.16..+0.23 s/lap), exactly where log1p(t)
  changes fastest, so the pooled model reassigns early-race SOFT degradation to the evolution term
  (beta_evo +0.638 per log1p-minute, an odd positive sign that itself flags misattribution). The late-race
  SOFT stints (naive slopes -0.01..+0.11) then anchor beta_deg[SOFT] low.
- **Identification is fragile, not just noisy**: switching f from log1p to linear swings Catalunya's raw deg
  betas from ~+0.06 to ~+0.93-0.99 s/lap while SSE differs by only 1.8%. Within-stint demeaned
  corr(age, time) = 0.9997. The deg/evolution split is decided almost entirely by the functional form
  assumed for evolution, which the data barely constrains. Reported stderrs are conditional on the chosen
  f and therefore flatter than honest.
- **Montreal passes the same rubric** (SOFT +0.0907 > MEDIUM +0.0690 > HARD +0.0440, all in band, all
  >2 sigma, log1p SSE -34.6% vs no-evolution) - but given the fragility above and that v1 called this
  venue noise-dominated, one passing fixture with a form-sensitive estimator is not a basis to ship deg hints.
- Per the ticket: v2 fails on the rubric fixture -> deg hints drop from the roadmap, with two honest
  datapoints (v1 per-stint OLS, v2 pooled+evolution) recorded.

## Resolution

Verdict **noise-dominated** on the rubric fixture (Catalunya): fuel-adjusted compound ordering
violated with the fuel-free SOFT-MEDIUM delta confidently the wrong sign (-0.0615 s/lap, 5.1 sigma);
identification is form-fragile (within-stint corr(age, session_time) ~0.9997; log1p vs linear swings
betas ~15x at ~2% SSE change). Montreal passing the same rubric under log1p reverses v1 for that venue
and proves the estimator is model-choice-sensitive, not shippable. **Per the ticket: per-stint tyre-deg
hints drop from the roadmap** (two honest datapoints on record; #12 closes as out of scope).

## Appendix - reproduction script (stdlib only)

Run: `python3 deg_fit_v2.py <repo>/data/fixtures/<fixture_dir>` - deterministic.

```python
#!/usr/bin/env python3
"""Wayfinder #18 prototype v2: pooled per-compound tyre-deg slopes with a
track-evolution (session-time) regressor.

Model (single pooled OLS per fixture, solved by hand-rolled normal equations):

  lap_duration = stint_intercept[j]
               + beta_evo * f(session_time_minutes)
               + sum_c beta_deg[c] * tyre_age * 1[compound == c]

- stint intercepts absorb driver/car pace and fuel load AT STINT START;
- beta_evo (shared) absorbs track evolution;
- beta_deg per compound is the quantity of interest.

f(session_time): tried both linear (minutes since first lap start) and
log1p(minutes); the fit with lower SSE is used for the verdict, both are
reported.

Cleaning is reused verbatim from prototype v1 (ship/docs/2026-07-12-
prototype-deg-slopes.md):
  E1 lap_duration null/missing (or null date_start)  -> dropped
  E2 is_pit_out_lap                                  -> dropped
  E3 last lap of a stint followed by another stint    -> dropped (in-lap)
  E4 lap overlaps a SC/VSC/yellow/red window from race_control.json
  E5 residual outlier trim: per-stint OLS of duration ~ tyre_age, drop laps
     with |residual| > max(1.5 s, P90 of that stint's |residuals|), then the
     surviving laps enter the POOLED fit (one trim pass, no refit-retrim).
Stints contribute only if >= 5 clean laps survive (MIN_LAPS).

Honesty notes baked into the output:
- Within a stint, tyre_age and session_time advance together (near-perfectly
  collinear); identification of beta_deg vs beta_evo comes ONLY from stints
  starting at different times on different compounds. We report the
  within-stint-demeaned correlation corr(age~, time~) and the stderrs from
  (X'X)^-1 * s^2 so the collinearity cost is visible, not hidden.
- Per-stint intercepts do NOT absorb within-stint fuel burn-off; fuel gain
  remains collinear with tyre_age. beta_deg is reported raw and with the
  same +0.05 s/lap fuel-gain adjustment as v1. Compound DELTAS are fuel-free
  (the fuel term cancels) and carry the ordering test.

Usage: python3 deg_fit_v2.py <fixture_dir>
Deterministic: no randomness, stable sorts, pure stdlib (Python 3.13).
Writes <script_dir>/<fixture_name>/results.json and results.md; prints the md.
"""

import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

MIN_LAPS = 5
FUEL_GAIN_S_PER_LAP = 0.05  # assumed lap-time gain per lap from fuel burn (v1)
OUTLIER_FLOOR_S = 1.5       # E5 floor: never drop residuals smaller than this
DRY = ["SOFT", "MEDIUM", "HARD"]
COMPOUND_ORDER = DRY + ["INTERMEDIATE", "WET"]
BAND_LO, BAND_HI = 0.02, 0.15  # plausible fuel-adjusted deg band (s/lap)


def parse_ts(s):
    return datetime.fromisoformat(s)


def load(fixture_dir):
    d = Path(fixture_dir)
    laps = json.loads((d / "laps.json").read_text())
    stints = json.loads((d / "stints.json").read_text())
    rc = json.loads((d / "race_control.json").read_text())
    return laps, stints, rc


def neutralization_windows(rc):
    """E4 windows -- identical logic to v1 (see module docstring)."""
    events = sorted(rc, key=lambda r: r["date"])
    windows = []
    open_sectors = {}
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
                windows.append((sc_open, t, "SC/VSC"))
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
    # bounded linear scan over a few dozen windows per lap; fine at this size
    return any(ws < end and start < we for ws, we, _ in windows)


def in_lap_numbers(stints):
    """E3: last lap of every stint that is followed by another stint."""
    by_driver = {}
    for s in stints:
        by_driver.setdefault(s["driver_number"], []).append(s)
    inlaps = set()
    for drv, ss in by_driver.items():
        ss.sort(key=lambda s: s["stint_number"])
        for cur, _nxt in zip(ss, ss[1:]):
            if cur["lap_end"] is not None:
                inlaps.add((drv, cur["lap_end"]))
    return inlaps


def percentile(sorted_vals, p):
    """Linear-interpolation percentile on a pre-sorted list (deterministic)."""
    if not sorted_vals:
        return float("nan")
    k = (len(sorted_vals) - 1) * p
    f, c = math.floor(k), math.ceil(k)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def simple_ols_residuals(pts):
    """Residuals of y ~ a + b*x (closed form); None if degenerate."""
    n = len(pts)
    xbar = sum(x for x, _ in pts) / n
    ybar = sum(y for _, y in pts) / n
    sxx = sum((x - xbar) ** 2 for x, _ in pts)
    if sxx == 0:
        return None
    b = sum((x - xbar) * (y - ybar) for x, y in pts) / sxx
    a = ybar - b * xbar
    return [y - (a + b * x) for x, y in pts]


def clean_laps(laps, stints, windows, t0):
    """Apply E1-E5; return per-stint kept observations and drop counts.

    Each observation: (tyre_age, session_minutes, lap_duration).
    """
    lap_index = {(l["driver_number"], l["lap_number"]): l for l in laps}
    inlaps = in_lap_numbers(stints)
    drops = {"null": 0, "pit_out": 0, "in_lap": 0, "neutralized": 0, "outlier": 0, "kept": 0}
    kept_stints = []  # list of (stint_key, compound, [(age, minutes, y), ...])
    for s in sorted(stints, key=lambda s: (s["driver_number"], s["stint_number"])):
        drv, comp = s["driver_number"], s["compound"]
        if s["lap_start"] is None or s["lap_end"] is None or comp is None:
            continue
        obs = []
        for lap_no in range(s["lap_start"], s["lap_end"] + 1):
            lap = lap_index.get((drv, lap_no))
            if lap is None or lap.get("lap_duration") is None or lap.get("date_start") is None:
                drops["null"] += 1
                continue
            if lap.get("is_pit_out_lap"):
                drops["pit_out"] += 1
                continue
            if (drv, lap_no) in inlaps:
                drops["in_lap"] += 1
                continue
            ts = parse_ts(lap["date_start"])
            te = ts + timedelta(seconds=lap["lap_duration"])
            if overlaps_any(ts, te, windows):
                drops["neutralized"] += 1
                continue
            age = s["tyre_age_at_start"] + (lap_no - s["lap_start"])
            minutes = (ts - t0).total_seconds() / 60.0
            obs.append((age, minutes, lap["lap_duration"]))
        if len(obs) < MIN_LAPS:
            continue
        resid = simple_ols_residuals([(a, y) for a, _, y in obs])
        if resid is None:
            continue
        abs_r = sorted(abs(r) for r in resid)
        cut = max(OUTLIER_FLOOR_S, percentile(abs_r, 0.90))
        kept = [o for o, r in zip(obs, resid) if abs(r) <= cut]
        drops["outlier"] += len(obs) - len(kept)
        if len(kept) < MIN_LAPS:
            continue
        drops["kept"] += len(kept)
        kept_stints.append(((drv, s["stint_number"]), comp, kept))
    return kept_stints, drops


def gauss_solve(A, B):
    """Solve A X = B (A: p x p, B: p x m) by Gauss-Jordan elimination with
    partial pivoting. Works on copies; returns X as p x m list of lists."""
    p = len(A)
    m = len(B[0])
    M = [row[:] + brow[:] for row, brow in zip(A, B)]
    for col in range(p):
        piv = max(range(col, p), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-12:
            raise ValueError("singular normal-equations matrix at column %d" % col)
        M[col], M[piv] = M[piv], M[col]
        inv_piv = 1.0 / M[col][col]
        for r in range(p):
            if r == col:
                continue
            f = M[r][col] * inv_piv
            if f == 0.0:
                continue
            for c in range(col, p + m):
                M[r][c] -= f * M[col][c]
    return [[M[r][p + c] / M[r][r] for c in range(m)] for r in range(p)]


def fit_pooled(kept_stints, evo_fn):
    """Pooled OLS via normal equations. evo_fn maps minutes -> regressor
    (or None for the no-evolution baseline model).

    Returns dict with betas, covariance for deg columns, SSE, dof."""
    stint_keys = [k for k, _, _ in kept_stints]
    comps = sorted({c for _, c, _ in kept_stints}, key=COMPOUND_ORDER.index)
    S = len(stint_keys)
    has_evo = evo_fn is not None
    p = S + (1 if has_evo else 0) + len(comps)
    evo_idx = S if has_evo else None
    deg_idx = {c: S + (1 if has_evo else 0) + i for i, c in enumerate(comps)}
    rows = []  # (sparse [(idx, val), ...], y)
    for si, (_, comp, obs) in enumerate(kept_stints):
        for age, minutes, y in obs:
            nz = [(si, 1.0)]
            if has_evo:
                nz.append((evo_idx, evo_fn(minutes)))
            nz.append((deg_idx[comp], float(age)))
            rows.append((nz, y))
    xtx = [[0.0] * p for _ in range(p)]
    xty = [0.0] * p
    for nz, y in rows:
        for i, vi in nz:
            xty[i] += vi * y
            for j, vj in nz:
                xtx[i][j] += vi * vj
    beta = [r[0] for r in gauss_solve(xtx, [[v] for v in xty])]
    sse = 0.0
    for nz, y in rows:
        r = y - sum(v * beta[i] for i, v in nz)
        sse += r * r
    n = len(rows)
    dof = n - p
    s2 = sse / dof
    inv = gauss_solve(xtx, [[1.0 if i == j else 0.0 for j in range(p)] for i in range(p)])
    cov = {(a, b): s2 * inv[deg_idx[a]][deg_idx[b]] for a in comps for b in comps}
    return {
        "compounds": comps, "n_laps": n, "n_stints": S, "n_params": p,
        "beta_evo": beta[evo_idx] if has_evo else None,
        "se_evo": math.sqrt(s2 * inv[evo_idx][evo_idx]) if has_evo else None,
        "beta_deg": {c: beta[deg_idx[c]] for c in comps},
        "se_deg": {c: math.sqrt(cov[(c, c)]) for c in comps},
        "cov_deg": cov, "sse": sse, "dof": dof, "s": math.sqrt(s2),
    }


def demeaned_correlation(kept_stints):
    """corr(age, minutes) after removing per-stint means -- the collinearity
    the pooled model actually faces once stint intercepts are absorbed."""
    xs, ys = [], []
    for _, _, obs in kept_stints:
        ma = sum(a for a, _, _ in obs) / len(obs)
        mm = sum(m for _, m, _ in obs) / len(obs)
        for a, m, _ in obs:
            xs.append(a - ma)
            ys.append(m - mm)
    sxx = sum(x * x for x in xs)
    syy = sum(y * y for y in ys)
    sxy = sum(x * y for x, y in zip(xs, ys))
    if sxx == 0 or syy == 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


def compound_stats(kept_stints):
    out = {}
    for _, comp, obs in kept_stints:
        d = out.setdefault(comp, {"n_stints": 0, "n_laps": 0})
        d["n_stints"] += 1
        d["n_laps"] += len(obs)
    return out


def verdict_of(fit):
    """Rubric (ticket #18): on fuel-adjusted betas --
    signal-usable  : SOFT > MEDIUM > HARD, each in [0.02, 0.15] s/lap,
                     and each |beta_adj| > 2*stderr;
    signal-marginal: ordering holds but band or 2-sigma test misses;
    noise-dominated: ordering violated or fewer than 2 dry compounds."""
    dry = [c for c in DRY if c in fit["beta_deg"]]
    if len(dry) < 2:
        return "noise-dominated", "fewer than 2 dry compounds fit"
    adj = {c: fit["beta_deg"][c] + FUEL_GAIN_S_PER_LAP for c in dry}
    ordered = all(adj[a] > adj[b] for a, b in zip(dry, dry[1:]))
    in_band = all(BAND_LO <= adj[c] <= BAND_HI for c in dry)
    sig = all(abs(adj[c]) > 2 * fit["se_deg"][c] for c in dry)
    detail = ("ordering=%s (%s); band[%.2f,%.2f]=%s; 2-sigma=%s"
              % ("OK" if ordered else "VIOLATED",
                 " > ".join("%s:%+.4f" % (c, adj[c]) for c in dry),
                 BAND_LO, BAND_HI, "OK" if in_band else "MISS",
                 "OK" if sig else "MISS"))
    if ordered and in_band and sig:
        return "signal-usable", detail
    if ordered:
        return "signal-marginal", detail
    return "noise-dominated", detail


def render_md(session, fits, best_name, kept_stints, drops, n_windows, corr, verdicts):
    fit = fits[best_name]
    base = fits["no-evolution"]
    cs = compound_stats(kept_stints)
    dry = [c for c in COMPOUND_ORDER if c in fit["beta_deg"]]
    L = []
    L.append("## Pooled deg-slope fit v2 (evolution-adjusted) - session %s" % session)
    L.append("")
    v, d = verdicts[best_name]
    L.append("Verdict (%s evolution model): **%s** - %s" % (best_name, v, d))
    L.append("")
    L.append("Laps pooled: %d across %d stints (%d params) | dropped: null=%d, pit-out=%d, "
             "in-lap=%d, SC/VSC/yellow=%d, outlier=%d | neutralization windows: %d"
             % (fit["n_laps"], fit["n_stints"], fit["n_params"], drops["null"], drops["pit_out"],
                drops["in_lap"], drops["neutralized"], drops["outlier"], n_windows))
    L.append("")
    L.append("Within-stint demeaned corr(tyre_age, session_minutes) = %.4f "
             "(identification of deg vs evolution rests on cross-stint contrast)" % corr)
    L.append("")
    L.append("### Evolution term and model comparison (SSE)")
    L.append("")
    L.append("| model | beta_evo | se(evo) | SSE | residual s |")
    L.append("|---|---|---|---|---|")
    for name in ("linear", "log1p", "no-evolution"):
        f = fits[name]
        be = "%+.5f" % f["beta_evo"] if f["beta_evo"] is not None else "-"
        se = "%.5f" % f["se_evo"] if f["se_evo"] is not None else "-"
        L.append("| %s%s | %s | %s | %.2f | %.3f |"
                 % (name, " (best)" if name == best_name else "", be, se, f["sse"], f["s"]))
    L.append("")
    L.append("(beta_evo units: s/lap per minute for linear; s/lap per log1p-minute for log1p. "
             "SSE improvement of best vs no-evolution: %.2f -> %.2f, -%.1f%%)"
             % (base["sse"], fit["sse"], 100 * (1 - fit["sse"] / base["sse"])))
    L.append("")
    L.append("### Per-compound deg slopes, %s evolution model (s/lap of tyre age)" % best_name)
    L.append("")
    L.append("| compound | n_stints | n_laps | beta raw | beta fuel-adj (+0.05) | stderr | ratio adj/se |")
    L.append("|---|---|---|---|---|---|---|")
    for c in dry:
        b = fit["beta_deg"][c]
        se = fit["se_deg"][c]
        adj = b + FUEL_GAIN_S_PER_LAP
        ratio = abs(adj) / se if se > 0 else float("inf")
        L.append("| %s | %d | %d | %+.4f | %+.4f | %.4f | %.1f |"
                 % (c, cs[c]["n_stints"], cs[c]["n_laps"], b, adj, se, ratio))
    L.append("")
    dry3 = [c for c in DRY if c in fit["beta_deg"]]
    if len(dry3) >= 2:
        L.append("### Compound deltas (fuel-free: the fuel term cancels)")
        L.append("")
        for a, b in zip(dry3, dry3[1:]):
            d_ = fit["beta_deg"][a] - fit["beta_deg"][b]
            var = fit["cov_deg"][(a, a)] + fit["cov_deg"][(b, b)] - 2 * fit["cov_deg"][(a, b)]
            se = math.sqrt(max(var, 0.0))
            L.append("- %s - %s: %+.4f s/lap (se %.4f, ratio %.1f)"
                     % (a, b, d_, se, abs(d_) / se if se > 0 else float("inf")))
        L.append("")
    L.append("### Verdicts per evolution model")
    L.append("")
    for name in ("linear", "log1p"):
        v, d = verdicts[name]
        L.append("- %s: **%s** - %s" % (name, v, d))
    return "\n".join(L) + "\n"


def main():
    if len(sys.argv) != 2:
        print("usage: python3 deg_fit_v2.py <fixture_dir>", file=sys.stderr)
        return 2
    fixture = Path(sys.argv[1])
    session = fixture.name
    laps, stints, rc = load(fixture)
    windows = neutralization_windows(rc)
    dated = [l["date_start"] for l in laps if l.get("date_start")]
    if not dated:
        print("no dated laps in fixture", file=sys.stderr)
        return 1
    t0 = min(parse_ts(d) for d in dated)
    kept_stints, drops = clean_laps(laps, stints, windows, t0)
    fits = {
        "linear": fit_pooled(kept_stints, lambda m: m),
        "log1p": fit_pooled(kept_stints, lambda m: math.log1p(m)),
        "no-evolution": fit_pooled(kept_stints, None),
    }
    best_name = min(("linear", "log1p"), key=lambda n: fits[n]["sse"])
    verdicts = {n: verdict_of(fits[n]) for n in ("linear", "log1p", "no-evolution")}
    corr = demeaned_correlation(kept_stints)
    md = render_md(session, fits, best_name, kept_stints, drops, len(windows), corr, verdicts)
    cs = compound_stats(kept_stints)
    results = {
        "session": session, "model": "pooled OLS: stint intercepts + beta_evo*f(t) + beta_deg[c]*age",
        "best_evolution_model": best_name,
        "verdict": verdicts[best_name][0], "verdict_detail": verdicts[best_name][1],
        "assumptions": {"fuel_gain_s_per_lap": FUEL_GAIN_S_PER_LAP, "min_laps": MIN_LAPS,
                        "outlier_rule": "per-stint OLS(y~age); drop |resid| > max(1.5s, stint P90), one pass",
                        "band_s_per_lap": [BAND_LO, BAND_HI]},
        "drop_counts": drops, "n_neutralization_windows": len(windows),
        "within_stint_demeaned_corr_age_time": round(corr, 4),
        "per_compound_counts": cs,
        "models": {},
    }
    for name, f in fits.items():
        results["models"][name] = {
            "n_laps": f["n_laps"], "n_stints": f["n_stints"], "n_params": f["n_params"],
            "beta_evo": None if f["beta_evo"] is None else round(f["beta_evo"], 5),
            "se_evo": None if f["se_evo"] is None else round(f["se_evo"], 5),
            "beta_deg_raw": {c: round(v, 4) for c, v in f["beta_deg"].items()},
            "beta_deg_fuel_adj": {c: round(v + FUEL_GAIN_S_PER_LAP, 4) for c, v in f["beta_deg"].items()},
            "se_deg": {c: round(v, 4) for c, v in f["se_deg"].items()},
            "sse": round(f["sse"], 2), "residual_s": round(f["s"], 3),
            "verdict": verdicts[name][0],
        }
        dry3 = [c for c in DRY if c in f["beta_deg"]]
        deltas = {}
        for a, b in zip(dry3, dry3[1:]):
            var = f["cov_deg"][(a, a)] + f["cov_deg"][(b, b)] - 2 * f["cov_deg"][(a, b)]
            deltas["%s-%s" % (a, b)] = {"delta": round(f["beta_deg"][a] - f["beta_deg"][b], 4),
                                        "se": round(math.sqrt(max(var, 0.0)), 4)}
        results["models"][name]["compound_deltas"] = deltas
    outdir = Path(__file__).resolve().parent / session
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "results.json").write_text(json.dumps(results, indent=1) + "\n")
    (outdir / "results.md").write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
