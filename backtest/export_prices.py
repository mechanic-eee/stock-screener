"""Export cached SQLite prices to a parquet file for calibration.

The calibration backtest expects [ticker, date, adj_close, volume]. This reads
the local screener.db and writes that subset, optionally filtered by market.

Usage:
    python backtest/export_prices.py --market US --out exports/prices_us.parquet
    python backtest/export_prices.py --out exports/prices_all.parquet
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "screener.db"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", choices=["KR", "US"], default=None,
                    help="filter to one market group (default: all)")
    ap.add_argument("--out", default="exports/prices.parquet")
    args = ap.parse_args()

    if not DB.exists():
        print(f"no DB at {DB} — run a scan first to populate prices.", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(DB))
    try:
        if args.market:
            q = ("SELECT p.ticker, p.date, p.adj_close, p.volume FROM prices p "
                 "JOIN tickers t ON t.ticker = p.ticker WHERE t.market = ? ORDER BY p.ticker, p.date")
            df = pd.read_sql_query(q, conn, params=(args.market,))
        else:
            df = pd.read_sql_query(
                "SELECT ticker, date, adj_close, volume FROM prices ORDER BY ticker, date", conn)
    finally:
        conn.close()

    if df.empty:
        print("no price rows to export.", file=sys.stderr)
        return 1

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"wrote {len(df):,} rows, {df['ticker'].nunique()} tickers -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
