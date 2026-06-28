#!/usr/bin/env python3
"""Explore price-based TIMING signals — the validated weak spot.

The score picks WHAT (recoverable vs falling knife) but the strategy backtest
showed timing (WHEN to enter) is weak. This tests candidate price-only timing
signals' per-date IC on the cohort, point-in-time, to see if any adds an entry
edge worth turning into a filter. Exploratory only (no filter changes): a signal
earns a filter if it shows a consistent positive IC on KR (the trustworthy arm).

Candidates (computed from the <=T price slice):
  - off_lows    : close / min(close[-60:]) - 1   (recovered off the trough = basing)
  - higher_low  : min(close[-20:]) > min(close[-40:-20])  (bottoming structure)
  - vol_dryup   : 1 - mean(vol[-20:]) / mean(vol[-120:-20])  (volume drying up)
  - above_ma50  : close / mean(close[-50:]) - 1  (reclaimed the 50d MA)

Usage: python backtest/timing_signals_explore.py
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

HORIZONS = [120, 250]


def spearman(a, b):
    return a.rank().corr(b.rank())


def per_date_ic(df, col, ret):
    sub = df[[col, ret, "date"]].dropna()
    ics = [spearman(g[col], g[ret]) for _, g in sub.groupby("date")
           if len(g) >= 8 and g[col].nunique() > 1]
    ics = [x for x in ics if pd.notna(x)]
    if not ics:
        return np.nan, np.nan, np.nan
    a = np.array(ics)
    t = a.mean() / (a.std(ddof=1) / np.sqrt(len(a))) if len(a) > 1 and a.std(ddof=1) > 0 else np.nan
    return a.mean(), t, (a > 0).mean()


def candidates(close: np.ndarray, vol: np.ndarray, i: int) -> dict:
    """Timing-signal values from the series up to index i (inclusive)."""
    def w(arr, a, b):  # safe slice arr[i-a : i-b]
        lo, hi = max(0, i - a), max(0, i - b)
        return arr[lo:hi]
    out = {}
    last = close[i]
    low60 = np.min(close[max(0, i - 59):i + 1])
    out["off_lows"] = (last / low60 - 1.0) if low60 > 0 else np.nan
    l20, l40 = w(close, 20, 0), w(close, 40, 20)
    out["higher_low"] = float(np.min(l20) > np.min(l40)) if len(l20) and len(l40) else np.nan
    v20, v120 = w(vol, 20, 0), w(vol, 120, 20)
    out["vol_dryup"] = (1 - v20.mean() / v120.mean()) if len(v20) and len(v120) and v120.mean() > 0 else np.nan
    ma50 = np.mean(close[max(0, i - 49):i + 1])
    out["above_ma50"] = (last / ma50 - 1.0) if ma50 > 0 else np.nan
    return out


def main():
    for market in ("KR", "US"):
        ppath = ROOT / "exports" / f"prices_{market.lower()}.parquet"
        panpath = ROOT / "exports" / f"validation_panel_{market}_v1.parquet"
        if not ppath.exists() or not panpath.exists():
            print(f"{market}: 데이터 없음"); continue
        prices = pd.read_parquet(ppath)
        prices["date"] = pd.to_datetime(prices["date"])
        panel = pd.read_parquet(panpath)
        panel["date"] = pd.to_datetime(panel["date"])
        # per-ticker sorted close/volume arrays (same order build_panel used)
        arrs = {}
        for tk, g in prices.groupby("ticker", sort=False):
            g = g.sort_values("date")
            arrs[tk] = (g["adj_close"].to_numpy(float), g["volume"].to_numpy(float))

        recs = []
        miss = 0
        for r in panel.itertuples(index=False):
            a = arrs.get(r.ticker)
            if a is None or int(r.pos) >= len(a[0]):
                miss += 1
                continue
            row = {"date": r.date, "fwd_120": r.fwd_120, "fwd_250": r.fwd_250}
            row.update(candidates(a[0], a[1], int(r.pos)))
            recs.append(row)
        df = pd.DataFrame(recs)
        print(f"\n===== {market}  (n={len(df)}, miss {miss}) — 타이밍 신호 per-date IC =====")
        print(f"  {'신호':12s}  {'120d IC(t,+날짜)':>22s}  {'250d IC(t,+날짜)':>22s}")
        for col in ("off_lows", "higher_low", "vol_dryup", "above_ma50"):
            cells = []
            for h in HORIZONS:
                ic, t, pos = per_date_ic(df, col, f"fwd_{h}")
                cells.append(f"{ic:+.3f} (t{t:+.1f},{pos:.0%})")
            print(f"  {col:12s}  {cells[0]:>22s}  {cells[1]:>22s}")
    print("\n해석: KR(신뢰)서 |t|≳2·일관 양(+)이면 진입 타이밍 엣지 → 필터화 후보. 0근처면 기존 신호로 충분.")


if __name__ == "__main__":
    main()
