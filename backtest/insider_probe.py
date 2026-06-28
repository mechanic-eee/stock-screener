#!/usr/bin/env python3
"""Probe: does insider OPEN-MARKET BUYING predict recovery? (SEC Form 4, US, scoped)

Insiders buying their own crashed stock with their own cash is a classic recovery
tell. This is a SCOPED feasibility+signal test (not the full cohort — Form 4 for
all 18k rows = ~50k fetches). For a sample of cohort (ticker, T) rows it counts
open-market purchases (transactionCode P) filed in [T-90, T] and compares forward
returns of names WITH vs WITHOUT insider buying, plus a pooled IC. If the buy
group clearly outperforms, the full live signal + a fuller validation is justified.

Key efficiency: filter Form 4s to the window FIRST (via the submissions filing
dates), then fetch only the few in-window XMLs.

Usage: python backtest/insider_probe.py [--dates 6 --per-date 60]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backtest"))
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import edgar_pit as E  # noqa: E402  (UA + CIK map)

UA = {"User-Agent": E.UA}
CACHE = ROOT / "exports" / "edgar_cache" / "_form4"


def _get(url: str) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()


def _submissions(cik: str):
    fp = CACHE / f"sub_{cik}.json"
    CACHE.mkdir(parents=True, exist_ok=True)
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            pass
    try:
        data = _get(f"https://data.sec.gov/submissions/CIK{cik}.json")
        time.sleep(0.11)
        fp.write_bytes(data)
        return json.loads(data)
    except Exception:
        return None


def insider_buys(cik: str, T: pd.Timestamp, window_days: int = 90) -> float | None:
    """Count open-market purchase (P) transactions in Form 4s filed in [T-w, T].

    None if no submissions data (e.g., foreign filer with no Form 4)."""
    import re
    sub = _submissions(cik)
    if not sub:
        return None
    r = sub["filings"]["recent"]
    lo = (T - pd.Timedelta(days=window_days)).strftime("%Y-%m-%d")
    hi = T.strftime("%Y-%m-%d")
    idx = [i for i, f in enumerate(r["form"]) if f == "4" and lo <= r["filingDate"][i] <= hi]
    if not idx:
        return 0.0
    buys = 0
    for i in idx:
        acc = r["accessionNumber"][i].replace("-", "")
        raw_doc = r["primaryDocument"][i].split("/")[-1]
        fp = CACHE / f"f4_{acc}.xml"
        try:
            if fp.exists():
                raw = fp.read_text(encoding="utf-8", errors="ignore")
            else:
                raw = _get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{raw_doc}"
                           ).decode("utf-8", "ignore")
                time.sleep(0.11)
                fp.write_text(raw, encoding="utf-8")
        except Exception:
            continue
        buys += raw.count("<transactionCode>P</transactionCode>")
    return float(buys)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dates", type=int, default=6, help="가장 최근 N개 리밸런스 날짜 샘플")
    ap.add_argument("--per-date", type=int, default=60, help="날짜당 최대 종목 수(점수 상위)")
    args = ap.parse_args()

    panel = pd.read_parquet(ROOT / "exports" / "validation_panel_US_v1.parquet")
    panel["date"] = pd.to_datetime(panel["date"])
    cmap = E.load_cik_map()
    dates = sorted(panel["date"].unique())[-args.dates:]
    sample = []
    for d in dates:
        g = panel[panel["date"] == d].sort_values("composite_full", ascending=False).head(args.per_date)
        sample.append(g)
    sample = pd.concat(sample, ignore_index=True)
    print(f"표본: {len(sample)}행 · {len(dates)}날짜 · Form4 조회 중...", flush=True)

    rows = []
    for k, r in enumerate(sample.itertuples(index=False), 1):
        cik = cmap.get(str(r.ticker).upper())
        nb = insider_buys(cik, pd.Timestamp(r.date)) if cik else None
        rows.append({"date": r.date, "ticker": r.ticker, "buys": nb,
                     "fwd_120": r.fwd_120, "fwd_250": r.fwd_250})
        if k % 60 == 0:
            print(f"  {k}/{len(sample)}", flush=True)
    df = pd.DataFrame(rows)
    have = df["buys"].notna()
    print(f"\nForm4 데이터 있는 행: {have.sum()}/{len(df)} "
          f"(매수>0인 행: {(df['buys'] > 0).sum()})")

    # buy vs no-buy forward returns
    for h in (120, 250):
        col = f"fwd_{h}"
        buy = df[(df["buys"] > 0)][col].dropna()
        nobuy = df[(df["buys"] == 0)][col].dropna()
        if len(buy) >= 5 and len(nobuy) >= 5:
            print(f"  {h}d: 내부자매수有 {buy.mean():+.1f}% (n{len(buy)}) vs 無 "
                  f"{nobuy.mean():+.1f}% (n{len(nobuy)}) → 차이 {buy.mean()-nobuy.mean():+.1f}%p")
        else:
            print(f"  {h}d: 표본 부족 (有 {len(buy)}, 無 {len(nobuy)})")
    # pooled IC of buy-count vs forward return
    s = df[have][["buys", "fwd_250"]].dropna()
    if len(s) >= 20 and s["buys"].nunique() > 1:
        ic = s["buys"].rank().corr(s["fwd_250"].rank())
        print(f"  pooled IC(매수건수, 250d): {ic:+.3f} (n{len(s)})")
    print("\n해석: 매수有 그룹이 뚜렷이 높으면 → 라이브 신호화 + 본검증 정당. 차이 없으면 → 보류.")


if __name__ == "__main__":
    main()
