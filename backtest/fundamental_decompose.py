#!/usr/bin/env python3
"""Decompose the `fundamental` signal — which component is negative on US?

At power, the combined `fundamental` score (revenue-YoY + op-margin + debt/equity)
is the strongest signal on KR (t5-7) but NEGATIVE on US (t-2.7). This re-derives
each cohort row's point-in-time FundamentalsBundle (cached EDGAR/DART, no refetch),
scores the three components separately, and measures each one's per-date IC vs
forward returns — to find the culprit and judge whether a market-specific or
component-level reweight is warranted.

Usage: python backtest/fundamental_decompose.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "backtest"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from screener import fundamentals as fund, scoring  # noqa: E402

HORIZONS = [120, 250]
# the three sub-scores of fundamental_score (scoring.py)
COMPONENTS = {
    "revenue_yoy": (scoring.fundamental_revenue_score, "매출성장"),
    "op_margin": (scoring.fundamental_margin_score, "영업마진"),
    "debt_to_equity": (scoring.fundamental_debt_score, "부채/자본"),
}


def spearman(a, b):
    return a.rank().corr(b.rank())


def per_date_ic(df, score_col, ret_col):
    sub = df[[score_col, ret_col, "date"]].dropna()
    ics = [spearman(g[score_col], g[ret_col]) for _, g in sub.groupby("date")
           if len(g) >= 8 and g[score_col].nunique() > 1]
    ics = [x for x in ics if pd.notna(x)]
    if not ics:
        return np.nan, np.nan, np.nan
    a = np.array(ics)
    t = a.mean() / (a.std(ddof=1) / np.sqrt(len(a))) if len(a) > 1 and a.std(ddof=1) > 0 else np.nan
    return a.mean(), t, (a > 0).mean()


def _bundle_getter(market):
    """Return f(ticker, T_str) -> FundamentalsBundle, reusing cached PIT sources."""
    if market == "US":
        import edgar_pit
        cmap = edgar_pit.load_cik_map()
        cache = {}

        def get(ticker, T):
            if ticker not in cache:
                cik = cmap.get(ticker.upper())
                cache[ticker] = edgar_pit.fetch_companyfacts(cik) if cik else None
            cf = cache[ticker]
            if not cf:
                return None
            rows = edgar_pit.pit_rows(cf, T)
            return fund._signals_from_rows(rows, market="KR") if rows else None
        return get
    else:
        import dart_pit
        key = os.getenv("DART_API_KEY") or ""
        try:
            cmap = fund._load_corp_map(key)  # disk-cached from the v1b run
        except Exception:
            cmap = {}

        def get(ticker, T):
            corp = cmap.get(ticker)
            if not corp:
                return None
            rows = dart_pit.pit_rows(key, corp, T)  # reads disk cache; key only on miss
            return fund._signals_from_rows(rows, market="KR") if rows else None
        return get


def main():
    for market in ("KR", "US"):
        path = ROOT / "exports" / f"validation_panel_{market}_v1.parquet"
        if not path.exists():
            print(f"{market}: panel 없음"); continue
        panel = pd.read_parquet(path)
        panel["date"] = pd.to_datetime(panel["date"])
        get = _bundle_getter(market)

        # re-derive each component score per (ticker, T)
        recs = []
        seen_fail = 0
        for r in panel.itertuples(index=False):
            T = pd.Timestamp(r.date).strftime("%Y-%m-%d")
            fb = get(r.ticker, T)
            row = {"date": r.date, "fwd_120": r.fwd_120, "fwd_250": r.fwd_250}
            if fb is None or not getattr(fb, "available", False):
                seen_fail += 1
            else:
                for field, (fn, _) in COMPONENTS.items():
                    v = getattr(fb, field, None)
                    row[f"s_{field}"] = fn(v) if v is not None else np.nan
            recs.append(row)
        df = pd.DataFrame(recs)

        print(f"\n===== {market}  (n={len(df)}, 번들실패 {seen_fail}) — 컴포넌트별 per-date IC =====")
        print(f"  {'컴포넌트':12s} {'데이터%':>7s}  {'120d IC(t,+날짜)':>22s}  {'250d IC(t,+날짜)':>22s}")
        for field, (_, label) in COMPONENTS.items():
            col = f"s_{field}"
            if col not in df:
                print(f"  {label:12s}  데이터 없음"); continue
            cov = df[col].notna().mean()
            cells = []
            for h in HORIZONS:
                ic, t, pos = per_date_ic(df, col, f"fwd_{h}")
                cells.append(f"{ic:+.3f} (t{t:+.1f},{pos:.0%})")
            print(f"  {label:12s} {cov:>6.0%}  {cells[0]:>22s}  {cells[1]:>22s}")
    print()


if __name__ == "__main__":
    main()
