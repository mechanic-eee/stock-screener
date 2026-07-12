"""SQLite-backed store for price history and the ticker universe.

Replaces the earlier per-ticker pickle cache. The public functions keep the
same signatures (load_prices/save_prices/load_universe/save_universe) so the
engine and app are unchanged. Screening uses adjusted close: `load_prices`
returns a frame whose `close` column IS the adjusted close.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

import pandas as pd

from . import db


def screen_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Canonical screening frame — the WHOLE bar in adjusted terms.

    yfinance stores raw OHLC plus Adj Close. Screening must not mix raw
    open/high/low with the adjusted close: around dividends/splits the close
    would sit outside [low, high], flipping candle colors and corrupting
    true-range (ATR). Scale O/H/L by adj_close/close so the bar is internally
    consistent. KR (FDR) is already fully adjusted, so its factor is 1.
    """
    out = df.copy()
    factor = (out["adj_close"] / out["close"]).where(out["close"] > 0, 1.0).fillna(1.0)
    for col in ("open", "high", "low"):
        out[col] = out[col] * factor
    out["close"] = out["adj_close"]
    return out[["open", "high", "low", "close", "volume"]]


def _stale(fetched_at: str, max_age_days: float) -> bool:
    try:
        fetched = dt.datetime.fromisoformat(fetched_at)
    except ValueError:
        return True
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=dt.timezone.utc)
    return (dt.datetime.now(dt.timezone.utc) - fetched) > dt.timedelta(days=max_age_days)


def load_prices(market: str, ticker: str, max_age_days: float = 1.0) -> Optional[pd.DataFrame]:
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT fetched_at FROM price_fetch_log WHERE ticker=?", (ticker,)
        ).fetchone()
        if not row or _stale(row[0], max_age_days):
            return None
        df = pd.read_sql_query(
            "SELECT date, open, high, low, close, adj_close, volume "
            "FROM prices WHERE ticker=? ORDER BY date",
            conn, params=(ticker,),
        )
    finally:
        conn.close()
    if df.empty:
        return None
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    return screen_frame(df)  # adjusted close + O/H/L scaled to match


def save_prices(market: str, ticker: str, df: pd.DataFrame) -> None:
    """`df` is indexed by date with columns open/high/low/close/adj_close/volume."""
    db.init_db()
    conn = db.get_connection()
    try:
        recs = []
        for idx, r in df.iterrows():
            adj = _f(r.get("adj_close"))
            if adj is None:
                adj = _f(r.get("close"))
            if adj is None:
                continue  # adj_close is NOT NULL; skip unusable rows
            vol = r.get("volume")
            recs.append((
                ticker, pd.Timestamp(idx).strftime("%Y-%m-%d"),
                _f(r.get("open")), _f(r.get("high")), _f(r.get("low")),
                _f(r.get("close")), adj,
                int(vol) if pd.notna(vol) else None,
            ))
        conn.executemany(
            "INSERT OR REPLACE INTO prices"
            "(ticker,date,open,high,low,close,adj_close,volume) VALUES (?,?,?,?,?,?,?,?)",
            recs,
        )
        conn.execute(
            "INSERT OR REPLACE INTO price_fetch_log(ticker,fetched_at,rows) VALUES (?,?,?)",
            (ticker, db.now_iso(), len(df)),
        )
        conn.commit()
    finally:
        conn.close()


def _f(v):
    return float(v) if v is not None and pd.notna(v) else None


def market_fresh(market: str, max_age_days: float = 7.0) -> bool:
    """Whether this market's universe was built recently (per-market clock)."""
    conn = db.get_connection()
    try:
        v = db.get_ops_meta(conn, f"universe_built_at:{market}")
    finally:
        conn.close()
    return bool(v) and not _stale(v, max_age_days)


def load_universe() -> Optional[list[dict]]:
    """All cached ticker rows (freshness is tracked per-market elsewhere)."""
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT ticker, market, name, security_type, is_excluded, exclude_reason FROM tickers"
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return None
    return [
        {"ticker": t, "market": m, "name": n, "security_type": st,
         "is_excluded": x, "exclude_reason": r}
        for (t, m, n, st, x, r) in rows
    ]


def save_market_universe(market: str, rows: list[dict]) -> None:
    """Replace one market's tickers and stamp its per-market build time."""
    db.init_db()
    conn = db.get_connection()
    try:
        conn.execute("DELETE FROM tickers WHERE market=?", (market,))
        recs = [(
            r["ticker"], r["market"], r.get("name") or r["ticker"],
            r.get("sector"), r.get("market_cap"), r.get("security_type", "common"),
            int(r.get("is_excluded", 0) or 0), r.get("exclude_reason"),
            db.now_iso(),
        ) for r in rows]
        conn.executemany(
            "INSERT OR REPLACE INTO tickers"
            "(ticker,market,name,sector,market_cap,security_type,is_excluded,exclude_reason,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            recs,
        )
        conn.execute("DELETE FROM tickers WHERE ticker IS NULL OR ticker=''")
        conn.commit()
        db.upsert_ops_meta(conn, f"universe_built_at:{market}", db.now_iso())
    finally:
        conn.close()
