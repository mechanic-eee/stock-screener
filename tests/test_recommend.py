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


def test_seed_cohort_survives_decision() -> None:
    """실계좌 결정이 '다른 코호트'의 워치리스트 시드 행을 지우면 안 된다.

    NVO 2026-07-20 실매수가 6/25 시드 코호트를 10→9로 줄였던 회귀
    (같은 사이클 시드(시드일==결정일)만 결정이 대체 — 페이퍼 픽 이중집계 방지는 유지)."""
    import track

    tmp = Path(tempfile.mkdtemp())
    wl = tmp / "WATCHLIST.md"
    dc = tmp / "DECISIONS.md"
    wl.write_text("\n".join([
        "| 종목 (티커) | 논거 | 진입 | 손절선 | 촉매 | 상태 | 갱신일 |",
        "|---|---|---|---|---|---|---|",
        "| Novo (NVO) | 스크리너 93점 시드 | 현재가 $45.88 부근 | $42.13 | 실적 | 보유 | 2026-06-25 |",
        "| Amplus (259630) | 스크리너 85점 | 9,720원 | 7,923원 | 실적 | 보유(페이퍼) | 2026-07-18 |",
    ]), encoding="utf-8")
    dc.write_text("\n".join([
        "## 📌 포지션",
        "| 날짜 | 티커 | 액션 | 진입가 | 손절 | 수량 | 비중 | 논거 | 상태 | 청산 |",
        "|---|---|---|---|---|---|---|---|---|---|",
        "| 2026-07-20 | NVO | 매수 | 50.32 | 47.06 | 29 | 15% | 실계좌 (점수 93) | 보유 | — |",
        "| 2026-07-18 | 259630 | 매수 | 9720 | 7923 | 55 | 5% | 페이퍼 (점수 85) | 보유(페이퍼) | — |",
    ]), encoding="utf-8")

    items = track._collect(wl, dc)
    nvo = [r for r in items if r["ticker"] == "NVO"]
    amp = [r for r in items if r["ticker"] == "259630"]
    # NVO: 6/25 시드(watchlist)와 7/20 실포지션(decision) 둘 다 살아야 한다
    assert len(nvo) == 2 and {r["source"] for r in nvo} == {"watchlist", "decision"}, nvo
    seed = next(r for r in nvo if r["source"] == "watchlist")
    assert seed["date"].isoformat() == "2026-06-25" and seed["ref_price"] == 45.88, seed
    # 같은 사이클(시드일==결정일) 페이퍼 픽은 여전히 결정 행 하나로 대체(이중집계 방지)
    assert len(amp) == 1 and amp[0]["source"] == "decision", amp
    print("  seed-cohort: older seed survives real decision, same-cycle dedup kept OK")


def test_review_verdict() -> None:
    """규율 대시보드 _verdict: 규칙별 태그/플래그 (타이밍 신호 없음, 규칙만)."""
    import datetime as dt

    import review
    today = dt.date(2026, 7, 22)

    def V(h, price, rank=None, distress=None, edgar=None):
        return review._verdict(h, price, rank, distress, edgar, today)

    # 손절 이탈 → 🔴
    r = V({"market": "US", "cost": 50.0, "stop": 47.0}, 46.0)
    assert r["tag"].startswith("🔴") and any("손절이탈" in f for f in r["flags"]), r

    # 손절선 미설정 → 🟠 (규율 갭)
    r = V({"market": "US", "cost": 50.0, "stop": None}, 60.0)
    assert r["tag"].startswith("🟠") and any("손절선 미설정" in f for f in r["flags"]), r

    # 손절 근접 → 🟠
    r = V({"market": "US", "cost": 50.0, "stop": 47.0}, 49.0)
    assert r["tag"].startswith("🟠") and any("손절근접" in f for f in r["flags"]), r

    # 위험공시 → 🔴 (손절 여유 충분해도)
    r = V({"market": "KR", "cost": 100.0, "stop": 50.0}, 90.0, distress=["감사의견 비적정"])
    assert r["tag"].startswith("🔴") and any("감사의견" in f for f in r["flags"]), r

    # 랭킹 하위 50% 강등 → 🟠
    r = V({"market": "US", "cost": 50.0, "stop": 40.0}, 60.0, rank=(400, 600, 70))
    assert r["tag"].startswith("🟠") and any("하위 50%" in f for f in r["flags"]), r

    # 깊은 손실 → 🟠 재평가 (청산 아님)
    r = V({"market": "KR", "cost": 100.0, "stop": 40.0}, 55.0)  # -45%
    assert r["tag"].startswith("🟠") and any("재평가" in f for f in r["flags"]), r

    # 계획된 추가 도래 → adds에 🔵, 태그는 유지(추가는 별개 축)
    r = V({"market": "US", "cost": 50.0, "stop": 45.0,
           "planned_add": {"date": "2026-07-25", "note": "2차 트랜치"}}, 52.0)
    assert r["tag"].startswith("🟢") and any("계획된 추가" in a for a in r["adds"]), r

    # 깨끗 → 🟢
    r = V({"market": "US", "cost": 50.0, "stop": 45.0}, 52.0)
    assert r["tag"].startswith("🟢") and not r["flags"], r

    # 가격 없음 → ⚪
    r = V({"market": "US", "cost": 50.0, "stop": 45.0}, None)
    assert r["tag"].startswith("⚪"), r

    # EDGAR 🔴 신규공시 → 🔴 청산검토 (손절 여유 충분해도)
    r = V({"market": "US", "cost": 50.0, "stop": 40.0}, 60.0, edgar=[("🔴", "424B5", dt.date(2026, 7, 20))])
    assert r["tag"].startswith("🔴") and any("424B5" in f for f in r["flags"]), r
    # EDGAR 🟠 8-K → 🟠
    r = V({"market": "US", "cost": 50.0, "stop": 40.0}, 60.0, edgar=[("🟠", "8-K", dt.date(2026, 7, 20))])
    assert r["tag"].startswith("🟠") and any("8-K" in f for f in r["flags"]), r
    # EDGAR 빈 리스트(점검했으나 신규 없음) → EDGAR 플래그 없음
    r = V({"market": "US", "cost": 50.0, "stop": 45.0}, 52.0, edgar=[])
    assert r["tag"].startswith("🟢") and not any("EDGAR" in f for f in r["flags"]), r

    # stop=0 → 미설정으로 정규화(🟠 손절선 미설정), price<=0 오판 없음
    r = V({"market": "US", "cost": 50.0, "stop": 0}, 60.0)
    assert r["tag"].startswith("🟠") and any("손절선 미설정" in f for f in r["flags"]), r

    # 랭킹 유니버스 밖(None) → 강등 아님 (ETF 오탐 방지)
    r = V({"market": "US", "cost": 50.0, "stop": 45.0}, 52.0, rank=(None, 600, None))
    assert r["tag"].startswith("🟢") and not any("강등" in f for f in r["flags"]), r
    # 랭킹 상위권 → 강등 아님
    r = V({"market": "US", "cost": 50.0, "stop": 45.0}, 52.0, rank=(10, 600, 90))
    assert r["tag"].startswith("🟢"), r

    # 계획된 추가: 창밖(D+20) → adds 없음
    r = V({"market": "US", "cost": 50, "stop": 45, "planned_add": {"date": "2026-08-11", "note": "x"}}, 52.0)
    assert not r["adds"], r
    # 계획된 추가: '지남'(D-2)
    r = V({"market": "US", "cost": 50, "stop": 45, "planned_add": {"date": "2026-07-20", "note": "x"}}, 52.0)
    assert any("지남" in a for a in r["adds"]), r
    # 잘못된 날짜 형식 → 크래시 없이 ⚠️ 플래그로 표면화
    r = V({"market": "US", "cost": 50, "stop": 45, "planned_add": {"date": "2026.08.10", "note": "x"}}, 52.0)
    assert any("planned_add 날짜 형식 오류" in f for f in r["flags"]), r
    # planned_add가 객체 아닌 문자열 → 크래시 없이 무시
    r = V({"market": "US", "cost": 50, "stop": 45, "planned_add": "2026-08-10"}, 52.0)
    assert r["tag"].startswith("🟢") and not r["adds"], r
    # ★ 물타기 방지: 🔴(손절이탈) 있으면 계획된 추가 억제 → adds 없음, soft에 '보류'
    r = V({"market": "US", "cost": 50, "stop": 45, "planned_add": {"date": "2026-07-25", "note": "2차"}}, 44.0)
    assert r["tag"].startswith("🔴") and not r["adds"] and any("보류" in s for s in r["soft"]), r

    print("  review verdict: stop0/edgar/rank-none/rank-top/add-window/add-suppress-on-red/malformed OK")


def test_review_watch_verdict() -> None:
    """워치(재진입 트리거·재상정일): 상방/하방/날짜/오류 전 분기."""
    import datetime as dt

    import review
    today = dt.date(2026, 8, 8)
    W = review._watch_verdict

    # price_above: 도달/미달/가격없음
    assert W({"ticker": "NVO", "type": "price_above", "level": 47.06, "note": "재진입"}, 47.10, today)
    assert W({"ticker": "NVO", "type": "price_above", "level": 47.06}, 46.99, today) is None
    assert W({"ticker": "NVO", "type": "price_above", "level": 47.06}, None, today) is None
    # price_below 도달
    assert W({"ticker": "X", "type": "price_below", "level": 10.0}, 9.5, today)
    # date: D-DAY / D+n / 미도래 / 형식오류
    assert "D-DAY" in W({"ticker": "215200", "type": "date", "date": "2026-08-08", "note": "실적"}, None, today)
    assert "D+2" in W({"ticker": "215200", "type": "date", "date": "2026-08-06", "note": "실적"}, None, today)
    assert W({"ticker": "010780", "type": "date", "date": "2026-08-18"}, None, today) is None
    assert "형식 오류" in W({"ticker": "X", "type": "date", "date": "8/18"}, None, today)
    # 미상 type → 표면화
    assert "미상" in W({"ticker": "X", "type": "pricebelow"}, 1.0, today)
    # level 결측/비숫자 → 블라인드 방지 표면화 (감사 F8)
    assert "미설정" in W({"ticker": "X", "type": "price_above"}, 50.0, today)
    assert "형식 오류" in W({"ticker": "X", "type": "price_above", "level": "사만칠천"}, 50.0, today)
    # 문자열이라도 숫자로 강제 가능하면 정상 판정
    assert W({"ticker": "X", "type": "price_above", "level": "47.06"}, 47.10, today)
    # dict 아닌 항목 → 크래시 없이 표면화 (감사 F2)
    assert "형식 오류" in W("NVO>47", None, today)
    print("  watch verdict: above/below/date/dday/malformed/level-guard OK")


def test_track_exit_price_freeze() -> None:
    """청산 행은 청산가에 동결 — 현재가 재계산으로 기록과 어긋나던 버그(8/7 관찰) 회귀가드."""
    import track

    md = "\n".join([
        "## 📌 포지션",
        "| 날짜 | 티커 | 액션 | 진입가 | 손절 | 수량 | 비중 | 논거 | 상태 | 청산가/수익률 |",
        "|---|---|---|---|---|---|---|---|---|---|",
        "| 2026-07-20 | NVO | 매수 | 50.28 | 47.06 | 31 | 16% | x (점수 93) | 청산 | 45.22 (-10.1%) |",
        "| 2026-08-07 | MNSO | 매수 | 12.29 | 11.39 | 111 | 14% | y (점수 84) | 보유(페이퍼) | — |",
    ])
    p = Path(tempfile.mkdtemp()) / "DECISIONS.md"
    p.write_text(md, encoding="utf-8")
    by = {r["ticker"]: r for r in track._records_from(p, "decision")}
    assert by["NVO"]["exit_price"] == 45.22, by["NVO"]     # 청산가 파싱("45.22 (-10.1%)" → 45.22)
    assert by["MNSO"]["exit_price"] is None, by["MNSO"]    # 열린 포지션은 동결 없음

    # 전액손실 청산 "0 (-100%)" → exit_price 0.0 (falsy지만 유효한 동결값 — 감사 F3)
    md0 = md.replace("| 청산 | 45.22 (-10.1%) |", "| 청산 | 0 (-100%) |")
    p0 = Path(tempfile.mkdtemp()) / "DECISIONS.md"
    p0.write_text(md0, encoding="utf-8")
    by0 = {r["ticker"]: r for r in track._records_from(p0, "decision")}
    assert by0["NVO"]["exit_price"] == 0.0, by0["NVO"]
    print("  exit-price freeze: closed row parses exit(+zero), open row None OK")


def test_ledger_summary() -> None:
    """실현손익 원장: 통산·연도필터·KR 분리·공제 경계 양쪽."""
    import ledger

    trades = [
        {"date": "2026-07-21", "ticker": "A", "market": "US", "qty": 10, "buy": 10.0, "sell": 15.0},   # +50
        {"date": "2026-08-01", "ticker": "B", "market": "US", "qty": 10, "buy": 20.0, "sell": 15.0},   # -50
        {"date": "2025-12-31", "ticker": "C", "market": "US", "qty": 100, "buy": 1.0, "sell": 9.0},    # 작년 — 제외
        {"date": "2026-08-05", "ticker": "440110", "market": "KR", "qty": 10, "buy": 1000, "sell": 2000},  # KR +1만원
    ]
    s = ledger._summary(trades, fx=1000.0, year=2026)
    assert len(s["rows"]) == 3, s["rows"]                      # 2025 거래 제외
    assert abs(s["us_total_usd"] - 0.0) < 1e-9, s              # +50-50 통산 0
    assert s["kr_total_krw"] == 10000, s                       # KR은 분리(비과세)
    assert s["taxable_krw"] == 0 and s["est_tax_krw"] == 0, s
    assert s["exemption_left_krw"] == ledger.EXEMPTION_KRW, s  # 통산 0이면 공제 전액 여유

    # 공제 초과 케이스: +$3,000 × 1000원 = 300만 → 과세표준 50만 → 세 11만
    s2 = ledger._summary([{"date": "2026-01-01", "ticker": "D", "market": "US",
                           "qty": 100, "buy": 10.0, "sell": 40.0}], fx=1000.0, year=2026)
    assert s2["taxable_krw"] == 500_000 and abs(s2["est_tax_krw"] - 110_000) < 1e-6, s2
    assert s2["exemption_left_krw"] < 0, s2
    print("  ledger: netting/year-filter/KR-split/exemption-both-sides OK")


def test_review_theme_concentration() -> None:
    import review

    rows = [
        {"h": {"theme": "NAND"}, "value_usd": 60},
        {"h": {"theme": "leverage"}, "value_usd": 30},
        {"h": {"theme": "pharma"}, "value_usd": 10},
        {"h": {"theme": "NAND"}, "value_usd": None},   # 값 없음 → 스킵
    ]
    themes = {"NAND": {"comfort_max_pct": 40, "label": "낸드"}, "leverage": {"comfort_max_pct": 15}}
    out = review._theme_concentration(rows, themes)
    assert out[0][0] is True and "낸드: 60%" in out[0][1] and "초과" in out[0][1], out  # 내림차순·초과
    labels = [line for _, line in out]
    assert any("leverage: 30%" in l and "초과" in l for l in labels), out
    assert any("pharma: 10%" in l and "초과" not in l for l in labels), out  # cap 없으면 초과 아님
    assert review._theme_concentration([{"h": {"theme": "x"}, "value_usd": None}], {}) == []  # tot 0 → []
    print("  review theme_concentration: pct/cap/skip-None/sort/empty OK")


def test_review_rank_map() -> None:
    """_rank_map: 점수 키('점수')·유니버스 제외(ETF)·유니버스 밖 None·3-튜플 arity 고정."""
    import sys as _sys
    import types

    import review
    fake = types.ModuleType("recommend")
    fake.twl = types.SimpleNamespace(DEFAULT_SNAPSHOT="x")
    rows = [
        {"ticker": "AAA", "market": "US", "_security_type": "common", "점수": 90},
        {"ticker": "BBB", "market": "US", "_security_type": "common", "점수": 70},
        {"ticker": "ETF", "market": "US", "_security_type": "etf", "점수": 80},
    ]
    fake._load_rows = lambda *a, **k: (rows, {})
    old = _sys.modules.get("recommend")
    _sys.modules["recommend"] = fake
    try:
        m = review._rank_map([{"ticker": "AAA", "market": "US"}, {"ticker": "BBB", "market": "US"},
                              {"ticker": "ZZZ", "market": "US"}, {"ticker": "ETF", "market": "US"}])
    finally:
        if old is not None:
            _sys.modules["recommend"] = old
        else:
            _sys.modules.pop("recommend", None)
    assert m["AAA"] == (1, 2, 90), m       # rank1/2 (ETF 제외), 점수 키로 조회
    assert m["BBB"] == (2, 2, 70), m
    assert m["ZZZ"] == (None, 2, None), m  # 유니버스 밖
    assert m["ETF"] == (None, 2, None), m  # etf는 랭킹 리스트에서 제외
    print("  review rank_map: 점수-key + universe-exclusion + None + 3-tuple OK")


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

    # 날짜는 오늘 기준 상대값 — 고정 날짜(예전 "7/29")는 그날이 지나면 과거 이벤트로
    # 걸러져 테스트가 부패한다(2026-08-05 실제 발생: 파이프가 exit code까지 삼켜 red push).
    from datetime import date, timedelta
    cat = date.today() + timedelta(days=20)
    tr2 = date.today() + timedelta(days=35)
    rev120 = (date.today() + timedelta(days=120)).isoformat()

    tmp = Path(tempfile.mkdtemp())
    wl = tmp / "WATCHLIST.md"
    wl.write_text("\n".join([
        "| 종목 (티커) | 한줄 논거 | 진입 | 손절선 | 촉매/이벤트 (날짜) | 상태 | 갱신일 |",
        "|---|---|---|---|---|---|---|",
        f"| Boston Scientific (BSX) | x | $43.04 | $39.16 | 2Q 실적 ({cat.month}/{cat.day} 확정) | 보유(페이퍼) | 2026-07-18 |",
        f"| NerdWallet (NRDS) | x | $9.53 | — | 2Q 실적 ({cat.month}/{cat.day} 확정) | 제외 | 2026-07-18 |",
    ]), encoding="utf-8")
    dc = tmp / "DECISIONS.md"
    dc.write_text(f"- [2026-07-18] 2차 트랜치 결정 {tr2.month}/{tr2.day}(월), 120d 리뷰 {rev120}.",
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
    test_seed_cohort_survives_decision()
    test_review_verdict()
    test_review_watch_verdict()
    test_track_exit_price_freeze()
    test_ledger_summary()
    test_review_theme_concentration()
    test_review_rank_map()
    test_edgar_filter()
    test_weekly_cohort_lines()
    test_score_regex_formats()
    test_biz_days_behind()
    print("✅ test_recommend: all passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
