#!/usr/bin/env python3
"""Holding horizon / rotation / regime-exit experiment (2026-09-06, 시스템-평가 고도화 #1).

Question: the score's date-neutral edge is strongest at 60~120d and decays by
250d (strategy-backtest-top10). Does a shorter hold + rotation into the then-current
top-N harvest more of it per year? And does a mid-hold regime exit (benchmark
below its 200DMA) cut the absolute-return damage that timing risk causes?

Three tests, all point-in-time on the saved validation panels (score + forward
returns computed by composite_decile_backtest.py; no re-scoring):

  A. Chained rotation (no daily data needed):
       HOLD250  = top-N fwd_250 at T_k
       ROT120   = (1+top-N fwd_120 at T_k) x (1+top-N fwd_120 at T_{k+2}) - 1
       ROT60    = product over j=0..3 of (1+top-N fwd_60 at T_{k+j}) - 1
     gross and net of round-trip cost (1x / 2x / 4x), plus the date-neutral
     version (top-N minus that date's cohort, summed per leg) and a regime-gated
     version (a leg whose start date is below the benchmark 200DMA earns 0 = cash).
  B. Daily regime exit inside the hold (daily prices, delisted held to last):
       B0 hold 250d | B1 exit first day benchmark < 200DMA | B2 same but only
       after 60d minimum hold | B4 exit on regime-off only if the position is
       under water (keep winners).
  H. Panel hygiene — discovered while building this: KR rebalance dates before
     2022-06-30 are 100% delisted-only cohorts (survivor prices start 2021-04 and
     MIN_HISTORY=252 pushes survivors' first eligible date to 2022-06). Every KR
     statistic below is therefore reported on the CLEAN dates (>= 2022-06-30)
     and the earlier delisted-only dates are shown separately, not pooled.

Usage: python backtest/holding_rotation_experiment.py [--topn 10]
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

from regime_analysis import load_benchmark, regime_at  # noqa: E402
from composite_decile_backtest import load_prices, per_date_ic  # noqa: E402

SCORE = "composite_full"
COST_RT = {"KR": 0.30, "US": 0.45}          # round-trip cost %, recommendation-design 비용 모델
CLEAN_START = {"KR": pd.Timestamp("2022-06-30"), "US": None}


# --------------------------------------------------------------------------- helpers
def load_panel(market: str) -> pd.DataFrame:
    p = pd.read_parquet(ROOT / "exports" / f"validation_panel_{market}_v1.parquet")
    p["date"] = pd.to_datetime(p["date"])
    return p


def topn_table(panel: pd.DataFrame, topn: int) -> pd.DataFrame:
    """Per rebalance date: top-N mean fwd (60/120/250), cohort mean fwd, n."""
    rows = []
    for T, g in panel.groupby("date"):
        g = g.dropna(subset=[SCORE])
        if len(g) < topn * 2:
            continue
        top = g.sort_values(SCORE, ascending=False).head(topn)
        rec = {"date": T, "n": len(g)}
        for h in (60, 120, 250):
            rec[f"top_{h}"] = top[f"fwd_{h}"].mean()
            rec[f"all_{h}"] = g[f"fwd_{h}"].mean()
        rows.append(rec)
    return pd.DataFrame(rows).set_index("date").sort_index()


def chain(legs: list[float]) -> float:
    out = 1.0
    for r in legs:
        out *= 1.0 + r / 100.0
    return (out - 1.0) * 100.0


def tstat(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 1 and x.std(ddof=1) > 0 else float("nan")


def stats_line(name: str, s: pd.Series, ref: pd.Series | None = None) -> str:
    s = s.dropna()
    if s.empty:
        return f"| {name} | — | — | — | — | — |"
    diff = ""
    if ref is not None:
        d = (s - ref).dropna()
        diff = f"{d.mean():+.1f}%p (t{tstat(d):+.1f}, {(d > 0).mean():.0%} 승)"
    return (f"| {name} | {s.mean():+.1f}% | {s.median():+.1f}% | {(s > 0).mean():.0%} | "
            f"{s.min():+.1f}% | {diff or '기준'} |")


# --------------------------------------------------------------------------- Test A
def test_a(tbl: pd.DataFrame, bench: pd.Series | None, cost: float) -> pd.DataFrame:
    dates = list(tbl.index)
    above = {T: (regime_at(bench, T).get("above_200dma") if bench is not None else None) for T in dates}
    rows = []
    for k, T in enumerate(dates):
        if k + 3 >= len(dates):
            break
        L60 = [dates[k + j] for j in range(4)]
        L120 = [dates[k], dates[k + 2]]
        top60 = [tbl.loc[d, "top_60"] for d in L60]
        top120 = [tbl.loc[d, "top_120"] for d in L120]
        all60 = [tbl.loc[d, "all_60"] for d in L60]
        all120 = [tbl.loc[d, "all_120"] for d in L120]
        if any(pd.isna(v) for v in top60 + top120 + [tbl.loc[T, "top_250"], tbl.loc[T, "all_250"]]):
            continue
        rec = {"start": T,
               "HOLD250": tbl.loc[T, "top_250"], "ROT120": chain(top120), "ROT60": chain(top60),
               "HOLD250_net": tbl.loc[T, "top_250"] - cost, "ROT120_net": chain(top120) - 2 * cost,
               "ROT60_net": chain(top60) - 4 * cost,
               # date-neutral edge harvested per year (additive over legs, costs netted)
               "EDGE_HOLD250": tbl.loc[T, "top_250"] - tbl.loc[T, "all_250"] - cost,
               "EDGE_ROT120": sum(t - a for t, a in zip(top120, all120)) - 2 * cost,
               "EDGE_ROT60": sum(t - a for t, a in zip(top60, all60)) - 4 * cost,
               "cohort_250": tbl.loc[T, "all_250"]}
        if bench is not None and all(above[d] is not None for d in L60):
            g60 = [r if above[d] else 0.0 for r, d in zip(top60, L60)]
            g120 = [r if above[d] else 0.0 for r, d in zip(top120, L120)]
            rec["GATE_HOLD250_net"] = (tbl.loc[T, "top_250"] - cost) if above[T] else 0.0
            rec["GATE_ROT120_net"] = chain(g120) - 2 * cost * sum(1 for d in L120 if above[d]) / 1.0
            rec["GATE_ROT60_net"] = chain(g60) - cost * sum(1 for d in L60 if above[d])
            rec["legs_above_60"] = sum(1 for d in L60 if above[d])
        rows.append(rec)
    return pd.DataFrame(rows).set_index("start")


# --------------------------------------------------------------------------- Test B
def build_arrays(df: pd.DataFrame) -> dict:
    arrs = {}
    for tk, g in df.groupby("ticker", sort=False):
        g = g.sort_values("date")
        arrs[tk] = (pd.DatetimeIndex(g["date"].values), g["adj_close"].to_numpy(float))
    return arrs


def regime_flags(bench: pd.Series) -> pd.Series:
    b = bench.dropna()
    ma = b.rolling(200).mean()
    return (b >= ma).astype(float).where(ma.notna())


def test_b(panel: pd.DataFrame, arrs: dict, delisted: set, bench: pd.Series, topn: int,
           start: pd.Timestamp | None) -> tuple[pd.DataFrame, dict]:
    flags = regime_flags(bench)
    recs = []
    for T, g in panel.groupby("date"):
        if start is not None and T < start:
            continue
        g = g.dropna(subset=[SCORE])
        if len(g) < topn * 2:
            continue
        top = g.sort_values(SCORE, ascending=False).head(topn)
        for r in top.itertuples(index=False):
            a = arrs.get(r.ticker)
            if a is None:
                continue
            dates, close = a
            pos = int(r.pos)
            if pos >= len(close) or close[pos] <= 0:
                continue
            end = min(pos + 250, len(close) - 1)
            f = flags.reindex(dates, method="ffill").to_numpy()
            def ret_at(j):
                return (close[j] / close[pos] - 1.0) * 100.0
            def first_off(j0, need_under=False):
                for j in range(j0, end + 1):
                    if f[j] == 0.0 and (not need_under or close[j] < close[pos]):
                        return j
                return None
            out = {"date": T, "ticker": r.ticker, "delisted": r.ticker in delisted,
                   "entry_above": bool(f[pos] == 1.0) if not np.isnan(f[pos]) else None,
                   "B0": ret_at(end), "B0_days": end - pos}
            j1 = first_off(pos + 1)
            j2 = first_off(pos + 61) if pos + 61 <= end else None
            j4 = first_off(pos + 1, need_under=True)
            out.update({"B1": ret_at(j1 if j1 is not None else end), "B1_exit": j1 is not None,
                        "B1_days": (j1 if j1 is not None else end) - pos,
                        "B2": ret_at(j2 if j2 is not None else end), "B2_exit": j2 is not None,
                        "B4": ret_at(j4 if j4 is not None else end), "B4_exit": j4 is not None})
            recs.append(out)
    df = pd.DataFrame(recs)
    return df, {}


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topn", type=int, default=10)
    args = ap.parse_args()
    lines: list[str] = []

    def emit(s=""):
        print(s, flush=True)
        lines.append(s)

    emit("# 실험 — 보유기간·회전·레짐 청산 (2026-09-06, point-in-time)")
    emit("")
    emit(f"_패널: validation_panel_*_v1 (`{SCORE}` 상위 {args.topn}, 분기 리밸런스). 비용: 왕복 KR {COST_RT['KR']}% · US {COST_RT['US']}%. "
         "도구: `backtest/holding_rotation_experiment.py`._")
    emit("> ⚠️ KR 패널 위생: 2022-06-30 이전 17개 날짜는 **상폐 종목만** 있는 코호트(생존자 시세가 2021-04부터라 MIN_HISTORY 252로 2022-06 전엔 생존자가 없음). "
         "아래 KR 수치는 전부 **클린 날짜(2022-06-30~, 11개)** 기준이며, 이전 날짜는 'H. 패널 위생'에만 따로 보인다. US는 생존자-only(낙관)·10y 시세.")
    emit("")

    for market in ("KR", "US"):
        panel = load_panel(market)
        clean_start = CLEAN_START[market]
        bench = load_benchmark(market)
        cost = COST_RT[market]
        emit(f"## {market}")
        emit("")

        # ---- H. panel hygiene (KR only meaningful, run both for symmetry)
        if market == "KR":
            df_l, delisted = load_prices(market)
            panel["delisted"] = panel["ticker"].isin(delisted)
            comp = panel.groupby("date").agg(n=("ticker", "size"), dl=("delisted", "mean"))
            dirty = comp[comp["dl"] >= 0.999]
            emit("### H. 패널 위생 — KR 날짜 구성")
            emit(f"- 상폐-only 날짜: {len(dirty)}개 ({dirty.index.min().date()}~{dirty.index.max().date()}, n {int(dirty['n'].min())}~{int(dirty['n'].max())}) · "
                 f"클린 날짜: {len(comp) - len(dirty)}개 ({clean_start.date()}~, 상폐 비중 {comp[comp.index >= clean_start]['dl'].mean():.1%})")
            for label, sub in (("전체 28날짜(기존 문서 기준)", panel), ("클린 11날짜", panel[panel["date"] >= clean_start]),
                               ("상폐-only 17날짜", panel[panel["date"] < clean_start])):
                cells = []
                for h in (60, 120, 250):
                    ic, t, pos, nd = per_date_ic(sub, SCORE, f"fwd_{h}")
                    cells.append(f"{h}d IC {ic:+.3f} (t{t:+.1f}, {nd}날짜)")
                emit(f"- {label}: " + " · ".join(cells))
            tbl_all = topn_table(panel, args.topn)
            tbl_clean = topn_table(panel[panel["date"] >= clean_start], args.topn)
            for h in (60, 120, 250):
                e_all = (tbl_all[f"top_{h}"] - tbl_all[f"all_{h}"]).dropna()
                e_cl = (tbl_clean[f"top_{h}"] - tbl_clean[f"all_{h}"]).dropna()
                emit(f"- 상위{args.topn} 날짜중립 엣지 {h}d: 전체 {e_all.mean():+.1f}%p ({(e_all>0).mean():.0%}) → 클린 {e_cl.mean():+.1f}%p ({(e_cl>0).mean():.0%}, t{tstat(e_cl):+.1f})"
                     f" · 클린 상위{args.topn} pooled {tbl_clean[f'top_{h}'].mean():+.1f}% / 코호트 {tbl_clean[f'all_{h}'].mean():+.1f}%")
            emit("")
            panel = panel[panel["date"] >= clean_start].copy()
        else:
            df_l, delisted = load_prices(market)

        tbl = topn_table(panel, args.topn)

        # ---- A. chained rotation
        a = test_a(tbl, bench, cost)
        emit(f"### A. 회전 규칙 — 같은 시작일에서 1년 (시작일 {len(a)}개, 각 전략 동일 시작 집합)")
        emit("")
        emit("| 전략 (비용 차감) | 평균 | 중앙 | 승률 | 최악 | vs HOLD250 |")
        emit("|---|---:|---:|---:|---:|---|")
        ref = a["HOLD250_net"]
        emit(stats_line("HOLD250 (250d 보유 1회)", a["HOLD250_net"]))
        emit(stats_line("ROT120 (120d × 2회 회전)", a["ROT120_net"], ref))
        emit(stats_line("ROT60 (60d × 4회 회전)", a["ROT60_net"], ref))
        emit(stats_line("코호트 250d (점수 무시)", a["cohort_250"]))
        if "GATE_HOLD250_net" in a:
            g = a.dropna(subset=["GATE_HOLD250_net"])
            emit(stats_line("GATE·HOLD250 (200일선 아래 시작이면 현금)", g["GATE_HOLD250_net"], g["HOLD250_net"]))
            emit(stats_line("GATE·ROT120 (레그 시작마다 레짐 확인)", g["GATE_ROT120_net"], g["HOLD250_net"]))
            emit(stats_line("GATE·ROT60 (분기마다 레짐 확인)", g["GATE_ROT60_net"], g["HOLD250_net"]))
        emit("")
        emit("| 날짜중립 엣지 수확/년 (비용 차감) | 평균 | 중앙 | 승률 | 최악 | vs HOLD250 |")
        emit("|---|---:|---:|---:|---:|---|")
        eref = a["EDGE_HOLD250"]
        emit(stats_line("EDGE·HOLD250", a["EDGE_HOLD250"]))
        emit(stats_line("EDGE·ROT120", a["EDGE_ROT120"], eref))
        emit(stats_line("EDGE·ROT60", a["EDGE_ROT60"], eref))
        emit("")
        emit("<details><summary>시작일별 (비용 차감, %)</summary>")
        emit("")
        cols = [c for c in ("HOLD250_net", "ROT120_net", "ROT60_net", "GATE_ROT60_net", "cohort_250", "legs_above_60") if c in a]
        emit("| 시작 | " + " | ".join(cols) + " |")
        emit("|---|" + "---:|" * len(cols))
        for T, r in a.iterrows():
            emit(f"| {T.date()} | " + " | ".join(("—" if pd.isna(r[c]) else (f"{r[c]:+.1f}" if c != "legs_above_60" else f"{int(r[c])}/4")) for c in cols) + " |")
        emit("")
        emit("</details>")
        emit("")

        # ---- B. daily regime exit
        if bench is None:
            emit("### B. 레짐 청산 — 벤치마크 로드 실패로 생략")
            emit("")
            continue
        arrs = build_arrays(df_l)
        b, _ = test_b(panel, arrs, delisted, bench, args.topn, clean_start)
        emit(f"### B. 보유 중 레짐 청산 (일봉, 상위{args.topn} 포지션 {len(b)}개, 최대 250d)")
        emit("")
        emit("| 변형 | 평균 | 중앙 | 승률 | 최악 | vs B0 | 레짐청산 비율 · 평균 보유일 |")
        emit("|---|---:|---:|---:|---:|---|---|")
        for key, name in (("B0", "B0 250d 보유"), ("B1", "B1 200일선 이탈 즉시 청산"),
                          ("B2", "B2 60d 이후에만 레짐 청산"), ("B4", "B4 레짐 이탈 + 손실 중일 때만 청산")):
            s = b[key]
            d = (s - b["B0"]).dropna()
            ex = f"{b[f'{key}_exit'].mean():.0%} · {b[f'{key}_days'].mean():.0f}d" if f"{key}_exit" in b and f"{key}_days" in b else \
                (f"{b[f'{key}_exit'].mean():.0%}" if f"{key}_exit" in b else f"— · {b['B0_days'].mean():.0f}d")
            vs = "기준" if key == "B0" else f"{d.mean():+.1f}%p (t{tstat(d):+.1f}, {(d>0).mean():.0%} 승)"
            emit(f"| {name} | {s.mean():+.1f}% | {s.median():+.1f}% | {(s>0).mean():.0%} | {s.min():+.1f}% | {vs} | {ex} |")
        # split by entry regime
        if b["entry_above"].notna().any():
            emit("")
            emit("| 진입 시 레짐 | n | B0 평균 | B1 평균 | B2 평균 | B4 평균 |")
            emit("|---|---:|---:|---:|---:|---:|")
            for flag, nm in ((True, "200일선 위"), (False, "200일선 아래")):
                sub = b[b["entry_above"] == flag]
                if len(sub):
                    emit(f"| {nm} | {len(sub)} | {sub['B0'].mean():+.1f}% | {sub['B1'].mean():+.1f}% | {sub['B2'].mean():+.1f}% | {sub['B4'].mean():+.1f}% |")
        emit("")

    emit("## 읽는 법")
    emit("- **A**: 같은 시작일 집합에서 1년을 보유 1회(HOLD250) vs 회전(ROT120/ROT60)으로 보낸 결과. 'vs HOLD250'의 t가 |2| 넘고 승률이 60%+면 방향 채택 후보. "
         "시작일이 분기마다 겹치므로 t는 낙관적 — 방향과 일관성으로 읽는다.")
    emit("- **EDGE 행**은 시장 방향을 뺀 순수 순위 엣지의 연간 수확량 — 회전이 '같은 엣지를 여러 번 수확'하는지를 직접 잰다.")
    emit("- **GATE 행**은 레짐을 '진입 스위치'로 쓴 결과(레그 시작 시 200일선 아래면 그 레그는 현금). ROT60+GATE가 사실상 '분기마다 레짐 재확인'이다.")
    emit("- **B**는 보유 중 레짐 이탈 청산. B1이 B0보다 나쁘면 '레짐 청산은 승자를 자른다'는 뜻이고, B4가 낫다면 '손실 중일 때만' 규칙이 후보.")
    emit("- 운영 반영은 10/10 분기 리뷰에서만. 이 결과는 안건 자료다.")
    out = ROOT / "docs" / "experiment-holding-rotation-2026-09-06.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
