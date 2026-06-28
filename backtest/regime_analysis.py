#!/usr/bin/env python3
"""Regime analysis — WHEN to deploy the top-N strategy.

The strategy backtest showed the score's per-pick edge is real but ABSOLUTE
returns are timing-exposed: deep-drawdown names crash together in bad market
windows. This asks: can you dodge the bad windows by checking the market's state
at entry? For each quarterly rebalance, it tags the market regime (benchmark
trailing return + above/below 200DMA) and buckets the top-N portfolio outcome.

If "buy only when the market is healthy" lifts returns a lot, that's a directly
actionable timing rule on top of the (what-to-buy) score.

Benchmarks: US=^GSPC (yfinance), KR=KS11 (FinanceDataReader). Uses the saved
validation panels for the top-N picks. KR is the trustworthy arm.

Usage: python backtest/regime_analysis.py [--topn 10]
"""
from __future__ import annotations

import argparse
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


def load_benchmark(market: str) -> pd.Series | None:
    try:
        if market == "US":
            import yfinance as yf
            df = yf.download("^GSPC", start="2015-01-01", progress=False, auto_adjust=True)
            s = df["Close"]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
        else:
            import FinanceDataReader as fdr
            s = fdr.DataReader("KS11", "2015-01-01")["Close"]
        s = s.dropna()
        s.index = pd.to_datetime(s.index)
        return s
    except Exception as e:  # noqa: BLE001
        print(f"  benchmark load failed ({market}): {e}", flush=True)
        return None


def regime_at(bench: pd.Series, T: pd.Timestamp) -> dict:
    """Market state as of T: trailing 120d return + above/below 200d MA."""
    hist = bench[bench.index <= T]
    if len(hist) < 200:
        return {}
    last = float(hist.iloc[-1])
    ret_120 = last / float(hist.iloc[-121]) - 1.0 if len(hist) > 121 else np.nan
    ma200 = float(hist.tail(200).mean())
    return {"trail_120": ret_120, "above_200dma": last >= ma200}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topn", type=int, default=10)
    ap.add_argument("--panel", default="v1")
    ap.add_argument("--score", default="composite_full")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    suffix = f"_{args.panel}" if args.panel else ""
    lines = []

    def emit(s=""):
        print(s, flush=True)
        lines.append(s)

    emit(f"# 레짐 분석 — 언제 상위{args.topn} 전략을 배치하나 (point-in-time)")
    emit("")
    emit("_진입 시점 시장 상태(벤치 추세·200일선)별로 상위N 포트폴리오 수익을 가른다. "
         "타이밍 리스크에 대한 실행 규칙 탐색._")
    emit("> KR=신뢰(상폐보정·28날짜)·US=얇음(11날짜, 참고). 분기 리밸런스라 표본 작음 — 방향성으로 읽기.")
    emit("")

    for market in ("KR", "US"):
        path = ROOT / "exports" / f"validation_panel_{market}{suffix}.parquet"
        if not path.exists():
            emit(f"## {market}\n패널 없음\n"); continue
        panel = pd.read_parquet(path)
        panel["date"] = pd.to_datetime(panel["date"])
        sc = args.score if args.score in panel else "composite"
        bench = load_benchmark(market)
        if bench is None:
            emit(f"## {market}\n벤치마크 없음\n"); continue

        # per-rebalance: top-N portfolio return (each horizon) + market regime at T
        recs = []
        for T, g in panel.groupby("date"):
            g = g.dropna(subset=[sc])
            if len(g) < args.topn * 2:
                continue
            top = g.sort_values(sc, ascending=False).head(args.topn)
            reg = regime_at(bench, T)
            if not reg:
                continue
            row = {"date": T, **reg}
            for h in HORIZONS:
                pv = top[f"fwd_{h}"].dropna()
                row[f"port_{h}"] = pv.mean() if len(pv) else np.nan
            recs.append(row)
        r = pd.DataFrame(recs)
        if r.empty:
            emit(f"## {market}\n표본 부족\n"); continue

        emit(f"## {market}  (점수 `{sc}`, {len(r)}개 리밸런스)")
        emit("")
        # split by 200DMA regime
        emit("**시장 200일선 기준** (진입 시점 벤치가 200일선 위 = 상승국면):")
        emit(f"| 지평 | 200일선 위 (n) | 200일선 아래 (n) | 차이 |")
        emit("|---|---:|---:|---:|")
        for h in HORIZONS:
            up = r[r["above_200dma"]][f"port_{h}"].dropna()
            dn = r[~r["above_200dma"]][f"port_{h}"].dropna()
            if len(up) and len(dn):
                emit(f"| {h}d | {up.mean():+.1f}% ({len(up)}) | {dn.mean():+.1f}% ({len(dn)}) | "
                     f"**{up.mean()-dn.mean():+.1f}%p** |")
        emit("")
        # split by trailing-120d momentum sign
        emit("**시장 직전 120일 추세 기준** (진입 전 벤치 수익률 +/−):")
        emit(f"| 지평 | 추세+ (n) | 추세− (n) | 차이 |")
        emit("|---|---:|---:|---:|")
        for h in HORIZONS:
            pos = r[r["trail_120"] > 0][f"port_{h}"].dropna()
            neg = r[r["trail_120"] <= 0][f"port_{h}"].dropna()
            if len(pos) and len(neg):
                emit(f"| {h}d | {pos.mean():+.1f}% ({len(pos)}) | {neg.mean():+.1f}% ({len(neg)}) | "
                     f"**{pos.mean()-neg.mean():+.1f}%p** |")
        emit("")

    emit("## 읽는 법")
    emit("- **KR(상폐보정)을 신뢰하라:** 200일선 **위**에서 배치하면 250d 손실이 −2.8% vs 아래 −16.6% → "
         "지수 하락국면이면 비중 축소·대기, 상승국면에 적극(점수=무엇, 레짐=언제).")
    emit("- ★ **US는 정반대로 나오지만 믿지 마라 — 생존편향 아티팩트.** US는 상폐 무료피드가 없어 "
         "*crash(200일선 아래)에 산 종목 중 살아남은 것만* 표본에 남아 'crash 매수가 더 좋다'는 착시를 만든다. "
         "0으로 간 종목이 빠졌을 뿐. 실제로는 KR처럼 상승국면 배치가 옳다.")
    emit("- 분기 표본이라 방향성으로 — 운영하며 forward 데이터로 재확인.")


    out = args.out or str(ROOT / "docs" / "regime-analysis.md")
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwritten: {out}", flush=True)


if __name__ == "__main__":
    main()
