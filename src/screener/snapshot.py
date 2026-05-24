"""Candidate snapshot: serialize base-screen survivors for the hosted app.

The daily job runs the heavy scan (price fetch + base drawdown screen over the
full universe) and writes a small parquet of just the *candidates'* price
history. The hosted Streamlit app loads this snapshot (from a local path or a
raw GitHub URL) and runs the cheap interactive filters on top — so the UI stays
fully interactive without ever fetching thousands of tickers itself.

Parquet is long-format: one row per (ticker, date). A sidecar dict of
ticker->(market, name) is encoded in pandas attrs via a small meta frame.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import pandas as pd

from .models import TickerData

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATH = ROOT / "data" / "candidates.parquet"
# Sidecar published next to the candidates snapshot (same dir / same URL prefix):
# the market benchmark series, so the hosted app can run relative-strength
# without a live ^GSPC/KS11 fetch (which is blocked/rate-limited on the host).
BENCH_PATH = ROOT / "data" / "benchmarks.parquet"
BENCH_NAME = "benchmarks.parquet"


def export_candidates(candidates: list[TickerData], path: str | Path = DEFAULT_PATH) -> Path:
    """Write candidates' price history (+ name/market) to one parquet file."""
    frames = []
    for c in candidates:
        df = c.prices.reset_index()
        df = df.rename(columns={df.columns[0]: "date"})
        df["ticker"] = c.ticker
        df["market"] = c.market
        df["name"] = c.name
        df["security_type"] = c.security_type
        frames.append(df)
    if not frames:
        out = pd.DataFrame(columns=["ticker", "market", "name", "security_type", "date",
                                    "open", "high", "low", "close", "volume"])
    else:
        out = pd.concat(frames, ignore_index=True)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(path, index=False)
    return path


def _frame_to_candidates(df: pd.DataFrame) -> list[TickerData]:
    if df.empty:
        return []
    df["date"] = pd.to_datetime(df["date"])
    cands: list[TickerData] = []
    has_type = "security_type" in df.columns
    for ticker, g in df.groupby("ticker", sort=False):
        g = g.sort_values("date").set_index("date")
        prices = g[["open", "high", "low", "close", "volume"]].copy()
        cands.append(TickerData(
            ticker=str(ticker),
            market=str(g["market"].iloc[0]),
            name=str(g["name"].iloc[0]),
            prices=prices,
            security_type=str(g["security_type"].iloc[0]) if has_type else "common",
        ))
    return cands


def load_candidates(source: Optional[str | Path] = None) -> list[TickerData]:
    """Load candidates from a local parquet path or an http(s) URL."""
    src = str(source) if source is not None else str(DEFAULT_PATH)
    if src.startswith("http://") or src.startswith("https://"):
        import requests
        resp = requests.get(src, timeout=30)
        resp.raise_for_status()
        df = pd.read_parquet(io.BytesIO(resp.content))
    else:
        if not Path(src).exists():
            return []
        df = pd.read_parquet(src)
    return _frame_to_candidates(df)


def export_benchmarks(markets: list[str], path: str | Path = BENCH_PATH) -> Optional[Path]:
    """Fetch each market's benchmark series and write a small long-format parquet
    (market, date, close). Returns the path, or None if nothing was fetched."""
    from . import benchmark as benchmark_mod

    frames = []
    for market in markets:
        s = benchmark_mod.get_benchmark(market)
        if s is None or s.empty:
            continue
        df = s.rename("close").reset_index()
        df.columns = ["date", "close"]
        df["market"] = market
        frames.append(df)
    if not frames:
        return None
    out = pd.concat(frames, ignore_index=True)[["market", "date", "close"]]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(path, index=False)
    return path


def _read_parquet(src: str) -> Optional[pd.DataFrame]:
    try:
        if src.startswith("http://") or src.startswith("https://"):
            import requests
            resp = requests.get(src, timeout=30)
            resp.raise_for_status()
            return pd.read_parquet(io.BytesIO(resp.content))
        if Path(src).exists():
            return pd.read_parquet(src)
    except Exception:
        return None
    return None


def _sibling(source: Optional[str | Path], name: str) -> str:
    """Resolve a sibling artifact's path/URL next to the candidates snapshot."""
    if source is None:
        return str(BENCH_PATH)
    s = str(source)
    if s.startswith("http://") or s.startswith("https://"):
        return s.rsplit("/", 1)[0] + "/" + name
    return str(Path(s).parent / name)


def load_benchmarks(source: Optional[str | Path] = None) -> dict[str, pd.Series]:
    """Load the benchmark sidecar that sits next to the candidates snapshot."""
    df = _read_parquet(_sibling(source, BENCH_NAME))
    if df is None or df.empty:
        return {}
    df["date"] = pd.to_datetime(df["date"])
    out: dict[str, pd.Series] = {}
    for market, g in df.groupby("market", sort=False):
        out[str(market)] = g.sort_values("date").set_index("date")["close"]
    return out


def prime_benchmarks(source: Optional[str | Path] = None) -> dict[str, pd.Series]:
    """Load the benchmark sidecar and seed the benchmark cache (no-op if absent)."""
    from . import benchmark as benchmark_mod

    series = load_benchmarks(source)
    if series:
        benchmark_mod.prime(series)
    return series


def snapshot_meta(source: Optional[str | Path] = None) -> dict:
    """Lightweight info about a snapshot (ticker count, last date) without
    fully materializing TickerData."""
    src = str(source) if source is not None else str(DEFAULT_PATH)
    try:
        if src.startswith("http"):
            import requests
            df = pd.read_parquet(io.BytesIO(requests.get(src, timeout=30).content))
        elif Path(src).exists():
            df = pd.read_parquet(src)
        else:
            return {}
    except Exception:
        return {}
    if df.empty:
        return {"tickers": 0}
    return {
        "tickers": df["ticker"].nunique(),
        "last_date": str(pd.to_datetime(df["date"]).max().date()),
        "markets": sorted(df["market"].unique().tolist()),
    }
