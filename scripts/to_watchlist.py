"""Send screener results to the stock-investing WATCHLIST.md.

Takes the top-N candidates (by composite score) and merges them into the
investing project's watchlist as `관심` rows — KR rows into the KR table, US
into the US table — with an auto-drafted thesis/entry line (drawdown + score,
current price) and TBD stop/catalyst for the user to refine. Idempotent: a
ticker already in the watchlist is skipped.

Source (in priority order):
  --csv PATH        a results CSV exported from the app, OR
  --snapshot URL    a candidates snapshot (raw URL or local path); default is
                    the live cloud snapshot on the repo's data branch.

Examples:
  python scripts/to_watchlist.py --top 10
  python scripts/to_watchlist.py --market US --min-score 70 --dry-run
  python scripts/to_watchlist.py --tickers AAPL,005930
  python scripts/to_watchlist.py --csv screener_results.csv --top 15
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]  # .../projects
DEFAULT_WATCHLIST = ROOT / "stock-investing" / "WATCHLIST.md"
DEFAULT_SNAPSHOT = "https://raw.githubusercontent.com/mechanic-eee/stock-screener/data/candidates.parquet"

KR_HEADER = "## 🇰🇷"
US_HEADER = "## 🇺🇸"


# --------------------------------------------------------------------------- #
# Ranked rows from a source
# --------------------------------------------------------------------------- #
def _rows_from_snapshot(source: str, min_drop: int, years: int) -> list[dict]:
    from screener import engine, snapshot

    engine.ensure_filters_loaded()
    cands = snapshot.load_candidates(source)
    # priming lets RS/valuation/fundamentals contribute if the sidecars exist,
    # but base score alone is enough to rank — prime best-effort, ignore failures.
    for fn in (snapshot.prime_benchmarks, snapshot.prime_valuations, snapshot.prime_fundamentals):
        try:
            fn(source)
        except Exception:  # noqa: BLE001
            pass
    base = {"years": years, "min_drop_pct": min_drop}
    return engine.apply_filters(cands, base_params=base, selected={})


def _rows_from_csv(path: str) -> list[dict]:
    import csv

    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        try:
            score = float(r.get("점수", 0) or 0)
        except ValueError:
            score = 0.0
        try:
            close = float(r.get("close", 0) or 0)
        except ValueError:
            close = 0.0
        try:
            drop = float(r.get("하락률", 0) or 0)
        except ValueError:
            drop = 0.0
        out.append({"ticker": r.get("ticker", "").strip(), "name": r.get("name", "").strip(),
                    "market": r.get("market", "").strip(), "점수": score, "close": close, "하락률": drop})
    out.sort(key=lambda x: x["점수"], reverse=True)
    return out


# --------------------------------------------------------------------------- #
# Watchlist row drafting
# --------------------------------------------------------------------------- #
def _fmt_price(market: str, close: float) -> str:
    if market == "KR":
        return f"{close:,.0f}원"
    return f"${close:,.2f}"


def _draft_row(r: dict, today: str) -> str:
    name, ticker, market = r["name"], r["ticker"], r["market"]
    drop = r.get("하락률")
    score = r.get("점수")
    close = r.get("close")
    thesis_bits = []
    if drop is not None:
        thesis_bits.append(f"5년고가 대비 {drop:.0f}% 낙폭")
    if score is not None:
        thesis_bits.append(f"스크리너 {score:.0f}점")
    thesis = ", ".join(thesis_bits) + " (자동초안 — 확인 필요)" if thesis_bits else "(자동초안)"
    entry = f"현재가 {_fmt_price(market, close)} 부근" if close else "TBD"
    cells = [f"{name} ({ticker})", thesis, entry, "TBD", "TBD", "관심", today]
    return "| " + " | ".join(cells) + " |"


# --------------------------------------------------------------------------- #
# Markdown table parse + insert
# --------------------------------------------------------------------------- #
_TICKER_RE = re.compile(r"\(([^)]+)\)\s*$")  # ticker in the trailing (...) of cell 1


def _existing_tickers(lines: list[str]) -> set[str]:
    out: set[str] = set()
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|") or s.startswith("|---") or "종목 (티커)" in s:
            continue
        first = s.strip("|").split("|", 1)[0].strip().strip("_").strip()
        m = _TICKER_RE.search(first)
        if m:
            out.add(m.group(1).strip())
    return out


def _insert_after_table(lines: list[str], header_prefix: str, new_rows: list[str]) -> list[str]:
    """Insert new_rows at the end of the data block of the table under the
    section whose header line starts with header_prefix."""
    n = len(lines)
    i = 0
    # find the section header
    while i < n and not lines[i].startswith(header_prefix):
        i += 1
    if i >= n:
        raise ValueError(f"section header not found: {header_prefix}")
    # find the table header row (starts with '|') within this section
    j = i + 1
    while j < n and not lines[j].lstrip().startswith("|"):
        if lines[j].startswith("## ") or lines[j].startswith("---"):
            raise ValueError(f"no table under section {header_prefix}")
        j += 1
    # advance past all contiguous table rows (header + separator + data)
    k = j
    while k < n and lines[k].lstrip().startswith("|"):
        k += 1
    # k is the first non-table line; insert before it (end of data block)
    return lines[:k] + new_rows + lines[k:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--snapshot", default=DEFAULT_SNAPSHOT, help="candidates snapshot (raw URL or local path)")
    src.add_argument("--csv", help="results CSV exported from the app")
    ap.add_argument("--top", type=int, default=10, help="how many top-scored candidates to send (default 10)")
    ap.add_argument("--min-score", type=float, default=0.0, help="only send candidates at/above this score")
    ap.add_argument("--market", nargs="+", choices=["KR", "US"], help="restrict to these markets")
    ap.add_argument("--tickers", help="comma-separated tickers to send (overrides --top selection)")
    ap.add_argument("--min-drop", type=int, default=50, help="base drawdown %% (must match the snapshot)")
    ap.add_argument("--years", type=int, default=5)
    ap.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST), help="WATCHLIST.md to merge into")
    ap.add_argument("--dry-run", action="store_true", help="preview rows without writing")
    args = ap.parse_args()

    if args.csv:
        rows = _rows_from_csv(args.csv)
        print(f"source: csv {args.csv} ({len(rows)} rows)", flush=True)
    else:
        rows = _rows_from_snapshot(args.snapshot, args.min_drop, args.years)
        print(f"source: snapshot {args.snapshot} ({len(rows)} candidates)", flush=True)

    if args.market:
        rows = [r for r in rows if r["market"] in set(args.market)]
    if args.min_score:
        rows = [r for r in rows if r.get("점수", 0) >= args.min_score]

    if args.tickers:
        wanted = {t.strip() for t in args.tickers.split(",") if t.strip()}
        selected = [r for r in rows if r["ticker"] in wanted]
        missing = wanted - {r["ticker"] for r in selected}
        if missing:
            print(f"⚠️  not found in source: {', '.join(sorted(missing))}", flush=True)
    else:
        selected = rows[: args.top]

    if not selected:
        print("보낼 후보가 없습니다 (필터를 완화하거나 소스를 확인하세요).", flush=True)
        return 0

    wl_path = Path(args.watchlist)
    if not wl_path.exists():
        print(f"ERROR: watchlist not found: {wl_path}", flush=True)
        return 1
    text = wl_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    existing = _existing_tickers(lines)
    today = date.today().isoformat()

    kr_rows, us_rows, skipped = [], [], []
    for r in selected:
        if r["ticker"] in existing:
            skipped.append(r["ticker"])
            continue
        row_md = _draft_row(r, today)
        (kr_rows if r["market"] == "KR" else us_rows).append(row_md)

    print(f"\n선택 {len(selected)}종목 → 신규 KR {len(kr_rows)} · US {len(us_rows)}"
          f"{(' · 이미있음 ' + str(len(skipped))) if skipped else ''}", flush=True)
    for md in kr_rows + us_rows:
        print("  " + md, flush=True)

    if not kr_rows and not us_rows:
        print("\n신규로 추가할 종목이 없습니다 (전부 이미 워치리스트에 있음).", flush=True)
        return 0

    if args.dry_run:
        print("\n[dry-run] 파일을 쓰지 않았습니다.", flush=True)
        return 0

    if kr_rows:
        lines = _insert_after_table(lines, KR_HEADER, kr_rows)
    if us_rows:
        lines = _insert_after_table(lines, US_HEADER, us_rows)
    wl_path.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    print(f"\n✅ {wl_path} 에 KR {len(kr_rows)} · US {len(us_rows)}종목 추가(상태=관심). "
          f"논거·진입구간은 자동초안이니 손절선·촉매와 함께 다듬으세요.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
