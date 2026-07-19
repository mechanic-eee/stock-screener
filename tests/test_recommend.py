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

    # no-turnover-data rows must not be dropped by the liquidity gate, but must
    # be MARKED unchecked (3-state — silent pass was the audit's fail-open find)
    nodata = _row("NODATA")
    nodata.pop("avg_turnover")
    kept2, dropped2 = apply_gates([nodata])
    assert kept2 and not dropped2, dropped2
    assert "미검증" in kept2[0].get("_liquidity", ""), kept2[0]
    print("  gates: ordering + reasons + AND-combo + unchecked-marking OK")


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
    # decide.py writes "(점수 93)" — the old _SCORE regex silently dropped it
    # (2026-07-19 audit: score-efficacy loop broken for every real position)
    assert by["NVO"]["score"] == 93.0 and by["PGNY"]["score"] == 90.0, by

    valid = [{**r, "ret": 5.0, "days": 1} for r in recs]
    lines = track._cohort_summary(valid)
    assert len(lines) == 2, lines                       # same date, split by paper
    assert sum("[페이퍼]" in ln for ln in lines) == 1, lines
    print("  paper: record flag + cohort split + decide-format score OK")


def test_tranche_merge() -> None:
    """2nd tranche must merge (weighted avg), not overwrite tranche 1 (audit 중-9)."""
    import track

    md = "\n".join([
        "## 📌 포지션",
        "| 날짜 | 티커 | 액션 | 진입가 | 손절 | 수량 | 비중 | 논거 | 상태 | 청산 |",
        "|---|---|---|---|---|---|---|---|---|---|",
        "| 2026-07-18 | NVO | 매수 | 49.00 | 42.13 | 20 | 10% | x (점수 93) | 보유(페이퍼) | — |",
        "| 2026-08-10 | NVO | 추가매수 | 51.00 | 44.00 | 10 | 5% | 2차 (점수 91) | 보유(페이퍼) | — |",
        "| 2026-07-18 | TROX | 매수 | 7.55 | 6.00 | 100 | 8% | x (점수 80) | 청산 | 6.10 (-19.2%) |",
    ])
    p = Path(tempfile.mkdtemp()) / "DECISIONS.md"
    p.write_text(md, encoding="utf-8")

    from collections import defaultdict
    by = defaultdict(list)
    for r in track._records_from(p, "decision"):
        by[r["ticker"]].append(r)

    merged = track._merge_tranches([r for r in by["NVO"] if "보유" in r["status"]])
    assert abs(merged["ref_price"] - (49.00 * 20 + 51.00 * 10) / 30) < 1e-9, merged
    assert merged["shares"] == 30 and merged["stop"] == 44.00, merged
    assert merged["date"].isoformat() == "2026-07-18", merged   # holding starts at tranche 1
    assert merged["source"].endswith("×2"), merged
    assert len(by["TROX"]) == 1 and "청산" in by["TROX"][0]["status"]
    print("  tranche merge: weighted avg + latest stop + first date OK")


def test_score_regex_formats() -> None:
    import track

    cases = {"5년고가 대비 66% 낙폭, 스크리너 93점, ATR": 93.0,
             "EV캐즘 사이클 낙폭 (1차 트랜치) (점수 84.7)": 84.7,
             "레거시 표기 100점": 100.0}
    for text, want in cases.items():
        m = track._SCORE.search(text)
        assert m, text
        got = float(m.group(1) or m.group(2) or m.group(3))
        assert got == want, (text, got)
    print("  score regex: 3 formats OK")


def test_upcoming_events() -> None:
    """monitor event reminders: watchlist catalyst M/D + DECISIONS tranche/review."""
    import monitor
    import track

    tmp = Path(tempfile.mkdtemp())
    wl = tmp / "WATCHLIST.md"
    wl.write_text("\n".join([
        "| 종목 (티커) | 한줄 논거 | 진입 | 손절선 | 촉매/이벤트 (날짜) | 상태 | 갱신일 |",
        "|---|---|---|---|---|---|---|",
        "| Boston Scientific (BSX) | x | $43.04 | $39.16 | 2Q 실적 (7/29 확정) | 보유(페이퍼) | 2026-07-18 |",
        "| NerdWallet (NRDS) | x | $9.53 | — | 2Q 실적 (8/6 확정) | 제외 | 2026-07-18 |",
    ]), encoding="utf-8")
    dc = tmp / "DECISIONS.md"
    dc.write_text("- [2026-07-18] 2차 트랜치 결정 8/10(월), 120d 리뷰 2026-11-16.",
                  encoding="utf-8")

    old_wl, old_dc = track.WATCHLIST, track.DECISIONS
    track.WATCHLIST, track.DECISIONS = wl, dc
    try:
        events = monitor._upcoming_events({"BSX"})   # NRDS not held -> excluded
    finally:
        track.WATCHLIST, track.DECISIONS = old_wl, old_dc

    labels = [lbl for _, lbl in events]
    assert any("BSX" in lbl for lbl in labels), events
    assert not any("NRDS" in lbl for lbl in labels), events
    assert any("2차 트랜치" in lbl for lbl in labels), events
    assert any("120d 리뷰" in lbl for lbl in labels), events
    assert events == sorted(events, key=lambda e: e[0]), events
    print("  events: held-only catalyst + tranche/review parse OK")


def test_edgar_filter() -> None:
    """EDGAR watch: severity map, seen-skip, lookback window (pure function)."""
    from datetime import date

    import monitor

    assert monitor._classify_filing("424B5") == "🔴"
    assert monitor._classify_filing("S-1/A") == "🔴"
    assert monitor._classify_filing("NT 10-Q") == "🔴"
    assert monitor._classify_filing("8-K") == "🟠"
    assert monitor._classify_filing("10-Q") is None
    assert monitor._classify_filing("4") is None

    forms = ["8-K", "424B5", "10-Q", "8-K", "S-1"]
    dates = ["2026-07-18", "2026-07-15", "2026-07-14", "2026-05-01", "2026-07-10"]
    accs = ["a1", "a2", "a3", "a4", "a5"]
    got = monitor._filter_new_filings(forms, dates, accs, seen={"a5"},
                                      today=date(2026, 7, 19))
    got_accs = [g[3] for g in got]
    assert got_accs == ["a1", "a2"], got       # 10-Q ignored, a4 out of window, a5 seen
    assert got[1][0] == "🔴" and got[0][0] == "🟠", got
    print("  edgar: severity + seen + lookback OK")


def test_weekly_cohort_lines() -> None:
    """Weekly report pulls cohort bullets from TRACKING.md."""
    import monitor
    import track

    tmp = Path(tempfile.mkdtemp())
    (tmp / "TRACKING.md").write_text("\n".join([
        "# TRACKING", "",
        "**코호트별** (시드일 기준):",
        "- 2026-06-25 (24d, 10종목): 평균 +2.9%, 승률 60% (vs KOSPI -23.6%)",
        "- 2026-07-18 [페이퍼] (1d, 5종목): 평균 +0.3%, 승률 60%",
        "", "| 표 |",
    ]), encoding="utf-8")
    old = track.INVESTING
    track.INVESTING = tmp
    try:
        lines = monitor._tracking_cohort_lines()
    finally:
        track.INVESTING = old
    assert len(lines) == 2 and "[페이퍼]" in lines[1], lines
    print("  weekly: TRACKING cohort bullets parse OK")


def test_biz_days_behind() -> None:
    from datetime import date

    from recommend import _biz_days_behind

    assert _biz_days_behind(date(2026, 7, 17), date(2026, 7, 18)) == 0   # Fri data, Sat run
    assert _biz_days_behind(date(2026, 7, 17), date(2026, 7, 20)) == 1   # Fri data, Mon run
    assert _biz_days_behind(date(2026, 7, 15), date(2026, 7, 17)) == 2   # the 7/16 incident shape
    assert _biz_days_behind(date(2026, 7, 17), date(2026, 7, 17)) == 0
    print("  biz-days-behind: boundary cases OK")


def main() -> int:
    test_gates()
    test_paper_cohorts()
    test_tranche_merge()
    test_upcoming_events()
    test_edgar_filter()
    test_weekly_cohort_lines()
    test_score_regex_formats()
    test_biz_days_behind()
    print("✅ test_recommend: all passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
