"""CLI batch scan — also doubles as a no-UI smoke test.

Examples:
  python scan.py --markets US --limit 15
  python scan.py --markets KR US --limit 300 --min-drop 80 --macd
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from screener import engine  # noqa: E402
from screener.filters.base import optional_filters  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Drawdown stock screener (CLI).")
    ap.add_argument("--markets", nargs="+", default=["US"], choices=["KR", "US"])
    ap.add_argument("--years", type=int, default=5)
    ap.add_argument("--min-drop", type=int, default=80, help="min %% drop from N-year high")
    ap.add_argument("--limit", type=int, default=20, help="cap tickers scanned (0=all)")
    ap.add_argument("--macd", action="store_true", help="also require recent MACD bullish cross")
    args = ap.parse_args()

    base_params = {"years": args.years, "min_drop_pct": args.min_drop}
    print(f"universe={args.markets} limit={args.limit} base: -{args.min_drop}% / {args.years}y")

    def cb(i, total, ticker):
        print(f"\r  {i}/{total} {ticker:<12}", end="", flush=True)

    cands = engine.build_candidates(
        args.markets, base_params=base_params, years=args.years,
        limit=(args.limit or None), progress_cb=cb,
    )
    print(f"\nbase-screen survivors: {len(cands)}")

    selected = {}
    if args.macd:
        selected["macd_cross"] = next(f for f in optional_filters() if f.key == "macd_cross").defaults()

    rows = engine.apply_filters(cands, base_params=base_params, selected=selected)
    print(f"after optional filters: {len(rows)}\n")
    for r in rows[:50]:
        extras = " ".join(f"{k}={v}" for k, v in r.items()
                          if k not in {"ticker", "name", "market", "close", "하락률"})
        print(f"  [{r['market']}] {r['ticker']:<10} {r['name'][:18]:<18} "
              f"close={r['close']:.2f}  {extras}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
