#!/usr/bin/env python3
"""Gate threshold calibration backtest (ported from predecessor project).

Tunes the three base/gate thresholds against historical data by measuring
forward returns (30/90/180 trading days) of stocks that passed the gates:

    min_drawdown_pct   (price gate)
    macd_window_days   (momentum gate)
    volume_multiplier  (volume gate)

Enrichment-stage scorers (news/fundamentals) are intentionally excluded — they
need operational data and are calibrated later from production telemetry.

Usage:
    python backtest/calibrate_gates.py --synthetic --output report.md
    python backtest/calibrate_gates.py --data exports/prices_us.parquet --output calib_us.md
    python backtest/calibrate_gates.py --data exports/prices_kr.parquet --protocol grid
"""
import argparse
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

DEFAULT_PARAMS = {
    "min_drawdown_pct": 50,
    "macd_window_days": 3,
    "volume_multiplier": 1.5,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "volume_ma_window": 20,
    "lookback_years": 5,
}

OFAT_VARIATIONS = {
    "min_drawdown_pct": [30, 40, 50, 60, 70],
    "macd_window_days": [1, 2, 3, 5, 7],
    "volume_multiplier": [1.0, 1.25, 1.5, 2.0, 3.0],
}

FORWARD_HORIZONS = [30, 90, 180]


def compute_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line


def compute_drawdown(close, lookback_days):
    rolling_max = close.rolling(lookback_days, min_periods=250).max()
    return (close - rolling_max) / rolling_max * 100


def compute_volume_ratio(volume, ma_window=20):
    vol_ma = volume.shift(1).rolling(ma_window).mean()
    return volume / vol_ma


def find_gate_signals(group: pd.DataFrame, params: Dict) -> pd.DataFrame:
    if len(group) < 250:
        return pd.DataFrame()
    close = group["adj_close"]
    volume = group["volume"]
    macd, signal_line = compute_macd(close, params["macd_fast"], params["macd_slow"], params["macd_signal"])
    drawdown = compute_drawdown(close, params["lookback_years"] * 252)
    vol_ratio = compute_volume_ratio(volume, params["volume_ma_window"])

    macd_zc = (macd > 0) & (macd.shift(1) <= 0)
    macd_diff = macd - signal_line
    macd_sc = (macd_diff > 0) & (macd_diff.shift(1) <= 0)

    window = params["macd_window_days"]
    rows = []
    for i in range(window, len(group)):
        d = drawdown.iloc[i]
        if pd.isna(d) or d > -params["min_drawdown_pct"]:
            continue
        lo = max(0, i - window + 1)
        hi = i + 1
        zc_in = macd_zc.iloc[lo:hi].any()
        sc_in = macd_sc.iloc[lo:hi].any()
        if not (zc_in or sc_in):
            continue
        zc_idx = sc_idx = -1
        for j in range(i, lo - 1, -1):
            if macd_zc.iloc[j] and zc_idx < 0:
                zc_idx = j
            if macd_sc.iloc[j] and sc_idx < 0:
                sc_idx = j
        if zc_idx >= sc_idx:
            signal_idx = zc_idx if zc_idx >= 0 else sc_idx
        else:
            signal_idx = sc_idx
        signal_type = "zero_cross" if (zc_idx == signal_idx) else "signal_cross"
        v = vol_ratio.iloc[signal_idx]
        if pd.isna(v) or v < params["volume_multiplier"]:
            continue
        rows.append({
            "signal_date": group["date"].iloc[i],
            "today_idx": i,
            "macd_signal_type": signal_type,
            "macd_signal_age_days": i - signal_idx,
            "drawdown_pct": d,
            "volume_ratio": v,
            "close_at_signal": close.iloc[i],
        })
    return pd.DataFrame(rows)


def add_forward_returns(signals, group, horizons):
    if len(signals) == 0:
        return signals
    close = group["adj_close"].values
    n = len(close)
    for h in horizons:
        rets = []
        for idx in signals["today_idx"]:
            j = int(idx) + h
            rets.append((close[j] - close[idx]) / close[idx] * 100 if j < n else np.nan)
        signals[f"fwd_{h}d_pct"] = rets
    return signals


def run_backtest(prices, params, horizons=None):
    if horizons is None:
        horizons = FORWARD_HORIZONS
    out = []
    for ticker, group in prices.groupby("ticker", sort=False):
        group = group.sort_values("date").reset_index(drop=True)
        sigs = find_gate_signals(group, params)
        if len(sigs) > 0:
            sigs["ticker"] = ticker
            sigs = add_forward_returns(sigs, group, horizons)
            out.append(sigs)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def ofat_calibration(prices, base, variations):
    results = [(dict(base), run_backtest(prices, base))]
    for name, values in variations.items():
        for v in values:
            if v == base[name]:
                continue
            params = dict(base)
            params[name] = v
            print(f"  {name}={v} ...", flush=True)
            results.append((params, run_backtest(prices, params)))
    return results


def grid_search(prices, base, grid):
    keys = list(grid.keys())
    results = []
    for combo in product(*[grid[k] for k in keys]):
        params = dict(base)
        params.update(dict(zip(keys, combo)))
        print(f"  {dict(zip(keys, combo))} ...", flush=True)
        results.append((params, run_backtest(prices, params)))
    return results


def summarize(signals, horizons=None):
    if horizons is None:
        horizons = FORWARD_HORIZONS
    s = {"n_signals": len(signals)}
    if len(signals) == 0:
        return s
    if "signal_date" in signals.columns:
        sd = pd.to_datetime(signals["signal_date"])
        months = max(1, (sd.max() - sd.min()).days / 30.44)
        s["per_month"] = len(signals) / months
    for h in horizons:
        col = f"fwd_{h}d_pct"
        if col not in signals.columns:
            continue
        v = signals[col].dropna()
        if len(v) == 0:
            continue
        s[f"mean_{h}"] = v.mean()
        s[f"win_{h}"] = (v > 0).mean()
        s[f"sharpe_{h}"] = v.mean() / v.std() if v.std() > 0 else 0.0
    return s


def make_report(results, output_path, base_params, dataset_label):
    lines = ["# 게이트 캘리브레이션 결과", "",
             f"_생성: {datetime.now().isoformat(timespec='seconds')}_",
             f"_데이터: {dataset_label}_", ""]
    summaries = [(p, summarize(sigs)) for p, sigs in results]
    lines += ["## 1. 전체 비교표", "",
              "| 변동 | 값 | 신호수 | 월평균 | 90d 평균 | 90d 승률 | 90d Sharpe |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for params, s in summaries:
        diff = next((k for k in params if k in base_params and params[k] != base_params[k]), None)
        label = "base" if diff is None else diff
        value = "—" if diff is None else str(params[diff])
        lines.append(
            f"| {label} | {value} | {s['n_signals']} | "
            f"{s.get('per_month', float('nan')):.1f} | "
            f"{s.get('mean_90', float('nan')):+.2f}% | "
            f"{s.get('win_90', 0):.0%} | {s.get('sharpe_90', 0):.2f} |"
        )
    lines += ["", "## 2. 해석 가이드", "",
              "- **월평균 신호수**: 시장당 일 10~30건 통과를 목표. 너무 많으면 비용, 너무 적으면 알림이 없음.",
              "- **90d 승률**: 50% 미만이면 평균이 양수여도 운영 부담.",
              "- **Sharpe(mean/std)**: 같은 평균이면 변동성 작은 쪽이 낫다.",
              "- 보수적 임계치(깊은 하락·짧은 MACD윈도우·높은 거래량배수)는 신호수↓ 대신 승률·Sharpe↑.", ""]
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def generate_synthetic_universe(n_stocks=100, n_years=7, seed=42):
    rng = np.random.default_rng(seed)
    n_days = n_years * 252
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n_days)
    parts = []
    for i in range(n_stocks):
        start = rng.uniform(10, 200)
        log_returns = rng.normal(rng.uniform(-0.10, 0.20) / 252,
                                 rng.uniform(0.20, 0.60) / np.sqrt(252), n_days)
        if rng.random() < 0.5:
            for _ in range(rng.integers(1, 3)):
                cs = int(rng.integers(252, n_days - 252))
                cd = int(rng.integers(20, 80))
                cv = rng.uniform(0.30, 0.70)
                log_returns[cs:cs + cd] -= -np.log(1 - cv) / cd
                if rng.random() < 0.6:
                    rs = cs + cd + int(rng.integers(20, 100))
                    rd = int(rng.integers(60, 250))
                    if rs + rd < n_days:
                        log_returns[rs:rs + rd] += np.log(1 + rng.uniform(0.30, 0.80) * cv) / rd
        prices = start * np.exp(np.cumsum(log_returns))
        base_vol = rng.uniform(100_000, 5_000_000)
        rmag = np.abs(log_returns)
        vfactor = np.clip(1 + 5 * (rmag - rmag.mean()) / max(rmag.std(), 1e-9), 0.2, 10.0)
        parts.append(pd.DataFrame({
            "ticker": f"SYN{i:04d}", "date": dates,
            "adj_close": prices, "volume": (base_vol * vfactor).astype(int),
        }))
    return pd.concat(parts, ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--data", help="Parquet with [ticker, date, adj_close, volume]")
    src.add_argument("--synthetic", action="store_true")
    ap.add_argument("--output", default="calibration_report.md")
    ap.add_argument("--protocol", choices=["ofat", "grid"], default="ofat")
    ap.add_argument("--n-stocks", type=int, default=200)
    ap.add_argument("--n-years", type=int, default=7)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if args.synthetic:
        print(f"[synthetic] {args.n_stocks} stocks x {args.n_years} years (seed={args.seed})")
        prices = generate_synthetic_universe(args.n_stocks, args.n_years, args.seed)
        label = f"synthetic ({args.n_stocks} stocks x {args.n_years} years)"
    else:
        prices = pd.read_parquet(args.data)
        prices["date"] = pd.to_datetime(prices["date"])
        label = args.data

    print(f"Universe: {prices['ticker'].nunique()} tickers, {len(prices):,} rows, "
          f"{prices['date'].min().date()} -> {prices['date'].max().date()}")
    print(f"Protocol: {args.protocol}")
    if args.protocol == "ofat":
        results = ofat_calibration(prices, DEFAULT_PARAMS, OFAT_VARIATIONS)
    else:
        results = grid_search(prices, DEFAULT_PARAMS, {
            "min_drawdown_pct": [40, 50, 60],
            "macd_window_days": [1, 3, 5],
            "volume_multiplier": [1.25, 1.5, 2.0],
        })
    print(f"Writing report to {args.output} ...")
    make_report(results, args.output, DEFAULT_PARAMS, label)
    print("Done.")


if __name__ == "__main__":
    main()
