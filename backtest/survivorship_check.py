"""Survivorship-bias check (KR): how much do delisted names change the picture?

Runs the base gate on survivors-only vs survivors+delisted, with the production
liquidity floor. Forward returns are *delisting-aware*: a delisted name is held
to its last traded price (the delisting/bankruptcy outcome — often near zero),
while a survivor's beyond-data horizon stays NaN (genuinely unknown future).

Usage: python backtest/survivorship_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backtest"))
import calibrate_gates as cg  # noqa: E402

# KR production liquidity floor (matches engine.LIQUIDITY_FLOORS["KR"])
KR_FLOOR_TURNOVER, KR_FLOOR_PRICE = 500_000_000, 1000


def fwd_returns(signals, group, horizons, is_delisted):
    if len(signals) == 0:
        return signals
    close = group["adj_close"].values
    n = len(close)
    for h in horizons:
        rets = []
        for idx in signals["today_idx"]:
            idx = int(idx)
            j = idx + h
            if j < n:
                rets.append((close[j] - close[idx]) / close[idx] * 100)
            elif is_delisted:
                rets.append((close[-1] - close[idx]) / close[idx] * 100)  # held to delisting
            else:
                rets.append(np.nan)
        signals[f"fwd_{h}d_pct"] = rets
    return signals


def run(prices, delisted_set, params):
    out = []
    for ticker, g in prices.groupby("ticker", sort=False):
        g = g.sort_values("date").reset_index(drop=True)
        sigs = cg.find_gate_signals(g, params)
        if len(sigs) > 0:
            sigs["ticker"] = ticker
            sigs = fwd_returns(sigs, g, cg.FORWARD_HORIZONS, ticker in delisted_set)
            out.append(sigs)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def fmt(label, s):
    return (f"{label}: 신호 {s['n_signals']}, "
            f"90d평균 {s.get('mean_90', float('nan')):+.1f}%, "
            f"승률 {s.get('win_90', 0):.0%}, Sharpe {s.get('sharpe_90', 0):.3f}")


def main() -> int:
    surv = pd.read_parquet(ROOT / "exports" / "prices_kr.parquet")
    surv["date"] = pd.to_datetime(surv["date"])
    dpath = ROOT / "exports" / "prices_kr_delisted.parquet"
    if not dpath.exists():
        print("run fetch_delisted_kr.py first", file=sys.stderr)
        return 1
    deli = pd.read_parquet(dpath)
    deli["date"] = pd.to_datetime(deli["date"])
    delisted_set = set(deli["ticker"].unique())
    combined = pd.concat([surv[["ticker", "date", "adj_close", "volume"]],
                          deli[["ticker", "date", "adj_close", "volume"]]], ignore_index=True)

    params = dict(cg.DEFAULT_PARAMS)
    params["min_turnover"] = KR_FLOOR_TURNOVER
    params["min_price"] = KR_FLOOR_PRICE

    print(f"survivors {surv['ticker'].nunique()} + delisted {len(delisted_set)} tickers "
          f"(liquidity floor on)", flush=True)
    sig_surv = run(surv, set(), params)
    sig_comb = run(combined, delisted_set, params)
    print(fmt("생존자-only      ", cg.summarize(sig_surv)))
    print(fmt("생존자+상폐 보정  ", cg.summarize(sig_comb)))

    # how much came from delisted names, and how badly they did
    if not sig_comb.empty:
        d = sig_comb[sig_comb["ticker"].isin(delisted_set)]
        v = d["fwd_90d_pct"].dropna()
        print(f"  └ 상폐종목 신호 {len(d)}건 ({len(d)/len(sig_comb):.0%}), "
              f"그 90d평균 {v.mean():+.1f}% / 승률 {(v>0).mean():.0%}" if len(v) else "  └ 상폐 신호 없음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
