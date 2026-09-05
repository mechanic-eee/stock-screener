"""decide.py — 워치리스트 행 → 리스크 사이징 → DECISIONS 기록을 한 명령으로.

발굴→워치리스트→**[결정]**→사이징→추적 루프에서 '결정+사이징+기록'의 마찰을 없앤다.
지금 DECISIONS가 0건이라 점수 실효성(추적/리뷰)이 검증되지 못하는데, 그 입구를 연다.

WATCHLIST.md에서 티커 행을 찾아 진입(관심구간)·손절(ATR 자동초안)·점수·시장을 파싱하고,
position_size로 수량을 계산해 DECISIONS.md 「📌 포지션」 표에 한 줄을 덧붙인다. 매수 안 한
결정(관망/보류)은 「결정 로그」에 사유와 함께 남긴다("왜 안 샀나"가 더 값지다 — DECISIONS 규칙).

  python scripts/decide.py --ticker NVO                      # 자동초안 진입/손절로 매수 사이징
  python scripts/decide.py --ticker 025560 --entry 47000 --stop 34000
  python scripts/decide.py --ticker PGNY --action 관망 --note "거래대금 얇고 촉매 불명"
  python scripts/decide.py --ticker NVO --action 청산 --exit 55.00 --note "손절 도달"  # 보유행 상태→청산+수익률
  python scripts/decide.py --ticker NVO --dry-run            # 미리보기(쓰지 않음)
  python scripts/decide.py --ticker GEVO --action 판정 --verdict 관망 --src tip --px 1.40 --code 소멸 --note "..."
      # 매매 아닌 판정(베토/보류/관망/랭크컷/이연)을 구조화 트레일러와 함께 기록 — 대조군 사후추적의 입력

모든 기록은 DECISIONS.md(사람용) + decisions.jsonl(기계용, append-only)에 병기된다(2026-09-06 P1).
결정 로그 불릿 끝의 트레일러 `| verdict=… | src=… | px=… | code=… | recheck=…` 가 채굴 키다.

진입/손절을 안 주면 워치리스트 자동초안(현재가·ATR손절)을 쓴다 — 실제 체결가로 들어갈 땐
--entry/--stop으로 덮어써라(손절은 진입 전에 확정한다는 규칙 유지). 계좌·리스크는
position_size와 동일하게 gitignored data/portfolio.json(없으면 내장 기본값).
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import position_size as ps  # noqa: E402  (reuse size_position + portfolio loading + fmt)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]                 # stock-screener
INVEST = ROOT.parent / "stock-investing"                   # sibling project
WATCHLIST = INVEST / "WATCHLIST.md"
DECISIONS = INVEST / "DECISIONS.md"
JSONL = INVEST / "decisions.jsonl"      # 기계가독 병기 원장 (append-only)

_BUY_ACTIONS = {"매수", "추가매수"}
VERDICTS = ("베토", "보류", "관망", "랭크컷", "이연", "채택안함", "채택", "청산", "매수", "추가매수")
SOURCES = ("funnel", "tip", "rescreen", "holding", "auto-stop", "manual")


def _market_of(ticker: str) -> str:
    return "KR" if ticker.isdigit() and len(ticker) == 6 else "US"


def _trailer(verdict: str | None = None, src: str | None = None, px=None,
             code: str | None = None, recheck: str | None = None) -> str:
    """결정 로그 불릿 끝에 붙는 구조화 트레일러. 비어 있는 키는 생략."""
    parts = []
    if verdict:
        parts.append(f"verdict={verdict}")
    if src:
        parts.append(f"src={src}")
    if px is not None:
        parts.append(f"px={px:g}" if isinstance(px, (int, float)) else f"px={px}")
    if code:
        parts.append(f"code={code}")
    if recheck:
        parts.append(f"recheck={recheck}")
    return (" | " + " | ".join(parts)) if parts else ""


def _append_jsonl(rec: dict, path: Path | None = None) -> None:
    """decisions.jsonl에 한 줄 추가(실패해도 DECISIONS 기록은 살린다)."""
    import json
    try:
        pth = path or JSONL
        pth.parent.mkdir(parents=True, exist_ok=True)
        with pth.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ decisions.jsonl 기록 실패: {e}")


def _parse_price(text: str | None) -> float | None:
    """First price in a cell: handles '$45.88', '47,450원', '7.2만', ranges (low end)."""
    if not text:
        return None
    t = text.replace(",", "")
    m = re.search(r"([0-9]+\.?[0-9]*)\s*만", t)   # KR shorthand: 7.2만 -> 72000
    if m:
        return float(m.group(1)) * 10_000
    m = re.search(r"\$?\s*([0-9]+\.?[0-9]*)", t)
    return float(m.group(1)) if m else None


def _parse_score(text: str) -> int | None:
    m = re.search(r"스크리너\s*([0-9]+)\s*점", text)
    return int(m.group(1)) if m else None


def find_row(ticker: str):
    """Locate the ticker's watchlist row. Returns (market, cells) or (None, None).

    Market is inferred from the most recent 🇰🇷/🇺🇸 section header above the row.
    """
    if not WATCHLIST.exists():
        return None, None
    market = None
    pat = re.compile(r"\(" + re.escape(ticker) + r"\)", re.IGNORECASE)
    for line in WATCHLIST.read_text(encoding="utf-8").splitlines():
        if "🇰🇷" in line or "한국" in line:
            market = "KR"
        elif "🇺🇸" in line or "미국" in line:
            market = "US"
        if line.lstrip().startswith("|") and pat.search(line) and "예)" not in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4:
                return market, cells
    return None, None


def _insert_after_table(lines: list[str], header_marker: str, new_row: str) -> bool:
    """Insert new_row after the last `|`-row of the table under header_marker."""
    in_sec = False
    last_tbl = -1
    for i, ln in enumerate(lines):
        if header_marker in ln:
            in_sec = True
            continue
        if in_sec and ln.startswith("## "):
            break
        if in_sec and ln.lstrip().startswith("|"):
            last_tbl = i
    if last_tbl < 0:
        return False
    lines.insert(last_tbl + 1, new_row)
    return True


def _insert_log_bullet(lines: list[str], bullet: str) -> bool:
    """Insert a 결정 로그 bullet right after the section's blockquote (최신 위)."""
    in_sec = False
    for i, ln in enumerate(lines):
        if "🗒 결정 로그" in ln:
            in_sec = True
            continue
        if in_sec and not ln.startswith(">") and ln.strip() != "":
            lines.insert(i, bullet)
            lines.insert(i + 1, "")
            return True
    return False


def close_position(ticker: str, exit_px: float, note: str = "", date_str: str | None = None,
                   dry_run: bool = False, src: str = "manual", code: str | None = None) -> dict | None:
    """포지션 표의 `ticker` 보유행 **전부**(트랜치 포함)를 청산으로 바꾸고 결정 로그+jsonl에 남긴다.

    반환 {"ticker","exit","rows":[{"entry","ret","paper"}],"ret_avg","paper","bullet"} 또는
    None(보유행 없음). 예전 구현은 첫 행만 닫아 2차 트랜치가 '보유'로 남는 구멍이 있었다."""
    date_str = date_str or date.today().isoformat()
    mkt = _market_of(ticker)
    ecell = lambda v: f"{v:,.0f}" if mkt == "KR" else f"{v:,.2f}"  # noqa: E731
    lines = DECISIONS.read_text(encoding="utf-8").splitlines()
    closed: list[dict] = []
    for i, ln in enumerate(lines):
        if not ln.lstrip().startswith("|") or "예)" in ln:
            continue
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) < 10 or c[1] != ticker or "보유" not in c[8] or c[0].startswith("_"):
            continue
        entry = _parse_price(c[3])
        ret = ((exit_px - entry) / entry * 100.0) if entry else None
        paper = "페이퍼" in c[8]
        c[8] = "청산(페이퍼)" if paper else "청산"
        c[9] = f"{ecell(exit_px)} ({ret:+.1f}%)" if ret is not None else ecell(exit_px)
        lines[i] = "| " + " | ".join(c) + " |"
        closed.append({"entry": entry, "ret": ret, "paper": paper, "date": c[0]})
    if not closed:
        return None
    rets = [r["ret"] for r in closed if r["ret"] is not None]
    ret_avg = (sum(rets) / len(rets)) if rets else None
    paper = all(r["paper"] for r in closed)
    why = note or "(사유 미기재)"
    rtxt = ""
    if ret_avg is not None:
        rtxt = f" ({ret_avg:+.1f}%)" if len(closed) == 1 else \
            " (" + " / ".join(f"{r['date']} {r['ret']:+.1f}%" for r in closed if r["ret"] is not None) + ")"
    bullet = (f"- [{date_str}] {ticker} 청산{'(페이퍼)' if paper else ''} — {why}{rtxt}"
              + _trailer("청산", src, exit_px, code))
    _insert_log_bullet(lines, bullet)
    for r in closed:
        print(f"📌 청산: {ticker} {r['date']} 진입 {ecell(r['entry']) if r['entry'] else '?'} → {ecell(exit_px)}"
              + (f" ({r['ret']:+.1f}%)" if r["ret"] is not None else ""))
    if dry_run:
        print(f"📝 {bullet}\n   (dry-run — 쓰지 않음)")
        return {"ticker": ticker, "exit": exit_px, "rows": closed, "ret_avg": ret_avg, "paper": paper,
                "bullet": bullet}
    DECISIONS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _append_jsonl({"date": date_str, "ticker": ticker, "market": mkt, "action": "청산", "verdict": "청산",
                   "src": src, "px": exit_px, "code": code, "paper": paper, "ret_pct": ret_avg,
                   "rows": len(closed), "note": note})
    print(f"✅ 청산 기록 (보유행 {len(closed)}건 → 청산 + 결정 로그 + jsonl)")
    return {"ticker": ticker, "exit": exit_px, "rows": closed, "ret_avg": ret_avg, "paper": paper,
            "bullet": bullet}


def main() -> int:
    cfg = ps._load_portfolio()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ticker", required=True, help="워치리스트의 티커 (예: NVO, 025560)")
    ap.add_argument("--action", default="매수", choices=["매수", "추가매수", "관망", "보류", "청산", "판정"])
    ap.add_argument("--verdict", choices=list(VERDICTS), help="--action 판정: 베토/보류/관망/랭크컷/이연/채택안함")
    ap.add_argument("--src", choices=list(SOURCES), help="결정 출처: funnel(주간 깔때기)/tip(외부 팁)/rescreen(재상정)/holding(보유 점검)")
    ap.add_argument("--px", type=float, help="결정 시점 가격(대조군 기준가). 판정/관망/보류에 권장")
    ap.add_argument("--code", help="사유 코드: 희석/소멸/마진/밸류/이벤트/ATR/유동성/딜/손절/논거훼손 등")
    ap.add_argument("--recheck", help="재검토 날짜 YYYY-MM-DD (있으면 트레일러에 기록)")
    ap.add_argument("--entry", type=float, help="진입가 (기본: 워치리스트 자동초안 현재가)")
    ap.add_argument("--exit", dest="exit_px", type=float, help="청산가 (--action 청산)")
    ap.add_argument("--stop", type=float, help="손절가 (기본: 워치리스트 ATR 자동초안)")
    ap.add_argument("--risk", type=float, default=cfg["risk_pct"], help="1트레이드 리스크 %%")
    ap.add_argument("--max-pos", type=float, default=cfg["max_pos_pct"], help="1종목 최대 비중 %%")
    ap.add_argument("--account", type=float, help="계좌 크기 (기본: portfolio.json/내장)")
    ap.add_argument("--note", default="", help="논거/사유 (관망이면 필수에 가깝다)")
    ap.add_argument("--date", default=date.today().isoformat(), help="결정 날짜 (기본: 오늘)")
    ap.add_argument("--paper", action="store_true",
                    help="페이퍼 트레이드로 기록(상태 '보유(페이퍼)') — track가 실계좌와 분리 집계. "
                         "추천 파이프라인 첫 8주 페이퍼 우선 원칙용")
    ap.add_argument("--dry-run", action="store_true", help="쓰지 않고 미리보기")
    args = ap.parse_args()

    # ---- 청산: 포지션 표의 보유행 전부 → 청산 (트랜치 포함) ----
    if args.action == "청산":
        if args.exit_px is None:
            print("❌ --exit <청산가> 필요"); return 1
        res = close_position(args.ticker, args.exit_px, args.note, args.date, args.dry_run,
                             src=args.src or "manual", code=args.code)
        if res is None:
            print(f"❌ '{args.ticker}' 보유 포지션을 DECISIONS 포지션표에서 못 찾음 "
                  "(이미 청산됐거나 티커 확인)"); return 1
        return 0

    # ---- 판정: 매매 아닌 결정(베토/보류/관망/랭크컷/이연)을 트레일러와 함께 ----
    if args.action == "판정":
        if not args.verdict:
            print("❌ --verdict 필요 (베토/보류/관망/랭크컷/이연/채택안함)"); return 1
        market, cells = find_row(args.ticker)
        name = cells[0] if cells else args.ticker
        mkt = market or _market_of(args.ticker)
        why = args.note or "(사유 미기재 — --note 권장)"
        bullet = (f"- [{args.date}] {name} {args.verdict} — {why}"
                  + _trailer(args.verdict, args.src, args.px, args.code, args.recheck))
        print(f"📝 결정 로그: {bullet}")
        if args.dry_run:
            print("   (dry-run — 쓰지 않음)"); return 0
        lines = DECISIONS.read_text(encoding="utf-8").splitlines()
        if not _insert_log_bullet(lines, bullet):
            print("❌ 결정 로그 섹션을 못 찾음"); return 1
        DECISIONS.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _append_jsonl({"date": args.date, "ticker": args.ticker, "market": mkt, "action": "판정",
                       "verdict": args.verdict, "src": args.src, "px": args.px, "code": args.code,
                       "recheck": args.recheck, "note": args.note})
        print("✅ DECISIONS.md 결정 로그 + decisions.jsonl 기록")
        return 0

    market, cells = find_row(args.ticker)
    if cells is None:
        print(f"❌ '{args.ticker}'를 WATCHLIST.md 활성 목록에서 못 찾음. "
              f"(보류 섹션이거나 티커 표기 확인) — {WATCHLIST}")
        return 1
    name = cells[0]
    thesis_cell = cells[1] if len(cells) > 1 else ""
    entry = args.entry if args.entry is not None else _parse_price(cells[2] if len(cells) > 2 else None)
    stop = args.stop if args.stop is not None else _parse_price(cells[3] if len(cells) > 3 else None)
    score = _parse_score(thesis_cell)
    note = args.note or re.sub(r"\s*\(자동초안.*?\)", "", thesis_cell).strip()
    fmt = lambda v: ps._fmt(market, v)  # noqa: E731

    # ---- 관망/보류: 결정 로그에 사유 + 트레일러(px 없으면 워치리스트 현재가 초안) ----
    if args.action in {"관망", "보류"}:
        why = args.note or "(사유 미기재 — --note 권장)"
        px = args.px if args.px is not None else entry
        bullet = (f"- [{args.date}] {name} {args.action} — {why}" + (f" (스크리너 {score})" if score else "")
                  + _trailer(args.action, args.src or "funnel", px, args.code, args.recheck))
        print(f"📝 결정 로그: {bullet}")
        if args.dry_run:
            print("   (dry-run — 쓰지 않음)")
            return 0
        lines = DECISIONS.read_text(encoding="utf-8").splitlines()
        if not _insert_log_bullet(lines, bullet):
            print("❌ 결정 로그 섹션을 못 찾음"); return 1
        DECISIONS.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _append_jsonl({"date": args.date, "ticker": args.ticker, "market": market, "action": args.action,
                       "verdict": args.verdict or args.action, "src": args.src or "funnel", "px": px,
                       "code": args.code, "recheck": args.recheck, "score": score, "note": args.note})
        print("✅ DECISIONS.md 결정 로그 + decisions.jsonl 기록")
        return 0

    # ---- 매수/추가매수: 사이징 + 포지션 표 ----
    if entry is None or stop is None:
        print(f"❌ 진입/손절 파싱 실패 (진입={entry}, 손절={stop}). --entry/--stop로 지정.")
        return 1
    account = args.account if args.account is not None else (
        cfg["account_krw"] if market == "KR" else cfg["account_usd"])
    r = ps.size_position(entry, stop, account, args.risk, args.max_pos)
    if not r["ok"]:
        print(f"❌ {r['reason']}")
        return 1

    print(f"[{market}] {name}  ({args.action}{' · 페이퍼' if args.paper else ''})")
    print(f"  진입 {fmt(entry)} · 손절 {fmt(stop)} (-{r['stop_pct']:.1f}%) · "
          f"계좌 {fmt(account)} · 리스크 {args.risk:.1f}%" + (f" · 점수 {score}" if score else ""))
    print(f"  → 수량 {r['shares']:,}주 · 포지션 {fmt(r['position_value'])} (계좌 {r['position_pct']:.1f}%) · "
          f"손절시 −{fmt(r['risk_amount'])} (계좌 {r['risk_pct_actual']:.2f}%)"
          + ("  [최대비중 한도]" if r["capped_by_max_position"] else ""))
    if r["shares"] == 0:
        print("  ⚠️ 0주 — 손절폭 과대 또는 리스크% 과소. 손절 좁히거나 리스크%↑ 후 재실행.")
        return 1

    thesis = (note[:40] + ("…" if len(note) > 40 else "")) + (f" (점수 {score})" if score else "")
    cell = lambda v: f"{v:,.0f}" if market == "KR" else f"{v:,.2f}"  # noqa: E731 (table cell: KR=정수콤마, US=2소수)
    status = "보유(페이퍼)" if args.paper else "보유"
    row = (f"| {args.date} | {args.ticker} | {args.action} | {cell(entry)} | {cell(stop)} | "
           f"{r['shares']:,} | {r['position_pct']:.0f}% | {thesis} | {status} | — |")
    print(f"\n📌 포지션 행:\n{row}")
    if args.dry_run:
        print("   (dry-run — 쓰지 않음)")
        return 0
    lines = DECISIONS.read_text(encoding="utf-8").splitlines()
    if not _insert_after_table(lines, "📌 포지션", row):
        print("❌ 포지션 표를 못 찾음"); return 1
    DECISIONS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _append_jsonl({"date": args.date, "ticker": args.ticker, "market": market, "action": args.action,
                   "verdict": args.action, "src": args.src or "funnel", "px": entry, "stop": stop,
                   "shares": r["shares"], "position_pct": round(r["position_pct"], 1),
                   "paper": bool(args.paper), "score": score, "code": args.code, "note": note})
    print(f"✅ DECISIONS.md 포지션 표 + decisions.jsonl 기록 — 다음: track.py로 사후 추적")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
