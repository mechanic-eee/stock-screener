#!/usr/bin/env python3
"""Strategy backtest — translate the score's IC into 'what would I have made'.

The validation measured IC (a rank correlation). This answers the concrete
question: if each quarter you bought the TOP-N names by the composite score and
held H trading days, what did the average position return — vs the bottom-N and
vs buying a random cohort name? Uses the saved validation panels (score + forward
returns already computed point-in-time), so no refetch.

Reports per market / horizon:
  - top-N avg / median / win% / best / worst position return
  - bottom-N and full-cohort (the 'no skill' baseline) for contrast
  - top-minus-baseline edge (what the score buys you)
  - a per-rebalance portfolio return series (equal-weight the N picks) -> avg & win

Caveats it prints: KR is survivorship-corrected (delisted held-to-last) and the
trustworthy arm; US is survivor-only + thin (optimistic). Overlapping holds
(quarterly rebalance, up to 250d hold) mean these are per-position expectations,
not a compounded equity curve.

Usage: python backtest/strategy_backtest.py [--topn 10] [--panel v1]
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

HORIZONS = [60, 120, 250]


def _stats(s: pd.Series) -> dict:
    v = s.dropna()
    if len(v) == 0:
        return {}
    return {"n": len(v), "mean": v.mean(), "median": v.median(),
            "win": (v > 0).mean(), "best": v.max(), "worst": v.min(),
            "sharpe": v.mean() / v.std() if v.std() > 0 else 0.0}


def strategy(panel: pd.DataFrame, score_col: str, topn: int):
    """Per-rebalance top-N / bottom-N picks by score.

    Returns pooled position returns (every pick equal-weighted — dominated by a
    few brutal rebalance dates) AND per-date edges (top-N mean minus that date's
    cohort mean, one number per rebalance — timing-neutral, the honest read).
    """
    out = {h: {"top": [], "bot": [], "all": [], "port_top": [], "edge": []} for h in HORIZONS}
    for _, g in panel.groupby("date"):
        g = g.dropna(subset=[score_col])
        if len(g) < topn * 2:
            continue
        ranked = g.sort_values(score_col, ascending=False)
        top = ranked.head(topn)
        bot = ranked.tail(topn)
        for h in HORIZONS:
            col = f"fwd_{h}"
            tv, av = top[col].dropna(), g[col].dropna()
            out[h]["top"].extend(tv.tolist())
            out[h]["bot"].extend(bot[col].dropna().tolist())
            out[h]["all"].extend(av.tolist())
            if len(tv) and len(av):
                out[h]["port_top"].append(tv.mean())          # this period's portfolio return
                out[h]["edge"].append(tv.mean() - av.mean())  # timing-neutral edge vs cohort
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topn", type=int, default=10, help="몇 개를 사나 (기본 10)")
    ap.add_argument("--panel", default="v1", help="패널 접미사 (v1=가격+펀더, ''=가격만)")
    ap.add_argument("--score", default="composite_full",
                    help="랭킹 점수열 (composite_full=가격+펀더, composite=가격만)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    suffix = f"_{args.panel}" if args.panel else ""
    lines = []

    def emit(s=""):
        print(s, flush=True)
        lines.append(s)

    emit(f"# 전략 백테스트 — 점수 상위 {args.topn}개 매수 시 (point-in-time)")
    emit("")
    emit(f"_각 분기 리밸런스마다 `{args.score}` 상위 {args.topn}개를 사서 H일 보유한 결과. "
         f"패널: validation_panel_*{suffix}.parquet (점수·forward수익 모두 point-in-time)._")
    emit("> ⚠️ KR=생존편향 보정(신뢰)·US=생존자only+얇음(낙관). 겹치는 보유라 *포지션당 기대치*지 복리 곡선 아님.")
    emit("")

    for market in ("KR", "US"):
        path = ROOT / "exports" / f"validation_panel_{market}{suffix}.parquet"
        if not path.exists():
            emit(f"## {market}\n패널 없음: {path}\n")
            continue
        panel = pd.read_parquet(path)
        sc = args.score if args.score in panel else "composite"
        res = strategy(panel, sc, args.topn)
        emit(f"## {market}  (점수열 `{sc}`, n={len(panel)}, 날짜 {panel['date'].nunique()})")
        emit("")
        emit(f"**날짜중립 엣지** = 매 리밸런스에서 상위{args.topn} 평균 − 그 날짜 코호트 평균(타이밍 제거, 정직). "
             f"**pooled** = 전 포지션 동일가중(몇몇 폭락창이 지배 — 실현 타이밍 리스크 노출).")
        emit("")
        emit(f"| 지평 | **날짜중립 엣지** | +분기% | 상위{args.topn} pooled | 하위{args.topn} pooled | 전체 pooled |")
        emit("|---|---:|---:|---:|---:|---:|")
        for h in HORIZONS:
            t = _stats(pd.Series(res[h]["top"]))
            b = _stats(pd.Series(res[h]["bot"]))
            a = _stats(pd.Series(res[h]["all"]))
            e = pd.Series(res[h]["edge"]).dropna()
            if not t or len(e) == 0:
                continue
            emit(f"| {h}d | **{e.mean():+.1f}%p** | {(e>0).mean():.0%} | "
                 f"{t['mean']:+.1f}% | {b['mean']:+.1f}% | {a['mean']:+.1f}% |")
        emit("")
        emit(f"_상위{args.topn} 최선/최악 포지션(250d): "
             f"{_stats(pd.Series(res[250]['top'])).get('best',0):+.0f}% / "
             f"{_stats(pd.Series(res[250]['top'])).get('worst',0):+.0f}% — 개별 분산 큼, 손절 필수._")
        emit("")

    emit("## 읽는 법 (정직하게)")
    emit(f"- **날짜중립 엣지**가 점수의 진짜 값어치 — *그날 코호트를 그냥 사는 것* 대비 상위{args.topn}이 더 번 %p. "
         "KR서 +1~4%p, 대부분 분기서 양(+). 즉 점수는 **같은 폭락주 중 더 나은 쪽을 고른다.**")
    emit("- ★ **pooled 절대수익이 음수여도 엣지는 양수일 수 있다** — 폭락주는 시장창에 따라 무더기로 깨진다(타이밍 리스크). "
         "점수는 *상대적으로* 낫게 해줄 뿐, 나쁜 창에서 절대 손실까지 막아주진 않는다. → **시간 분산(한 분기 몰빵 금지)·ATR 손절** 필수.")
    emit("- ★ **랭킹엔 반드시 펀더 포함**(`composite_full`): 가격만(`composite`)은 *최상위 분위가 역전*(decile 9~10 음수)이지만, "
         "펀더를 넣으면 최상위까지 단조 — 펀더가 '겉만 싼 함정'을 최상위에서 걸러낸다.")
    emit("- 보유기간 길수록 엣지 안정(펀더가 시간 두고 작동) — **몇 달~1년 홀드 전제**.")
    emit("- 최악 포지션은 −100%(상폐)까지 — **개별 보장 없음, 분산이 전부**. KR 수치 신뢰(상폐보정·표본 두꺼움), US는 방향 참고만.")

    out = args.out or str(ROOT / "docs" / f"strategy-backtest-top{args.topn}.md")
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwritten: {out}", flush=True)


if __name__ == "__main__":
    main()
