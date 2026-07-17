"""recommend.py — 주간 추천 깔때기: 랭킹 상위 → 하드 게이트 → 체크리스트 후보.

docs/recommendation-design-2026-07-17.md §1의 자동화 구간(단계 0~1 + 유동성·부도
이중확인 + 진입 전 위험공시 재점검)을 한 명령으로 실행한다. 출력은 '매수 리스트'가
아니라 **사람 체크리스트(단계 3)에 올릴 후보 + 탈락 사유**다 — 점수는 후보 풀
축소기이지 최종 선택기가 아니다.

게이트 순서 (숫자 파라미터는 전부 [재량] — 12주 사전등록 고정, 개정은 분기 리뷰만):
  0. 레짐: 지수 200일선 아래 시장은 신규 차단(후보는 페이퍼 전용 표기)   [검증]
  1. 랭크 컷: 시장별 enrichment 랭킹 상위 N(기본 15)                     [검증 정합]
  2. 펀더 4신호(fundamental·altman·piotroski·GP) 결측 0                  [검증 취지]
  3. ATR% ≤ 8                                                            [재량]
  4. Altman Z''<1.1 AND Piotroski≤2 동시면 탈락(부도 이중확인)           [재량]
  5. 유동성: R-사이징 포지션 초안 ≤ 20일 평균 거래대금의 3%              [재량]
  6. 위험공시 라이브 재점검(monitor._distress 재사용, --no-fresh-distress로 생략)

  python scripts/recommend.py                          # KR+US 깔때기 + exports/ 체크리스트
  python scripts/recommend.py --markets US --top 15
  python scripts/recommend.py --no-fresh-distress      # DART/펀더 라이브 재점검 생략(빠름)
  python scripts/recommend.py --no-write               # 체크리스트 파일 안 씀(콘솔만)
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import position_size as ps  # noqa: E402
import to_watchlist as twl  # noqa: E402  (reuse _attach_atr + DEFAULT_SNAPSHOT)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:  # DART_API_KEY 등 로컬 .env
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"

# 일일 알림·to_watchlist 기본과 동일한 검증 세트 (설계 §1 단계 1의 랭킹 기반)
ALERT_SET = ["fundamental", "valuation", "altman_z", "piotroski",
             "gross_profit", "atr_risk"]
FUND4 = ("fundamental", "altman_z", "piotroski", "gross_profit")

# 왕복 거래비용 가정치 [재량 — 정보 표시용]: KR 매도 거래세 ~0.15% + 슬리피지
# 편도 ~0.15%×2, US는 세금 무시(SEC fee 미미) + 슬리피지 왕복. 검증 엣지(픽당
# +1.3~3.8%p)의 12~35%를 비용이 먹는다는 걸 매 실행마다 눈앞에 둔다(적대검증 §C1).
COST_NOTE = {"KR": ("≈0.45%", "거래세 0.15% + 슬리피지 0.15%×2"),
             "US": ("≈0.30%", "슬리피지 0.15%×2")}


# --------------------------------------------------------------------------- #
# 게이트 (순수 함수 — 테스트 대상)
# --------------------------------------------------------------------------- #
def apply_gates(rows: list[dict], atr_max: float = 8.0,
                altman_floor: float = 1.1, pio_floor: float = 2.0,
                turnover_cap_pct: float = 3.0):
    """설계 §1 단계 1의 하드 게이트를 순서대로 적용.

    rows의 각 행은 engine.apply_filters 산출물에 `atr_pct`(ATR%),
    `avg_turnover`(20일 평균 거래대금), `pos_value`(R-사이징 포지션 초안 금액)가
    부착돼 있어야 한다. 반환: (통과 행 리스트, [(탈락 행, 사유)]).
    첫 번째로 걸린 게이트가 사유가 된다.
    """
    kept, dropped = [], []
    for r in rows:
        vals = r.get("_values") or {}
        miss = [k for k in FUND4 if k not in vals]
        if miss:
            dropped.append((r, f"펀더 결측 {len(miss)}건({','.join(miss)}) — 결측-중립 함정"))
            continue
        atr = r.get("atr_pct")
        if atr is None:
            dropped.append((r, "ATR/손절초안 산출 불가(OHLC 부족)"))
            continue
        if atr > atr_max:
            dropped.append((r, f"ATR {atr:.1f}% > {atr_max:.0f}% [재량]"))
            continue
        if (float(vals["altman_z"]) < altman_floor
                and float(vals["piotroski"]) <= pio_floor):
            dropped.append((r, f"부도 이중확인(Altman {vals['altman_z']:.2f}<{altman_floor}"
                               f" AND F {vals['piotroski']:.0f}≤{pio_floor:.0f}) [재량]"))
            continue
        to = r.get("avg_turnover")
        pv = r.get("pos_value")
        if to and pv and pv > to * (turnover_cap_pct / 100.0):
            dropped.append((r, f"유동성(포지션 {pv:,.0f} > 20일 거래대금 {to:,.0f}의 "
                               f"{turnover_cap_pct:.0f}%) [재량]"))
            continue
        kept.append(r)
    return kept, dropped


# --------------------------------------------------------------------------- #
# 데이터 로드 · 부착
# --------------------------------------------------------------------------- #
def _load_rows(source: str, min_drop: int, years: int):
    """스냅샷 → 검증 세트 랭킹 행 + (거래대금·ATR손절·사이징 부착용) 가격 프레임."""
    from screener import engine, snapshot

    engine.ensure_filters_loaded()
    cands = snapshot.load_candidates(source)
    for fn in (snapshot.prime_benchmarks, snapshot.prime_valuations,
               snapshot.prime_fundamentals):
        try:
            fn(source)
        except Exception:  # noqa: BLE001 — 사이드카 없으면 fail-soft(결측 게이트가 잡는다)
            pass
    selected = {k: {} for k in ALERT_SET}
    rows = engine.apply_filters(cands, base_params={"years": years, "min_drop_pct": min_drop},
                                selected=selected, fetch_news=False)
    px = {c.ticker: c.prices for c in cands}
    return rows, px


def _attach_drafts(rows: list[dict], px: dict, stop_mult: float,
                   cfg: dict, risk_pct: float) -> None:
    """ATR 손절 초안(to_watchlist 재사용) + 20일 거래대금 + R-사이징 초안 부착."""
    for r in rows:
        prices = px.get(r["ticker"])
        if prices is None or prices.empty:
            continue
        twl._attach_atr(r, prices, stop_mult)  # -> atr_pct, stop
        try:
            turn = (prices["close"] * prices["volume"]).dropna().tail(20)
            if len(turn):
                r["avg_turnover"] = float(turn.mean())
        except Exception:  # noqa: BLE001 — 거래량 없으면 유동성 게이트는 통과(정보 부족 표기)
            pass
        stop = r.get("stop")
        close = r.get("close")
        if stop and close and stop < close:
            account = cfg["account_krw"] if r["market"] == "KR" else cfg["account_usd"]
            s = ps.size_position(close, stop, account, risk_pct, cfg["max_pos_pct"])
            if s["ok"]:
                r["pos_value"] = s["position_value"]
                r["pos_pct"] = s["position_pct"]
                r["shares"] = s["shares"]
                r["stop_pct"] = s["stop_pct"]


def _regime(markets: list[str]) -> dict[str, bool | None]:
    """시장별 200일선 위 여부 (스냅샷 프라임 후라 라이브 fetch 없음). None=판정불가."""
    from screener import benchmark

    out: dict[str, bool | None] = {}
    for mk in markets:
        try:
            s = benchmark.get_benchmark(mk)
            out[mk] = (float(s.iloc[-1]) >= float(s.tail(200).mean())
                       if s is not None and len(s) >= 200 else None)
        except Exception:  # noqa: BLE001
            out[mk] = None
    return out


def _fresh_distress(market: str, ticker: str) -> list[str]:
    """진입 전 위험공시·펀더 치명신호 라이브 재점검 — monitor._distress 재사용.

    사이드카는 최대 하루 낡았을 수 있다: monitor가 보유종목에 하던 체크를
    진입 전으로 당긴다(설계 §1 게이트 5). best-effort — 실패하면 빈 리스트.
    """
    import monitor

    return monitor._distress(market, ticker)


# --------------------------------------------------------------------------- #
# 출력
# --------------------------------------------------------------------------- #
def _fmt(market: str, v) -> str:
    if v is None:
        return "—"
    return f"{v:,.0f}원" if market == "KR" else f"${v:,.2f}"


def _checklist_md(finalists: list[dict], dropped_all: list[tuple[dict, str]],
                  regime: dict, risk_pct: float, today: str) -> str:
    out = [f"# 추천 깔때기 체크리스트 — {today}",
           "",
           "> `scripts/recommend.py` 산출. **매수 리스트가 아니다** — 아래 후보를 사람",
           "> 체크(negative screen, 종목당 15분, 베토 주 2건 상한)에 올려 3~5픽으로 좁힌다.",
           "> 규칙·숫자는 12주 고정 (docs/recommendation-design-2026-07-17.md).", ""]
    reg_parts = []
    for mk, above in regime.items():
        tag = "판정불가" if above is None else ("200일선↑ 진입가능" if above else "200일선↓ 신규차단(페이퍼만)")
        reg_parts.append(f"{mk} {tag}")
    out += [f"**레짐:** {' · '.join(reg_parts)}", ""]
    out += [f"**비용 리마인더:** 왕복 KR {COST_NOTE['KR'][0]}({COST_NOTE['KR'][1]}) · "
            f"US {COST_NOTE['US'][0]}({COST_NOTE['US'][1]}) — 검증 엣지 +1.3~3.8%p/픽의 "
            "12~35%가 비용. 2트랜치 분할해도 %비용은 동일(금액 비례).", ""]
    for r in finalists:
        mk, t = r["market"], r["ticker"]
        paper_only = regime.get(mk) is False
        head = (f"## {t} — {r.get('name', '')} ({mk}) · 점수 {r.get('점수')} · "
                f"낙폭 {r.get('하락률', 0):.0f}% · ATR {r.get('atr_pct', 0):.1f}%")
        if paper_only:
            head += " · ⚠️ 레짐↓ 페이퍼 전용"
        out.append(head)
        stop_txt = (f"{_fmt(mk, r.get('stop'))} (−{r.get('stop_pct', 0):.1f}%)"
                    if r.get("stop") else "—")
        size_txt = (f"{r.get('shares', 0):,}주 · 포지션 {_fmt(mk, r.get('pos_value'))} "
                    f"({r.get('pos_pct', 0):.1f}%, R {risk_pct:.1f}%)"
                    if r.get("shares") else "산출 불가")
        out += [f"- 진입초안 {_fmt(mk, r.get('close'))} · 손절초안 {stop_txt} · 수량초안 {size_txt}",
                "- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): ",
                "- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)",
                "- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)",
                "- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]",
                "- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): ",
                f"- 탈락 시: `python scripts/decide.py --ticker {t} --action 관망 --note \"<사유>\"`",
                f"- 채택 시: `python scripts/to_watchlist.py --tickers {t}` → 큐레이션 → "
                f"`python scripts/decide.py --ticker {t} --paper`  (첫 8주 페이퍼/반액)",
                ""]
    if dropped_all:
        out += ["## 게이트 탈락 (사유 기록 — 사후 검증 대상)", ""]
        for r, why in dropped_all:
            out.append(f"- {r['ticker']} ({r['market']}, 점수 {r.get('점수')}): {why}")
        out.append("")
    out += ["## 다음 단계", "",
            "- 확정 픽은 **당일~익일 현재가 부근 즉시** 1차 트랜치(50%) — 눌림 대기 금지 [검증]",
            "- 2차 트랜치 +2~4주 시간 기반 [재량] · 캘린더에 2차일·120d 리뷰일 기록",
            "- 관망 탈락도 반드시 decide.py로 기록 — 베토 실효성 검증 데이터", ""]
    return "\n".join(out)


def main() -> int:
    cfg = ps._load_portfolio()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--markets", nargs="+", default=["KR", "US"], choices=["KR", "US"])
    ap.add_argument("--top", type=int, default=15, help="시장별 랭킹 컷 (기본 15)")
    ap.add_argument("--types", nargs="+", default=["common", "preferred"],
                    help="포함 종목유형 (기본: 일일 알림과 동일 — CEF/ETF 혼입 방지)")
    ap.add_argument("--atr-max", type=float, default=8.0, help="[재량] ATR%% 상한 (기본 8)")
    ap.add_argument("--turnover-cap", type=float, default=3.0,
                    help="[재량] 포지션 ≤ 20일 평균 거래대금의 %% (기본 3)")
    ap.add_argument("--risk", type=float, default=cfg["risk_pct"],
                    help="사이징 초안 R%% (기본 portfolio.json — 첫 8주는 반액 권장)")
    ap.add_argument("--stop-atr-mult", type=float, default=2.5)
    ap.add_argument("--min-drop", type=int, default=50)
    ap.add_argument("--years", type=int, default=5)
    ap.add_argument("--snapshot", default=twl.DEFAULT_SNAPSHOT)
    ap.add_argument("--no-fresh-distress", action="store_true",
                    help="위험공시 라이브 재점검 생략 (빠름 — 사이드카 데이터만 신뢰)")
    ap.add_argument("--no-write", action="store_true", help="exports/ 체크리스트 파일 안 씀")
    args = ap.parse_args()

    print(f"스냅샷 로드·랭킹 중... ({'+'.join(ALERT_SET)})", flush=True)
    rows, px = _load_rows(args.snapshot, args.min_drop, args.years)
    regime = _regime(args.markets)

    finalists: list[dict] = []
    dropped_all: list[tuple[dict, str]] = []
    types = set(args.types)
    for mk in args.markets:
        # 유형필터를 랭크 컷 전에 — CEF가 알림 4위에 오르던 사건(2026-07-13 감사)과
        # 동일 패턴으로, ETF/펀드가 상위 15 슬롯을 차지하는 것을 막는다
        mrows = [r for r in rows if r.get("market") == mk
                 and r.get("_security_type", "common") in types][: args.top]
        _attach_drafts(mrows, px, args.stop_atr_mult, cfg, args.risk)
        kept, dropped = apply_gates(mrows, atr_max=args.atr_max,
                                    turnover_cap_pct=args.turnover_cap)
        # 게이트 6: 진입 전 위험공시·치명신호 라이브 재점검 (best-effort)
        if not args.no_fresh_distress:
            still = []
            for r in kept:
                flags = _fresh_distress(mk, r["ticker"])
                if flags:
                    dropped.append((r, "위험공시 재점검: " + " | ".join(flags)))
                else:
                    still.append(r)
            kept = still
        finalists += kept
        dropped_all += dropped

    today = date.today().isoformat()
    reg_txt = " · ".join(
        f"{mk} {'판정불가' if a is None else ('200일선↑' if a else '200일선↓ 신규차단')}"
        for mk, a in regime.items())
    print(f"\n레짐: {reg_txt}")
    print(f"비용: 왕복 KR {COST_NOTE['KR'][0]} · US {COST_NOTE['US'][0]} "
          f"(vs 엣지 +1.3~3.8%p/픽 — 잠식 주의)")
    if not any(regime.values()):
        print("⚠️ 전 시장 200일선 아래 — 이번 주 신규 진입 없음, 아래 후보는 페이퍼 전용.")

    print(f"\n게이트 통과 {len(finalists)}종목 (상위 {args.top}/시장 → 사람 체크 후보):")
    if finalists:
        print(f"{'티커':<8}{'시장':<4}{'점수':>6}{'낙폭':>6}{'ATR%':>6}"
              f"{'진입초안':>12}{'손절초안':>12}{'수량':>8}{'비중':>6}")
        for r in finalists:
            mk = r["market"]
            print(f"{r['ticker']:<8}{mk:<4}{r.get('점수', 0):>6.1f}{r.get('하락률', 0):>5.0f}%"
                  f"{r.get('atr_pct', 0):>6.1f}{_fmt(mk, r.get('close')):>12}"
                  f"{_fmt(mk, r.get('stop')):>12}{r.get('shares', 0):>8,}"
                  f"{r.get('pos_pct', 0):>5.1f}%")
    print(f"\n게이트 탈락 {len(dropped_all)}종목:")
    for r, why in dropped_all:
        print(f"  {r['ticker']:<8}({r['market']}, {r.get('점수')}) — {why}")

    if not args.no_write:
        EXPORTS.mkdir(exist_ok=True)
        out_path = EXPORTS / f"recommend-{today}.md"
        out_path.write_text(_checklist_md(finalists, dropped_all, regime,
                                          args.risk, today), encoding="utf-8")
        print(f"\n✅ 체크리스트 저장: {out_path}")
        print("다음: 체크리스트(종목당 15분, 베토 주 2건 상한) → 3~5픽 → "
              "decide.py --paper (첫 8주) → 당일 1차 트랜치")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
