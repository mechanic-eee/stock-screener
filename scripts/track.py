"""Track + review: how have the seeded / decided names actually done?

Closes the loop. Parses the investing project's WATCHLIST.md (seeds, incl. the
보류 section) and DECISIONS.md (open positions), fetches current prices, and
reports return-since-reference, days held, and distance to stop. Writes a
TRACKING.md snapshot next to them and prints a console table — so "did the
screener's picks work out" becomes visible instead of forgotten.

  python scripts/track.py            # console + writes stock-investing/TRACKING.md
  python scripts/track.py --dry-run  # console only
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

INVESTING = Path(__file__).resolve().parents[2] / "stock-investing"
WATCHLIST = INVESTING / "WATCHLIST.md"
DECISIONS = INVESTING / "DECISIONS.md"

_TICKER = re.compile(r"\(([A-Za-z0-9.]{1,7})\)")
_NUM = re.compile(r"-?\d[\d,]*\.?\d*")
_DATE = re.compile(r"(20\d\d)[-.](\d\d)[-.](\d\d)")
# 세 형식 전부: "스크리너 93점"(워치리스트) · "(점수 85)"(decide.py 포지션 행) ·
# "100점". decide 형식 누락으로 실포지션 5행의 점수가 전부 "—"로 소실됐었다
# (감사 2026-07-19 [상-4] — 점수 실효성 루프 단절).
_SCORE = re.compile(r"스크리너\s*([\d.]+)\s*점|점수\s*([\d.]+)|(\d+)\s*점")


def _num(cell: str):
    m = _NUM.search(cell.replace(" ", ""))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def _parse_date(cell: str):
    m = _DATE.search(cell)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _is_example(cells: list[str]) -> bool:
    joined = " ".join(cells)
    return joined.strip().startswith("_") or "예)" in joined or "_예" in joined


def _tables(text: str):
    """Yield (header_cells, [data_row_cells]) for each markdown table."""
    rows, cur = [], []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("|"):
            cur.append([c.strip() for c in s.strip("|").split("|")])
        elif cur:
            rows.append(cur)
            cur = []
    if cur:
        rows.append(cur)
    for tbl in rows:
        if len(tbl) < 2:
            continue
        header = tbl[0]
        data = [r for r in tbl[1:] if not set("".join(r)) <= set("-: ")]  # drop the |---| separator
        yield header, data


def _col(header: list[str], *names: str, exclude: str | None = None):
    for i, h in enumerate(header):
        if exclude and exclude in h:
            continue
        if any(n in h for n in names):
            return i
    return None


def _records_from(path: Path, source: str) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for header, data in _tables(path.read_text(encoding="utf-8")):
        ci_tkr = _col(header, "티커", "종목")
        ci_px = _col(header, "진입가", "진입", "현재가", "당시")  # "진입 관심구간" 셀의 '현재가 X 부근'
        ci_stop = _col(header, "손절")
        ci_qty = _col(header, "수량")
        ci_date = _col(header, "시드", "갱신", "날짜", exclude="촉매")  # avoid '촉매/이벤트 (날짜)'
        ci_status = _col(header, "상태")
        if ci_tkr is None or ci_px is None:
            continue
        for cells in data:
            if _is_example(cells) or len(cells) <= max(ci_tkr, ci_px):
                continue
            mt = _TICKER.search(cells[ci_tkr]) or re.search(r"\b(\d{6})\b", cells[ci_tkr])
            if mt:
                ticker = mt.group(1)
            else:
                # DECISIONS positions carry a bare ticker cell ("NVO" — no
                # parens); without this fallback US positions silently vanish
                # from tracking/monitoring (latent until the first US buy).
                bare = cells[ci_tkr].strip()
                if not re.fullmatch(r"[A-Za-z][A-Za-z0-9.]{0,6}", bare):
                    continue
                ticker = bare.upper()
            ref = _num(cells[ci_px])
            if ref is None or ref <= 0:
                continue
            sc = _SCORE.search(" ".join(cells))
            status = cells[ci_status] if ci_status is not None and ci_status < len(cells) else ""
            out.append({
                "ticker": ticker,
                "market": "KR" if ticker.isdigit() and len(ticker) == 6 else "US",
                "ref_price": ref,
                "shares": _num(cells[ci_qty]) if ci_qty is not None and ci_qty < len(cells) else None,
                "stop": _num(cells[ci_stop]) if ci_stop is not None and ci_stop < len(cells) else None,
                "date": _parse_date(cells[ci_date]) if ci_date is not None and ci_date < len(cells) else None,
                "status": status,
                "paper": "페이퍼" in status,
                "score": float(sc.group(1) or sc.group(2) or sc.group(3)) if sc else None,
                "source": source,
            })
    return out


def _merge_tranches(rows: list[dict]) -> dict:
    """같은 티커의 '보유' 트랜치 행들을 포지션 하나로 합성.

    수량 가중평단(수량 없으면 단순평균 폴백) · 진입일=최초 트랜치(보유기간 기준) ·
    손절=가장 최근 결정의 값 · 수량=합. 예전 단일 티커 키는 2차 트랜치가 1차
    기록을 통째로 덮어썼다(감사 2026-07-19 [중-9] — 8/10 2차 집행 전 수정)."""
    rows = sorted(rows, key=lambda r: (r["date"] is None, r["date"] or date.min))
    base = dict(rows[0])
    if len(rows) == 1:
        return base
    ws = [(r["ref_price"], r.get("shares") or 0) for r in rows]
    tot = sum(s for _, s in ws)
    if tot > 0:
        base["ref_price"] = sum(p * s for p, s in ws) / tot
        base["shares"] = tot
    else:
        base["ref_price"] = sum(p for p, _ in ws) / len(ws)
    stops = [r.get("stop") for r in rows if r.get("stop")]
    if stops:
        base["stop"] = stops[-1]
    base["source"] = f"{base.get('source', 'decision')}×{len(rows)}"
    return base


def _current_price(market: str, ticker: str):
    from screener.data import prices as prices_mod
    df = prices_mod.get_prices(market, ticker, years=1, max_age_days=1.0)
    if df is None or df.empty:
        return None
    return float(df["close"].iloc[-1])


def _fmt(market: str, v) -> str:
    if v is None:
        return "—"
    return f"{v:,.0f}원" if market == "KR" else f"${v:,.2f}"


def _cohort_summary(valid: list[dict]) -> list[str]:
    """One line per seed-date cohort (n, avg return, win, days) — a fair
    base-only vs enrichment comparison needs equal holding time, so we never
    pool across dates for the headline."""
    from collections import defaultdict

    cohorts: dict[object, list] = defaultdict(list)
    for r in valid:
        # paper trades aggregate separately: the 8-week paper-first phase must
        # never blend into the real-money cohort stats (recommendation-design §3)
        cohorts[(r["date"], bool(r.get("paper")))].append(r)
    lines = []
    for d, paper in sorted(cohorts, key=lambda x: (x[0] is None, x[0] or date.min, x[1])):
        cr = cohorts[(d, paper)]
        avg = sum(x["ret"] for x in cr) / len(cr)
        win = sum(1 for x in cr if x["ret"] > 0) / len(cr)
        days = next((x["days"] for x in cr if x["days"] is not None), None)
        scores = sorted({round(x["score"]) for x in cr if x["score"] is not None})
        stag = (f" · 점수 {scores[0]}~{scores[-1]}" if len(scores) > 1
                else (f" · 점수 {scores[0]}" if scores else ""))
        label = (d.isoformat() if d else "날짜없음") + (" [페이퍼]" if paper else "")
        dd = f"{days}d" if days is not None else "—"
        lines.append(f"{label} ({dd}, {len(cr)}종목{stag}): 평균 {avg:+.1f}%, 승률 {win:.0%}")
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="콘솔만, TRACKING.md 안 씀")
    args = ap.parse_args()

    # DECISIONS positions take priority over watchlist seeds for the same ticker.
    # Within DECISIONS, held tranche rows of one ticker merge into a single
    # position (weighted-average entry); closed rows stay separate episodes,
    # keyed (ticker, date, status) so nothing silently overwrites anything.
    from collections import defaultdict

    recs: dict[object, dict] = {}
    for r in _records_from(WATCHLIST, "watchlist"):
        recs.setdefault(r["ticker"], r)
    by_ticker: dict[str, list[dict]] = defaultdict(list)
    for r in _records_from(DECISIONS, "decision"):
        by_ticker[r["ticker"]].append(r)
    for tkr, drows in by_ticker.items():
        recs.pop(tkr, None)  # a decision replaces the watchlist seed row
        held = [r for r in drows if "보유" in (r.get("status") or "")]
        if held:
            recs[(tkr, "position")] = _merge_tranches(held)
        for r in drows:
            if r not in held:
                recs[(tkr, r.get("date"), r.get("status"))] = r
    items = list(recs.values())
    if not items:
        print("추적할 항목이 없습니다 (WATCHLIST/DECISIONS에 티커+가격 행 필요).")
        return 0

    print(f"추적 {len(items)}종목 — 현재가 조회 중...", flush=True)
    today = date.today()
    rows = []
    for it in items:
        cur = _current_price(it["market"], it["ticker"])
        ret = ((cur - it["ref_price"]) / it["ref_price"] * 100.0) if cur else None
        days = (today - it["date"]).days if it["date"] else None
        vs_stop = ((cur - it["stop"]) / cur * 100.0) if (cur and it["stop"]) else None
        rows.append({**it, "current": cur, "ret": ret, "days": days, "vs_stop": vs_stop})

    rows.sort(key=lambda r: (r["ret"] is None, -(r["ret"] or 0)))

    # console
    print(f"\n{'티커':<8}{'시장':<5}{'기준가':>12}{'현재가':>12}{'수익률':>9}{'손절여유':>9}{'보유일':>7}  소스")
    for r in rows:
        ret = f"{r['ret']:+.1f}%" if r["ret"] is not None else "—"
        vs = f"{r['vs_stop']:+.1f}%" if r["vs_stop"] is not None else "—"
        dd = f"{r['days']}d" if r["days"] is not None else "—"
        print(f"{r['ticker']:<8}{r['market']:<5}{_fmt(r['market'], r['ref_price']):>12}"
              f"{_fmt(r['market'], r['current']):>12}{ret:>9}{vs:>9}{dd:>7}  {r['source']}")

    valid = [r for r in rows if r["ret"] is not None]
    cohort_lines = _cohort_summary(valid)
    avg = (sum(r["ret"] for r in valid) / len(valid)) if valid else 0.0
    win = (sum(1 for r in valid if r["ret"] > 0) / len(valid)) if valid else 0.0
    if cohort_lines:
        print("\n코호트별 (시드일 — 보유기간이 다르면 직접 비교는 시간이 지나야 공정):")
        for ln in cohort_lines:
            print("  " + ln)
        print(f"  전체 {len(valid)}종목 평균 {avg:+.1f}% (보유기간 혼재 — 참고용)")

    if not args.dry_run:
        out = [f"# TRACKING — 시드/포지션 사후 추적", "",
               f"_생성: {datetime.now().isoformat(timespec='minutes')} · `scripts/track.py`_",
               "_**가격 수익률** — 거래비용·세금(해외주식 양도세 22%)·환율·배당 미반영. "
               "기준가=기록 시점(시드/결정) 가격이며 워치리스트 시드는 산 적 없는 가상 기준._", ""]
        if cohort_lines:
            out.append("**코호트별** (시드일 기준 — 보유기간 다르면 비교는 시간 필요):")
            out += [f"- {ln}" for ln in cohort_lines]
            out.append(f"- 전체 {len(valid)}종목 평균 {avg:+.1f}% _(보유기간 혼재, 참고용)_")
            out.append("")
        out += [
               "| 티커 | 시장 | 기준가 | 현재가 | 수익률 | 손절여유 | 보유일 | 점수 | 상태 | 소스 |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            out.append("| " + " | ".join([
                r["ticker"], r["market"], _fmt(r["market"], r["ref_price"]),
                _fmt(r["market"], r["current"]),
                f"{r['ret']:+.1f}%" if r["ret"] is not None else "—",
                f"{r['vs_stop']:+.1f}%" if r["vs_stop"] is not None else "—",
                f"{r['days']}d" if r["days"] is not None else "—",
                f"{r['score']:.0f}" if r["score"] is not None else "—",
                r["status"] or "—", r["source"]]) + " |")
        (INVESTING / "TRACKING.md").write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"\n✅ {INVESTING / 'TRACKING.md'} 갱신.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
