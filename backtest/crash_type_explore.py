#!/usr/bin/env python3
"""Crash-TYPE signals — does *how* a name fell predict the rebound? (2026-09-06, 고도화 #2)

The universe (>=50% below the 5y high) mixes slow multi-year bleeders with names
that lost most of it in weeks. The human layer already reasons in 소멸형 / 정체형 /
이벤트형; the score does not. This measures point-in-time, price-only features of
the drawdown's SHAPE on the saved validation panels and reports per-date IC
(KR clean dates = trustworthy; US = direction), plus whether the best feature adds
to composite_full (incremental IC inside the top half, combined-rank top-N edge)
and a shock-vs-bleed bucket split.

Features from the <=T close slice (pos = index of T):
  ret_20 / ret_60 / ret_120     recent returns (negative = still falling)
  dd_share_60 / dd_share_120    share of the total drawdown (available-history high
                                -> T) realised in the last 60/120 trading days
                                (1.0 = it all happened recently = shock; 0 = bleed)
  days_since_high               trading days since the drawdown's high (capped by history)
  days_since_low52              trading days since the 52-week low
  drop5_max120                  worst 5-day return in the last 120 days (magnitude, %)
  off_lows                      close / 60d low - 1 (reference: known negative IC)

Caveat: KR survivor prices start 2021-04, so for KR 'high' is the highest close in
the available history (1.2~3.5y), not a true 5y high. US has 10y (proper) but is
survivor-only. Recent-return features (ret_*, drop5, dd_share_60) are unaffected.

Usage: python backtest/crash_type_explore.py [--topn 10]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backtest"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from composite_decile_backtest import load_prices, per_date_ic  # noqa: E402

SCORE = "composite_full"
CLEAN_START = {"KR": pd.Timestamp("2022-06-30"), "US": None}
FEATS = ["ret_20", "ret_60", "ret_120", "dd_share_60", "dd_share_120",
         "days_since_high", "days_since_low52", "drop5_max120", "off_lows"]
HORIZONS = (60, 120, 250)


def features(close: np.ndarray, p: int) -> dict:
    last = close[p]
    out: dict = {}

    def back(k):
        return close[p - k] if p - k >= 0 and close[p - k] > 0 else np.nan
    for k in (20, 60, 120):
        b = back(k)
        out[f"ret_{k}"] = (last / b - 1.0) * 100.0 if b == b else np.nan
    lo_i = max(0, p - 1259)
    win = close[lo_i:p + 1]
    ih = int(np.argmax(win))
    hi = float(win[ih])
    out["days_since_high"] = p - (lo_i + ih)
    dd_total = hi - last
    for k in (60, 120):
        b = back(k)
        out[f"dd_share_{k}"] = float(np.clip((b - last) / dd_total, -1.0, 1.0)) if (b == b and dd_total > 0) else np.nan
    lo52_i = max(0, p - 251)
    w52 = close[lo52_i:p + 1]
    out["days_since_low52"] = p - (lo52_i + int(np.argmin(w52)))
    j0 = max(5, p - 119)
    if p >= j0:
        seg = close[j0 - 5:p + 1]
        r5 = seg[5:] / seg[:-5] - 1.0
        out["drop5_max120"] = float(-np.nanmin(r5) * 100.0) if len(r5) else np.nan
    else:
        out["drop5_max120"] = np.nan
    low60 = float(np.min(close[max(0, p - 59):p + 1]))
    out["off_lows"] = (last / low60 - 1.0) * 100.0 if low60 > 0 else np.nan
    return out


def tstat(x) -> float:
    x = pd.Series(x).dropna()
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 1 and x.std(ddof=1) > 0 else float("nan")


def topn_edge(df: pd.DataFrame, score: str, h: int, topn: int) -> tuple[float, float, int]:
    """Date-neutral top-N edge (mean over dates of top-N mean minus cohort mean)."""
    e = []
    for _, g in df.groupby("date"):
        g = g.dropna(subset=[score, f"fwd_{h}"])
        if len(g) < topn * 2:
            continue
        top = g.sort_values(score, ascending=False).head(topn)
        e.append(top[f"fwd_{h}"].mean() - g[f"fwd_{h}"].mean())
    s = pd.Series(e)
    return float(s.mean()), tstat(s), len(s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topn", type=int, default=10)
    args = ap.parse_args()
    lines: list[str] = []

    def emit(s=""):
        print(s, flush=True)
        lines.append(s)

    emit("# 실험 — 폭락 유형(모양) 신호 (2026-09-06, point-in-time)")
    emit("")
    emit("_패널: validation_panel_*_v1. 특징은 T 이하 종가만으로 계산. per-date IC = 날짜별 횡단면 Spearman(특징, 이후 수익)의 평균, |t|≳2 유의. "
         "도구: `backtest/crash_type_explore.py`._")
    emit("> KR은 클린 날짜(2022-06-30~, 11개)만 사용(그 전은 상폐-only 코호트). KR 'high'는 가용 이력 내 최고가(5y 아님) — days_since_high·dd_share_120은 KR서 잘린 값. "
         "US는 10y 시세(모양 특징 정확)이나 생존자-only.")
    emit("")

    for market in ("KR", "US"):
        panel = pd.read_parquet(ROOT / "exports" / f"validation_panel_{market}_v1.parquet")
        panel["date"] = pd.to_datetime(panel["date"])
        if CLEAN_START[market] is not None:
            panel = panel[panel["date"] >= CLEAN_START[market]].copy()
        df_l, delisted = load_prices(market)
        arrs = {}
        for tk, g in df_l.groupby("ticker", sort=False):
            g = g.sort_values("date")
            arrs[tk] = g["adj_close"].to_numpy(float)
        recs, miss = [], 0
        for r in panel.itertuples(index=False):
            a = arrs.get(r.ticker)
            if a is None or int(r.pos) >= len(a):
                miss += 1
                continue
            row = {"date": r.date, "ticker": r.ticker, SCORE: getattr(r, SCORE),
                   "fwd_60": r.fwd_60, "fwd_120": r.fwd_120, "fwd_250": r.fwd_250}
            row.update(features(a, int(r.pos)))
            recs.append(row)
        df = pd.DataFrame(recs)
        emit(f"## {market}  (n={len(df)}, 날짜 {df['date'].nunique()}, 시세 누락 {miss})")
        emit("")
        emit("### 1. 특징별 per-date IC (양수 = 값이 클수록 이후 수익↑)")
        emit("")
        emit("| 특징 | 60d IC (t, +날짜) | 120d IC (t, +날짜) | 250d IC (t, +날짜) | 중앙값 |")
        emit("|---|---:|---:|---:|---:|")
        best = []
        for f in FEATS:
            cells = []
            for h in HORIZONS:
                ic, t, pos, nd = per_date_ic(df, f, f"fwd_{h}")
                cells.append(f"{ic:+.3f} (t{t:+.1f}, {pos:.0%})")
                if h == 120:
                    best.append((abs(t) if t == t else 0.0, f, t))
            emit(f"| {f} | " + " | ".join(cells) + f" | {df[f].median():+.1f} |")
        emit("")

        # baseline score IC / edge for reference
        emit("### 2. 점수 대비 증분 — 최상위 |t| 특징 2개 (120d 기준)")
        emit("")
        bic, bt, _, _ = per_date_ic(df, SCORE, "fwd_120")
        bedge, bedge_t, nd = topn_edge(df, SCORE, 120, args.topn)
        emit(f"- 기준 `{SCORE}`: 120d IC {bic:+.3f} (t{bt:+.1f}) · 상위{args.topn} 날짜중립 엣지 {bedge:+.1f}%p (t{bedge_t:+.1f}, {nd}날짜)")
        best.sort(reverse=True)
        for _, f, t in best[:2]:
            if t != t:
                continue
            sign = 1.0 if t > 0 else -1.0
            # (a) IC inside the score's top half
            half = df[df.groupby("date")[SCORE].rank(pct=True) >= 0.5]
            ic_h, t_h, pos_h, _ = per_date_ic(half, f, "fwd_120")
            # (b) combined rank: score rank + sign*feature rank (equal weight), and 2:1
            df["_rs"] = df.groupby("date")[SCORE].rank(pct=True)
            df["_rf"] = df.groupby("date")[f].rank(pct=True) * sign
            df["_comb11"] = df["_rs"] + df["_rf"]
            df["_comb21"] = 2 * df["_rs"] + df["_rf"]
            c11, c11t, _, _ = per_date_ic(df, "_comb11", "fwd_120")
            c21, c21t, _, _ = per_date_ic(df, "_comb21", "fwd_120")
            e11, e11t, _ = topn_edge(df, "_comb11", 120, args.topn)
            e21, e21t, _ = topn_edge(df, "_comb21", 120, args.topn)
            e250b, _, _ = topn_edge(df, SCORE, 250, args.topn)
            e250c, _, _ = topn_edge(df, "_comb21", 250, args.topn)
            emit(f"- **{f}** (부호 {'+' if sign > 0 else '−'}): 점수 상위 절반 내 IC {ic_h:+.3f} (t{t_h:+.1f}, +날짜 {pos_h:.0%}) · "
                 f"결합 랭크 1:1 IC {c11:+.3f} (t{c11t:+.1f}) / 2:1 IC {c21:+.3f} (t{c21t:+.1f}) · "
                 f"상위{args.topn} 엣지 120d: 기준 {bedge:+.1f} → 1:1 {e11:+.1f} (t{e11t:+.1f}) / 2:1 {e21:+.1f} (t{e21t:+.1f}) · "
                 f"250d: 기준 {e250b:+.1f} → 2:1 {e250c:+.1f}")
        emit("")

        # shock vs bleed bucket
        emit("### 3. 충격형 vs 출혈형 (dd_share_60 ≥ 0.5 = 낙폭의 절반 이상이 최근 60일)")
        emit("")
        emit(f"| 버킷 | n | 코호트 120d 평균 (승률) | 코호트 250d 평균 | 상위{args.topn} 엣지 120d (날짜) |")
        emit("|---|---:|---:|---:|---:|")
        for nm, sub in (("충격형 (≥0.5)", df[df["dd_share_60"] >= 0.5]), ("혼합 (0.2~0.5)", df[(df["dd_share_60"] >= 0.2) & (df["dd_share_60"] < 0.5)]),
                        ("출혈형 (<0.2)", df[df["dd_share_60"] < 0.2])):
            if len(sub) == 0:
                continue
            e, et, nd = topn_edge(sub, SCORE, 120, args.topn)
            emit(f"| {nm} | {len(sub)} | {sub['fwd_120'].mean():+.1f}% ({(sub['fwd_120'] > 0).mean():.0%}) | {sub['fwd_250'].mean():+.1f}% | "
                 f"{e:+.1f}%p (t{et:+.1f}, {nd}) |" if nd else f"| {nm} | {len(sub)} | {sub['fwd_120'].mean():+.1f}% ({(sub['fwd_120'] > 0).mean():.0%}) | {sub['fwd_250'].mean():+.1f}% | — |")
        emit("")

    emit("## 읽는 법")
    emit("- 1표에서 KR(클린) |t|≳2이고 US 부호가 같으면 '모양'에 정보가 있다. 부호가 음수인 특징(예: 값이 클수록 나쁨)은 반대로 쓰면 된다.")
    emit("- 2절이 핵심: 점수 상위 절반 **안에서도** IC가 살아 있고 결합 랭크의 상위N 엣지가 기준보다 크면 점수에 넣을 가치가 있다. 상위 절반 내 IC가 0이면 점수가 이미 흡수한 정보다.")
    emit("- 3절은 유니버스 정의의 문제: 버킷 간 코호트 수익이 크게 다르면 '유형'을 게이트로 쓸 근거, 엣지가 한 버킷에만 있으면 그 버킷에 집중할 근거.")
    emit("- 운영 반영은 10/10 분기 리뷰에서만.")
    out = ROOT / "docs" / "experiment-crash-type-2026-09-06.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
