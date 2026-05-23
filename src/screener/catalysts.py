"""Catalyst calendar: earnings dates fetch + cache (PRD §5.4.5).

Uses yfinance `get_earnings_dates()`, which covers both US and KR tickers (KR
via the .KS / .KQ suffix) — so no fragile 38커뮤니케이션 scraping is needed.
v1.0 tracks earnings only. Results cache to the `catalysts` SQLite table and
refresh weekly. Missing data -> unavailable (no warning, no bonus; fail-soft).
"""
from __future__ import annotations

import logging
import time
from datetime import date, datetime
from typing import Optional

import pandas as pd

from .data import db as db_mod
from .models import CatalystInfo

log = logging.getLogger(__name__)

REFRESH_DAYS = 7  # earnings calendar changes slowly; refresh weekly (PRD)


def _to_date(s: str) -> Optional[date]:
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _yf_symbols(market: str, ticker: str) -> list[str]:
    if market == "KR":
        return [f"{ticker}.KS", f"{ticker}.KQ"]  # KOSPI, then KOSDAQ
    return [ticker]


def _fetch_earnings_dates(market: str, ticker: str) -> list[date]:
    """All known earnings dates (past + upcoming) for a ticker, ascending."""
    import yfinance as yf

    for sym in _yf_symbols(market, ticker):
        try:
            ed = yf.Ticker(sym).get_earnings_dates(limit=16)
        except Exception:  # noqa: BLE001 — try next suffix / fail-soft
            continue
        if ed is not None and not ed.empty:
            return sorted({pd.Timestamp(i).date() for i in ed.index})
    return []


def _info_from_dates(dates: list[date], today: Optional[date] = None) -> CatalystInfo:
    today = today or date.today()
    if not dates:
        return CatalystInfo(available=False)
    future = [d for d in dates if d >= today]
    past = [d for d in dates if d < today]
    nxt = min(future) if future else None
    return CatalystInfo(
        available=True,
        next_earnings=nxt,
        days_until=(nxt - today).days if nxt else None,
        last_earnings=max(past) if past else None,
    )


# --------------------------------------------------------------------------- #
# Cache + public entry point
# --------------------------------------------------------------------------- #
def _load_cached(conn, ticker: str) -> Optional[list[date]]:
    row = conn.execute(
        "SELECT MAX(fetched_at) FROM catalysts WHERE ticker=? AND event_type='earnings'",
        (ticker,),
    ).fetchone()
    if not row or not row[0]:
        return None
    fetched = _to_date(row[0])
    if fetched and (date.today() - fetched).days > REFRESH_DAYS:
        return None  # stale
    rows = conn.execute(
        "SELECT scheduled_date FROM catalysts WHERE ticker=? AND event_type='earnings'",
        (ticker,),
    ).fetchall()
    return sorted(d for d in (_to_date(r[0]) for r in rows) if d)


def _save(conn, ticker: str, dates: list[date]) -> None:
    now = db_mod.now_iso()
    conn.executemany(
        "INSERT OR REPLACE INTO catalysts(ticker, event_type, scheduled_date, fetched_at)"
        " VALUES (?, 'earnings', ?, ?)",
        [(ticker, d.isoformat(), now) for d in dates],
    )
    conn.commit()


def get_catalyst(market: str, ticker: str, use_cache: bool = True,
                 max_retries: int = 3) -> CatalystInfo:
    """Fetch (or load cached) earnings dates and return the derived info.

    Always returns a CatalystInfo; `available=False` means no calendar found.
    """
    conn = db_mod.get_connection()
    try:
        if use_cache:
            cached = _load_cached(conn, ticker)
            if cached is not None:
                return _info_from_dates(cached)

        dates: list[date] = []
        for attempt in range(max_retries):
            try:
                dates = _fetch_earnings_dates(market, ticker)
                break
            except Exception as e:  # noqa: BLE001 — fail-soft
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    log.warning("catalyst fetch failed %s/%s: %s", market, ticker, e)
        if not dates:
            return CatalystInfo(available=False)
        try:
            _save(conn, ticker, dates)
        except Exception as e:  # noqa: BLE001
            log.warning("catalyst cache save failed %s/%s: %s", market, ticker, e)
        return _info_from_dates(dates)
    finally:
        conn.close()
