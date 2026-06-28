#!/usr/bin/env python3
"""Fundamental-weight refinement on the clean v1 panels (US EDGAR-fixed + KR DART).

The price-weight recalibration (weight_experiment.py) was a big win because the
price weights were badly mis-allocated. This asks the analogous question for the
FUNDAMENTAL weights: now that both panels are clean (EDGAR fy-bug fixed), does an
IC-informed reweight of fundamental·altman·piotroski·GP improve the price+fund
composite, or are they already well-allocated (so accruals-cut was the only fix)?

Varies ONLY the fundamental weights (price weights stay at registry values), and
measures the price+fund composite's per-date IC on each panel at 120d/250d.
IN-SAMPLE (directional). A change is only worth it if it helps BOTH markets.

Usage: python backtest/fund_weight_experiment.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from screener.filters import base as fbase  # noqa: E402
fbase.load_all()

PRICE_KEYS = ["drawdown"] + [f.key for f in fbase.optional_filters()
                             if not (f.needs_news or f.needs_fundamentals or f.needs_valuation or f.is_bonus)]
FUND_KEYS = [f.key for f in fbase.optional_filters() if f.needs_fundamentals]
ALL_KEYS = PRICE_KEYS + FUND_KEYS
REG = {k: fbase.get(k).weight for k in ALL_KEYS}  # live registry weights

# Fundamental weight sets to test (price weights always = registry).
FUND_SETS = {
    "현재(레지스트리)": {k: REG[k] for k in FUND_KEYS},
    # GP carries strong IC (KR t4-5) at low weight; piotroski high weight vs its IC.
    "GP↑·Pio↓": {**{k: REG[k] for k in FUND_KEYS}, "gross_profit": 0.18, "piotroski": 0.12},
    # do fundamentals deserve MORE total weight vs price? scale all fund x1.5.
    "펀더 비중 ×1.5": {k: REG[k] * 1.5 for k in FUND_KEYS},
    # IC-proportional (KR 250d per-date IC, floored at 0; accruals stays 0).
    "IC비례(KR250d)": {"fundamental": 0.17, "altman_z": 0.13, "gross_profit": 0.13,
                       "piotroski": 0.09, "accruals": 0.0, "share_issuance": 0.11},
}


def spearman(a, b):
    return a.rank().corr(b.rank())


def composite(panel, weights):
    cols = [f"_score_{k}" for k in ALL_KEYS if f"_score_{k}" in panel]
    keys = [k for k in ALL_KEYS if f"_score_{k}" in panel]
    S = panel[cols].to_numpy(dtype=float)
    w = np.array([weights.get(k, REG[k]) for k in keys], dtype=float)
    avail = ~np.isnan(S)
    num = np.nansum(np.where(avail, S * w, 0.0), axis=1)
    den = (np.where(avail, w, 0.0)).sum(axis=1)
    return np.where(den > 0, num / den, np.nan)


def per_date_ic(panel, comp, ret):
    df = pd.DataFrame({"c": comp, "r": panel[ret].values, "d": panel["date"].values}).dropna()
    ics = [spearman(g["c"], g["r"]) for _, g in df.groupby("d")
           if len(g) >= 8 and g["c"].nunique() > 1]
    ics = [x for x in ics if pd.notna(x)]
    if not ics:
        return np.nan, np.nan
    a = np.array(ics)
    t = a.mean() / (a.std(ddof=1) / np.sqrt(len(a))) if len(a) > 1 and a.std(ddof=1) > 0 else np.nan
    return a.mean(), t


def main():
    print(f"price keys: {PRICE_KEYS}")
    print(f"fund keys:  {FUND_KEYS}")
    print(f"registry fund weights: {{{', '.join(f'{k}:{REG[k]}' for k in FUND_KEYS)}}}\n")
    for market in ("KR", "US"):
        path = ROOT / "exports" / f"validation_panel_{market}_v1.parquet"
        if not path.exists():
            print(f"{market}: panel 없음 (composite_decile_backtest --fundamentals 먼저)"); continue
        panel = pd.read_parquet(path)
        print(f"===== {market} (n={len(panel)}, 날짜 {panel['date'].nunique()}) — 가격+펀더 합성 per-date IC =====")
        print(f"  {'가중치세트':16s} {'120d (t)':>16s}   {'250d (t)':>16s}")
        # price-only baseline for reference
        base_w = {k: REG[k] for k in PRICE_KEYS}
        for ret in ("fwd_120", "fwd_250"):
            pass
        pc = composite(panel, {k: (REG[k] if k in PRICE_KEYS else 0.0) for k in ALL_KEYS})
        i12, t12 = per_date_ic(panel, pc, "fwd_120")
        i25, t25 = per_date_ic(panel, pc, "fwd_250")
        print(f"  {'(가격만 참고)':16s} {i12:+.3f} (t{t12:+.1f})   {i25:+.3f} (t{t25:+.1f})")
        for label, fw in FUND_SETS.items():
            w = {**{k: REG[k] for k in PRICE_KEYS}, **fw}
            comp = composite(panel, w)
            i12, t12 = per_date_ic(panel, comp, "fwd_120")
            i25, t25 = per_date_ic(panel, comp, "fwd_250")
            print(f"  {label:16s} {i12:+.3f} (t{t12:+.1f})   {i25:+.3f} (t{t25:+.1f})")
        print()


if __name__ == "__main__":
    main()
