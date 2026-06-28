#!/usr/bin/env python3
"""Weight-recalibration experiment on the saved validation panels.

composite_decile_backtest.py measured each signal's IC. This re-weights the SAME
panel (no re-fetch) under candidate weight vectors and reports the composite's
per-date IC + decile spread, so we can see whether an IC-informed reweight fixes
the mis-calibration (US weakly-positive, KR inverted) the validation exposed.

IN-SAMPLE caveat: weights tuned to these same returns will look better here than
live. The point is directional — does turning on atr_risk and cutting the dead
high-weight signals flip KR positive and lift US? If yes, the diagnosis (weights,
not signals) holds. Treat magnitudes as upper bounds.

Usage: python backtest/weight_experiment.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SIG_KEYS = ["drawdown", "relative_strength", "vcp_contraction", "weekly_macd",
            "macd_cross", "volume_surge", "obv_accumulation", "atr_risk",
            "rsi", "bollinger", "moving_average"]

# current live weights (from each filter's `weight=`)
W_CURRENT = {
    "drawdown": 0.10, "relative_strength": 0.15, "vcp_contraction": 0.10,
    "weekly_macd": 0.15, "macd_cross": 0.10, "volume_surge": 0.10,
    "obv_accumulation": 0.10, "atr_risk": 0.00, "rsi": 0.10,
    "bollinger": 0.10, "moving_average": 0.10,
}

# IC-informed proposal: atr_risk ON (best signal, t>3 both mkts), dead high-weight
# signals (RS, weekly_macd) cut, anti-predictive ones (volume_surge, obv) zeroed.
W_PROPOSED = {
    "drawdown": 0.10, "relative_strength": 0.05, "vcp_contraction": 0.10,
    "weekly_macd": 0.05, "macd_cross": 0.10, "volume_surge": 0.00,
    "obv_accumulation": 0.00, "atr_risk": 0.25, "rsi": 0.05,
    "bollinger": 0.05, "moving_average": 0.05,
}

# minimal-change variant: ONLY turn on atr_risk (most defensible single edit)
W_ATR_ONLY = dict(W_CURRENT, atr_risk=0.20)


def spearman(a, b):
    return a.rank().corr(b.rank())


def composite(panel, weights):
    cols = [f"_score_{k}" for k in SIG_KEYS]
    S = panel[cols].to_numpy(dtype=float)
    w = np.array([weights[k] for k in SIG_KEYS], dtype=float)
    avail = ~np.isnan(S)
    num = np.nansum(np.where(avail, S * w, 0.0), axis=1)
    den = (np.where(avail, w, 0.0)).sum(axis=1)
    return np.where(den > 0, num / den, np.nan)


def per_date_ic(panel, comp, ret):
    df = pd.DataFrame({"c": comp, "r": panel[ret].values, "d": panel["date"].values}).dropna()
    ics = []
    for _, g in df.groupby("d"):
        if len(g) >= 8 and g["c"].nunique() > 1:
            ic = spearman(g["c"], g["r"])
            if pd.notna(ic):
                ics.append(ic)
    if not ics:
        return np.nan, np.nan, np.nan
    a = np.array(ics)
    t = a.mean() / (a.std(ddof=1) / np.sqrt(len(a))) if len(a) > 1 and a.std(ddof=1) > 0 else np.nan
    return a.mean(), t, (a > 0).mean()


def decile_spread(panel, comp, ret, qn=10):
    df = pd.DataFrame({"c": comp, "r": panel[ret].values}).dropna()
    if len(df) < 100:
        return np.nan, np.nan
    df["q"] = pd.qcut(df["c"].rank(method="first"), qn, labels=False)
    m = df.groupby("q")["r"].mean()
    return m.iloc[-1] - m.iloc[0], spearman(pd.Series(m.index), m.reset_index(drop=True))


def live_weights():
    """Read the weights actually registered in the filters right now — a regression
    check that the applied edits produce the expected composite IC (and import OK)."""
    sys.path.insert(0, str(ROOT / "src"))
    from screener.filters import base as fbase
    fbase.load_all()
    return {k: fbase.get(k).weight for k in SIG_KEYS}


def main():
    sets = {"적용전(0623)": W_CURRENT, "atr만 켬": W_ATR_ONLY,
            "IC제안(v2)": W_PROPOSED, "현재레지스트리": live_weights()}
    for market in ("US", "KR"):
        path = ROOT / "exports" / f"validation_panel_{market}.parquet"
        if not path.exists():
            print(f"{market}: panel 없음 — composite_decile_backtest.py 먼저 실행")
            continue
        panel = pd.read_parquet(path)
        print(f"\n========== {market}  (n={len(panel)}, 날짜 {panel['date'].nunique()}) ==========")
        for ret in ("fwd_120", "fwd_250"):
            print(f"\n  [{ret}]  per-date IC (t, +날짜%)        | 상위-하위 스프레드 (단조)")
            for label, w in sets.items():
                comp = composite(panel, w)
                ic, t, pos = per_date_ic(panel, comp, ret)
                spread, mono = decile_spread(panel, comp, ret)
                print(f"    {label:12s}  {ic:+.3f} (t{t:+.1f}, {pos:.0%})"
                      f"   | {spread:+.1f}%p (mono {mono:+.2f})")
    print()


if __name__ == "__main__":
    main()
