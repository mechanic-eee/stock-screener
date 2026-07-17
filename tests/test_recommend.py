"""Unit tests for the recommendation funnel (scripts/recommend.py) + paper-tag
tracking (scripts/track.py).

Guards the 2026-07-17 recommendation-design build:
  1. apply_gates ordering + reasons (결측 → ATR → 부도 이중확인 → 유동성).
  2. The Altman/Piotroski double-confirm is an AND (either alone must pass).
  3. track.py separates paper cohorts from real-money cohorts ([페이퍼] label).

Pure functions + temp files — no network, no snapshot. Invoke directly:
  python tests/test_recommend.py
"""
from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _row(ticker="TST", market="US", atr=4.0, altman=3.0, pio=6.0,
         turnover=1_000_000.0, pos_value=10_000.0, missing=()):
    vals = {"fundamental": 80.0, "altman_z": altman, "piotroski": pio,
            "gross_profit": 0.3, "valuation": 70.0, "atr_risk": atr}
    for k in missing:
        vals.pop(k, None)
    return {"ticker": ticker, "market": market, "점수": 85.0, "하락률": 60.0,
            "_values": vals, "atr_pct": atr, "avg_turnover": turnover,
            "pos_value": pos_value}


def test_gates() -> None:
    from recommend import apply_gates

    ok = _row("OK")
    miss = _row("MISS", missing=("piotroski",))
    fat_atr = _row("FATATR", atr=9.5)
    zombie = _row("ZOMBIE", altman=0.5, pio=2.0)          # both bad -> drop
    half_bad = _row("HALFBAD", altman=0.5, pio=5.0)       # one bad -> keep
    illiq = _row("ILLIQ", turnover=100_000.0, pos_value=10_000.0)  # 10% > 3%

    kept, dropped = apply_gates([ok, miss, fat_atr, zombie, half_bad, illiq])
    kept_t = {r["ticker"] for r in kept}
    reasons = {r["ticker"]: why for r, why in dropped}

    assert kept_t == {"OK", "HALFBAD"}, kept_t
    assert "결측" in reasons["MISS"], reasons
    assert "ATR" in reasons["FATATR"], reasons
    assert "부도 이중확인" in reasons["ZOMBIE"], reasons
    assert "유동성" in reasons["ILLIQ"], reasons

    # no-turnover-data rows must not be dropped by the liquidity gate (fail-soft)
    nodata = _row("NODATA")
    nodata.pop("avg_turnover")
    kept2, dropped2 = apply_gates([nodata])
    assert kept2 and not dropped2, dropped2
    print("  gates: ordering + reasons + AND-combo + fail-soft OK")


def test_paper_cohorts() -> None:
    import track

    md = "\n".join([
        "## 📌 포지션",
        "| 날짜 | 티커 | 액션 | 진입가 | 손절 | 수량 | 비중 | 논거 | 상태 | 청산 |",
        "|---|---|---|---|---|---|---|---|---|---|",
        "| 2026-07-17 | NVO | 매수 | 49.00 | 42.13 | 20 | 10% | x (점수 93) | 보유(페이퍼) | — |",
        "| 2026-07-17 | PGNY | 매수 | 31.00 | 24.05 | 14 | 9% | x (점수 90) | 보유 | — |",
    ])
    p = Path(tempfile.mkdtemp()) / "DECISIONS.md"
    p.write_text(md, encoding="utf-8")

    recs = track._records_from(p, "decision")
    by = {r["ticker"]: r for r in recs}
    assert by["NVO"]["paper"] is True and by["PGNY"]["paper"] is False, by

    valid = [{**r, "ret": 5.0, "days": 1} for r in recs]
    lines = track._cohort_summary(valid)
    assert len(lines) == 2, lines                       # same date, split by paper
    assert sum("[페이퍼]" in ln for ln in lines) == 1, lines
    print("  paper: record flag + cohort split OK")


def main() -> int:
    test_gates()
    test_paper_cohorts()
    print("✅ test_recommend: all passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
