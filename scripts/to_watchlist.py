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

Ranking is by the base (drawdown) score unless --indicators turns optional
indicators on, in which case the composite (base + weighted indicators) ranks
the shortlist — far more discriminating than base alone (where many tie at 100).

Examples:
  python scripts/to_watchlist.py --top 10
  python scripts/to_watchlist.py --indicators relative_strength fundamental valuation --top 10
  python scripts/to_watchlist.py --indicators all --market US --dry-run
  python scripts/to_watchlist.py --list-indicators
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
# Indicator-weighted ranking helpers
# --------------------------------------------------------------------------- #
def _optional_keys() -> list[str]:
    """Optional filter keys that help rank offline: excludes the news filter
    (needs a key + network) and bonus filters (don't shape the weighted rank)."""
    from screener import engine
    from screener.filters.base import optional_filters

    engine.ensure_filters_loaded()
    return [f.key for f in optional_filters() if not f.needs_news and not f.is_bonus]


def _resolve_indicators(names: list[str]) -> dict[str, dict]:
    """Map requested indicator keys (or 'all') to {key: {}} — each filter uses
    its own defaults (apply_filters merges them), acting as scorer+gate."""
    from screener.filters.base import get

    available = _optional_keys()
    if any(n.lower() == "all" for n in names):
        return {k: {} for k in available}
    selected: dict[str, dict] = {}
    for n in names:
        try:
            get(n)
        except KeyError:
            raise SystemExit(f"unknown indicator '{n}'. 사용 가능: {', '.join(available)} (또는 all)")
        selected[n] = {}
    return selected


def _parse_weights(s: str | None) -> dict[str, float]:
    if not s:
        return {}
    out: dict[str, float] = {}
    for pair in s.split(","):
        pair = pair.strip()
        if not pair:
            continue
        k, _, v = pair.partition("=")
        out[k.strip()] = float(v)
    return out


# --------------------------------------------------------------------------- #
# Ranked rows from a source
# --------------------------------------------------------------------------- #
def _attach_atr(row: dict, prices, stop_mult: float) -> None:
    """Attach ATR%-based volatility + a suggested stop (close - mult*ATR) to a row.

    Uses the candidate's daily OHLC (already in the snapshot) — no extra fetch.
    Lets the watchlist seed arrive with a real stop instead of 'TBD'."""
    from screener import indicators

    close = prices["close"].dropna()
    if len(close) < 15:
        return
    high = prices["high"] if "high" in prices else None
    low = prices["low"] if "low" in prices else None
    atr = indicators.atr(high, low, prices["close"], window=14)
    a = float(atr.iloc[-1])
    last = float(close.iloc[-1])
    if last <= 0 or a != a:  # NaN guard
        return
    row["atr_pct"] = a / last * 100.0
    row["stop"] = max(0.0, last - stop_mult * a)


def _rows_from_snapshot(source: str, min_drop: int, years: int,
                        selected: dict | None = None, weights: dict | None = None,
                        stop_mult: float = 2.5) -> list[dict]:
    from screener import engine, snapshot

    engine.ensure_filters_loaded()
    cands = snapshot.load_candidates(source)
    # priming lets RS/valuation/fundamentals contribute without live fetches if
    # the sidecars exist (needed when --indicators turns those on for ranking).
    for fn in (snapshot.prime_benchmarks, snapshot.prime_valuations, snapshot.prime_fundamentals):
        try:
            fn(source)
        except Exception:  # noqa: BLE001
            pass
    base = {"years": years, "min_drop_pct": min_drop}
    rows = engine.apply_filters(cands, base_params=base, selected=selected or {},
                                weights=weights or None, fetch_news=False)
    # draft an ATR-based stop per row from the candidate's price history
    px_by_ticker = {c.ticker: c.prices for c in cands}
    for r in rows:
        px = px_by_ticker.get(r["ticker"])
        if px is not None and not px.empty:
            _attach_atr(r, px, stop_mult)
    return rows


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


def _draft_row(r: dict, today: str, stop_mult: float = 2.5) -> str:
    name, ticker, market = r["name"], r["ticker"], r["market"]
    drop = r.get("하락률")
    score = r.get("점수")
    close = r.get("close")
    atr_pct = r.get("atr_pct")
    stop = r.get("stop")
    thesis_bits = []
    if drop is not None:
        thesis_bits.append(f"5년고가 대비 {drop:.0f}% 낙폭")
    if score is not None:
        thesis_bits.append(f"스크리너 {score:.0f}점")
    if atr_pct is not None:
        thesis_bits.append(f"ATR {atr_pct:.1f}%")
    thesis = ", ".join(thesis_bits) + " (자동초안 — 확인 필요)" if thesis_bits else "(자동초안)"
    entry = f"현재가 {_fmt_price(market, close)} 부근" if close else "TBD"
    # ATR-based stop draft (close - mult*ATR); falls back to TBD without prices (CSV source)
    stop_cell = f"{_fmt_price(market, stop)} (≈{stop_mult:g}×ATR)" if stop else "TBD"
    cells = [f"{name} ({ticker})", thesis, entry, stop_cell, "TBD", "관심", today]
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
    ap.add_argument("--indicators", nargs="+", metavar="KEY", default=None,
                    help="rank by base + these indicators (or 'all'); each uses its default params "
                         "so it both scores and gates. Snapshot source only. --list-indicators to see keys. "
                         "기본값(미지정): 일일 알림과 동일한 검증 세트 "
                         "(fundamental valuation altman_z piotroski gross_profit atr_risk) — "
                         "base-only 랭킹은 검증상 동전던지기라 --base-only로만 선택 가능.")
    ap.add_argument("--base-only", action="store_true",
                    help="지표 없이 기본 낙폭 점수로만 랭킹 (비권장 — 코호트 실측: base 5/25 "
                         "시드 −10.7%%/승률30%% vs enrichment 6/25 +4.0%%/70%%, LOG 2026-07-11)")
    ap.add_argument("--weights", metavar="key=w,...", help="override indicator weights, e.g. relative_strength=0.3,fundamental=0.4")
    ap.add_argument("--list-indicators", action="store_true", help="print available indicator keys and exit")
    ap.add_argument("--min-drop", type=int, default=50, help="base drawdown %% (must match the snapshot)")
    ap.add_argument("--years", type=int, default=5)
    ap.add_argument("--stop-atr-mult", type=float, default=2.5,
                    help="auto-draft stop = close - this*ATR (default 2.5; snapshot source only)")
    ap.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST), help="WATCHLIST.md to merge into")
    ap.add_argument("--dry-run", action="store_true", help="preview rows without writing")
    args = ap.parse_args()

    if args.list_indicators:
        from screener.filters.base import get
        print("사용 가능한 지표 (key — 라벨, 기본가중치):")
        for k in _optional_keys():
            f = get(k)
            print(f"  {k:18s} — {f.label} (w={f.weight})")
        print("\n예: --indicators relative_strength fundamental valuation  |  --indicators all")
        return 0

    if args.csv and args.indicators:
        print("ERROR: --indicators는 가격 데이터가 필요해 스냅샷 소스에서만 동작합니다 (--csv와 함께 못 씀).", flush=True)
        return 1

    # Default ranking = the validated daily-alert enrichment set (mirrors
    # daily_scan --alert-indicators). Resolved AFTER the source branch: CSV rows
    # already carry the app's composite 점수, so csv -> no indicator pass.
    # base-only is opt-in only — the cohort tracking measured its damage.
    ALERT_SET = ["fundamental", "valuation", "altman_z", "piotroski",
                 "gross_profit", "atr_risk"]
    indicators_arg = args.indicators
    if indicators_arg is None and not args.csv:
        if args.base_only:
            indicators_arg = None
            print("⚠️ base-only 랭킹 — 검증상 동전던지기입니다 (base 코호트 −10.7%/30% vs "
                  "enrichment +4.0%/70%, LOG 2026-07-11).", flush=True)
        else:
            indicators_arg = ALERT_SET

    selected = _resolve_indicators(indicators_arg) if indicators_arg else {}
    weights = _parse_weights(args.weights)

    if args.csv:
        rows = _rows_from_csv(args.csv)
        print(f"source: csv {args.csv} ({len(rows)} rows)", flush=True)
    else:
        rows = _rows_from_snapshot(args.snapshot, args.min_drop, args.years, selected, weights,
                                   stop_mult=args.stop_atr_mult)
        ind = ("+".join(selected) if selected else "base-only")
        print(f"source: snapshot {args.snapshot} ({len(rows)} candidates) · 랭킹={ind}", flush=True)

    if args.market:
        rows = [r for r in rows if r["market"] in set(args.market)]
    if args.min_score:
        rows = [r for r in rows if r.get("점수", 0) >= args.min_score]

    if args.tickers:
        wanted = {t.strip() for t in args.tickers.split(",") if t.strip()}
        selected = [r for r in rows if r["ticker"] in wanted]
        missing = wanted - {r["ticker"] for r in selected}
        if missing:
            print(f"⚠️  소스에서 못 찾음: {', '.join(sorted(missing))} — 스냅샷에 없거나 "
                  "지표 게이트(치명 펀더신호 등)에서 탈락했을 수 있습니다. "
                  "게이트 탈락 여부 확인: --base-only로 재실행해 보세요.", flush=True)
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
        row_md = _draft_row(r, today, args.stop_atr_mult)
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
          f"논거·진입구간·손절(≈{args.stop_atr_mult:g}×ATR)은 자동초안이니 촉매와 함께 다듬으세요.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
