"""Fetch price history for KR stocks delisted during the backtest window.

Survivorship-bias correction: the survivor-only price parquet omits names that
went to zero / were removed, which inflates backtested returns. FDR *does* serve
historical prices for delisted KR tickers, so we pull the ones delisted inside
the window and write them alongside the survivors, tagged with the delisting date
so the backtest can hold-to-delisting (forward return clamped to the last price).

Output: exports/prices_kr_delisted.parquet [ticker, date, adj_close, volume, delisting_date]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
WIN_START, WIN_END = "2021-04-01", "2026-05-22"
FETCH_FROM = "2017-01-01"  # enough lookback for the 5y-high drawdown


def main() -> int:
    import FinanceDataReader as fdr

    de = fdr.StockListing("KRX-DELISTING")
    de["DelistingDate"] = pd.to_datetime(de["DelistingDate"], errors="coerce")
    win = de[(de["DelistingDate"] >= WIN_START) & (de["DelistingDate"] <= WIN_END)].copy()
    if "SecuGroup" in win.columns:
        win = win[win["SecuGroup"] == "주권"]
    win = win.dropna(subset=["Symbol", "DelistingDate"])
    print(f"delisted (주권, in window): {len(win)} tickers", flush=True)

    frames, ok, empty, err = [], 0, 0, 0
    for i, (_, r) in enumerate(win.iterrows(), 1):
        code = str(r["Symbol"]).zfill(6)
        dd = r["DelistingDate"]
        try:
            df = fdr.DataReader(code, FETCH_FROM, dd.strftime("%Y-%m-%d"))
        except Exception:  # noqa: BLE001
            err += 1
            continue
        if df is None or df.empty or "Close" not in df.columns:
            empty += 1
            continue
        out = pd.DataFrame({
            "ticker": code,
            "date": pd.to_datetime(df.index),
            "adj_close": df["Close"].astype(float).values,
            "volume": df["Volume"].astype(float).values if "Volume" in df.columns else 0.0,
        })
        out["delisting_date"] = dd
        frames.append(out)
        ok += 1
        if i % 25 == 0 or i == len(win):
            print(f"  {i}/{len(win)}  ok={ok} empty={empty} err={err}", flush=True)
        time.sleep(0.15)  # be gentle on the source

    if not frames:
        print("no delisted prices fetched", file=sys.stderr)
        return 1
    allp = pd.concat(frames, ignore_index=True)
    outp = ROOT / "exports" / "prices_kr_delisted.parquet"
    outp.parent.mkdir(parents=True, exist_ok=True)
    allp.to_parquet(outp, index=False)
    print(f"wrote {len(allp):,} rows, {allp['ticker'].nunique()} tickers -> {outp}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
