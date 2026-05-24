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
# Enrichment sidecars: precomputed valuation/fundamentals bundles per ticker, so
# the hosted app can run those filters without live yfinance.info / DART calls
# (blocked/rate-limited on the host). Computed in the daily scan where the DART
# key + SQLite cache are present, baked here, primed by the app on load.
VAL_PATH = ROOT / "data" / "valuations.parquet"
VAL_NAME = "valuations.parquet"
FUND_PATH = ROOT / "data" / "fundamentals.parquet"
FUND_NAME = "fundamentals.parquet"


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


# --------------------------------------------------------------------------- #
# Enrichment sidecars (valuation / fundamentals)
# --------------------------------------------------------------------------- #
def _opt_float(v):
    return None if (v is None or pd.isna(v)) else float(v)


def _threaded_map(items, fn, max_workers, progress_cb):
    """Apply fn to each item, optionally across a thread pool (network I/O bound).

    Returns a list of (item, result). `fn` is expected to be fail-soft (never
    raise); any stray exception is swallowed so one bad ticker can't abort the
    whole snapshot. Results arrive in completion order, which is fine — each row
    is keyed by ticker.
    """
    results = []
    total = len(items)
    if max_workers and max_workers > 1 and total > 1:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = {ex.submit(fn, it): it for it in items}
            for i, fut in enumerate(as_completed(futs), 1):
                it = futs[fut]
                try:
                    results.append((it, fut.result()))
                except Exception:  # noqa: BLE001 — never abort the snapshot
                    pass
                if progress_cb:
                    progress_cb(i, total, it.ticker)
    else:
        for i, it in enumerate(items, 1):
            try:
                results.append((it, fn(it)))
            except Exception:  # noqa: BLE001
                pass
            if progress_cb:
                progress_cb(i, total, it.ticker)
    return results


def _enrich_targets(candidates: list[TickerData], types) -> list[TickerData]:
    """Only enrich security types where valuation/fundamentals are meaningful
    (common/preferred by default); ETFs/SPACs/warrants have no useful multiples."""
    wanted = set(types)
    return [c for c in candidates if getattr(c, "security_type", "common") in wanted]


def export_valuations(
    candidates: list[TickerData],
    path: str | Path = VAL_PATH,
    types=("common", "preferred"),
    max_workers: int = 8,
    progress_cb=None,
) -> Optional[Path]:
    """Fetch each candidate's valuation bundle and write a per-ticker parquet."""
    from . import valuation as valuation_mod

    targets = _enrich_targets(candidates, types)

    def _val(c):
        last = float(c.prices["close"].iloc[-1]) if not c.prices.empty else None
        return valuation_mod.get_valuation(c.market, c.ticker, last_price=last)

    pairs = _threaded_map(targets, _val, max_workers, progress_cb)
    rows = [{
        "ticker": c.ticker, "available": bool(vb.available),
        "per": vb.per, "pbr": vb.pbr, "roe": vb.roe, "dividend_yield": vb.dividend_yield,
    } for c, vb in pairs]
    out = pd.DataFrame(rows, columns=["ticker", "available", "per", "pbr", "roe", "dividend_yield"])
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(path, index=False)
    return path


def export_fundamentals(
    candidates: list[TickerData],
    path: str | Path = FUND_PATH,
    types=("common", "preferred"),
    max_workers: int = 8,
    progress_cb=None,
) -> Optional[Path]:
    """Fetch each candidate's derived fundamentals bundle and write a parquet."""
    from . import fundamentals as fundamentals_mod

    targets = _enrich_targets(candidates, types)
    pairs = _threaded_map(
        targets, lambda c: fundamentals_mod.get_fundamentals(c.market, c.ticker),
        max_workers, progress_cb,
    )
    rows = [{
        "ticker": c.ticker, "available": bool(fb.available),
        "revenue_yoy": fb.revenue_yoy, "op_margin": fb.op_margin,
        "debt_to_equity": fb.debt_to_equity,
        "four_quarters_all_loss": bool(fb.four_quarters_all_loss),
        "capital_impairment": bool(fb.capital_impairment), "periods": int(fb.periods),
    } for c, fb in pairs]
    out = pd.DataFrame(rows, columns=[
        "ticker", "available", "revenue_yoy", "op_margin", "debt_to_equity",
        "four_quarters_all_loss", "capital_impairment", "periods"])
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(path, index=False)
    return path


def load_valuations(source: Optional[str | Path] = None) -> dict:
    """Load the valuation sidecar -> {ticker: ValuationBundle}."""
    from .models import ValuationBundle

    df = _read_parquet(_sibling(source, VAL_NAME))
    if df is None or df.empty:
        return {}
    out = {}
    for r in df.itertuples(index=False):
        out[str(r.ticker)] = ValuationBundle(
            available=bool(r.available),
            per=_opt_float(r.per), pbr=_opt_float(r.pbr),
            roe=_opt_float(r.roe), dividend_yield=_opt_float(r.dividend_yield),
        )
    return out


def load_fundamentals(source: Optional[str | Path] = None) -> dict:
    """Load the fundamentals sidecar -> {ticker: FundamentalsBundle}."""
    from .models import FundamentalsBundle

    df = _read_parquet(_sibling(source, FUND_NAME))
    if df is None or df.empty:
        return {}
    out = {}
    for r in df.itertuples(index=False):
        out[str(r.ticker)] = FundamentalsBundle(
            available=bool(r.available),
            revenue_yoy=_opt_float(r.revenue_yoy), op_margin=_opt_float(r.op_margin),
            debt_to_equity=_opt_float(r.debt_to_equity),
            four_quarters_all_loss=bool(r.four_quarters_all_loss),
            capital_impairment=bool(r.capital_impairment),
            periods=int(r.periods) if not pd.isna(r.periods) else 0,
        )
    return out


def prime_valuations(source: Optional[str | Path] = None) -> dict:
    """Load the valuation sidecar and seed the valuation cache (no-op if absent)."""
    from . import valuation as valuation_mod

    m = load_valuations(source)
    if m:
        valuation_mod.prime(m)
    return m


def prime_fundamentals(source: Optional[str | Path] = None) -> dict:
    """Load the fundamentals sidecar and seed the fundamentals cache (no-op if absent)."""
    from . import fundamentals as fundamentals_mod

    m = load_fundamentals(source)
    if m:
        fundamentals_mod.prime(m)
    return m
