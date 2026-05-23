"""Alert de-duplication / cooldown — PRD §5.6.

A ticker that was alerted is silenced for `base_days` *calendar* days. It can
re-alert sooner only if its new score beats the most recent alert's score by at
least `reset_increase` (a materially stronger signal). Only the single most
recent prior alert is the comparison baseline.

The decision is a pure function (`should_alert`) so it's unit-testable without a
DB; `filter_alerts` / `record_alerts` are the SQLite-backed wrappers that the
daily scan uses against the `alert_history` table.
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Optional

from .data import db as db_mod

DEFAULT_BASE_DAYS = 14
DEFAULT_RESET_INCREASE = 20.0
SCORE_KEY = "점수"


def _parse_date(s: str) -> date:
    return datetime.strptime(s[:10], "%Y-%m-%d").date()


def last_alert(conn: sqlite3.Connection, ticker: str) -> Optional[tuple[date, float]]:
    """Most recent prior alert for a ticker, as (date, score), or None."""
    row = conn.execute(
        "SELECT alert_date, total_score FROM alert_history "
        "WHERE ticker=? ORDER BY alert_date DESC, id DESC LIMIT 1",
        (ticker,),
    ).fetchone()
    if not row:
        return None
    return _parse_date(row[0]), float(row[1] if row[1] is not None else 0.0)


def should_alert(prev: Optional[tuple[date, float]], new_score: float, today: date,
                 base_days: int, reset_increase: float) -> tuple[bool, str]:
    """Decide whether to (re)alert. Returns (allow, human-readable reason)."""
    if prev is None:
        return True, "신규"
    prev_date, prev_score = prev
    age = (today - prev_date).days
    if age >= base_days:
        return True, f"쿨다운만료({age}일)"
    if new_score >= prev_score + reset_increase:
        return True, f"점수급등(+{new_score - prev_score:.0f})"
    return False, f"쿨다운({age}/{base_days}일, 직전 {prev_score:.0f})"


def filter_alerts(
    conn: sqlite3.Connection,
    rows: list[dict],
    today: Optional[date] = None,
    base_days: int = DEFAULT_BASE_DAYS,
    reset_increase: float = DEFAULT_RESET_INCREASE,
    score_key: str = SCORE_KEY,
) -> tuple[list[dict], list[dict]]:
    """Split score-ranked rows into (allowed, suppressed), order preserved.

    Each returned row gets a `_cooldown` reason string for logging.
    """
    today = today or date.today()
    allowed: list[dict] = []
    suppressed: list[dict] = []
    for r in rows:
        prev = last_alert(conn, r["ticker"])
        ok, reason = should_alert(prev, float(r.get(score_key, 0) or 0), today,
                                  base_days, reset_increase)
        tagged = {**r, "_cooldown": reason}
        (allowed if ok else suppressed).append(tagged)
    return allowed, suppressed


def record_alerts(
    conn: sqlite3.Connection,
    rows: list[dict],
    today: Optional[date] = None,
    score_key: str = SCORE_KEY,
) -> None:
    """Log the alerts that were actually sent into alert_history."""
    today = today or date.today()
    ts = today.isoformat()
    now = db_mod.now_iso()
    conn.executemany(
        "INSERT INTO alert_history(ticker, alert_date, total_score, created_at) "
        "VALUES (?, ?, ?, ?)",
        [(r["ticker"], ts, float(r.get(score_key, 0) or 0), now) for r in rows],
    )
    conn.commit()
