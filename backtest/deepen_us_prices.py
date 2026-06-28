"""Deepen the US price cache to N years for a higher-power US backtest.

The US validation is the underpowered arm (11 rebalance dates, ~30-70 names each)
because the price cache only holds ~5y. This force-fetches the FULL US common
universe at --years (default 10) into the SQLite cache. save_prices is
INSERT OR REPLACE on (ticker,date), so older rows MERGE in without corrupting the
existing recent rows. After this, re-export prices_us.parquet and re-run the
validation for ~2x the rebalance dates (closer to KR's power).

  python backtest/deepen_us_prices.py --years 10
then:
  python backtest/export_prices.py --market US --out exports/prices_us.parquet
  python backtest/composite_decile_backtest.py --market US --fundamentals edgar
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from screener.data import prices as P  # noqa: E402
from screener.data import universe as U  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=10)
    ap.add_argument("--types", nargs="+", default=["common"])
    ap.add_argument("--limit", type=int, default=None, help="첫 N개만 (테스트용)")
    args = ap.parse_args()

    rows = U.build_universe(["US"], include_types=tuple(args.types))
    if args.limit:
        rows = rows[: args.limit]
    print(f"US {args.types}: {len(rows)} tickers — {args.years}y로 강제 재fetch (캐시 병합)", flush=True)
    ok = fail = 0
    for i, r in enumerate(rows, 1):
        try:
            df = P.get_prices("US", r["ticker"], years=args.years, use_cache=False)
            if df is not None and not df.empty:
                ok += 1
            else:
                fail += 1
        except Exception:  # noqa: BLE001 — one bad ticker must not stop the deepening
            fail += 1
        if i % 200 == 0 or i == len(rows):
            print(f"  {i}/{len(rows)}  (ok {ok}, fail {fail})", flush=True)
    print(f"done: ok {ok}, fail {fail}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
