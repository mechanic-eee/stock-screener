"""SQLite schema + connection management.

Ported/adapted from the predecessor project's PRD §7.1 schema. Tables are
created idempotently. We keep the full schema (signals/news/fundamentals/...)
forward-compatible for later enrichment work, but the current pipeline only
populates `tickers`, `prices`, and `price_fetch_log`.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# project root = .../stock-screener  (this file: src/screener/data/db.py)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = ROOT / "data" / "screener.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickers (
  ticker TEXT PRIMARY KEY,
  market TEXT NOT NULL,
  name TEXT NOT NULL,
  sector TEXT,
  market_cap REAL,
  security_type TEXT DEFAULT 'common',
  is_excluded INTEGER DEFAULT 0,
  exclude_reason TEXT,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS prices (
  ticker TEXT NOT NULL,
  date TEXT NOT NULL,
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  adj_close REAL NOT NULL,
  volume INTEGER,
  PRIMARY KEY (ticker, date)
);
CREATE INDEX IF NOT EXISTS idx_prices_ticker_date ON prices(ticker, date);

-- our addition: per-ticker price freshness tracking for cache invalidation
CREATE TABLE IF NOT EXISTS price_fetch_log (
  ticker TEXT PRIMARY KEY,
  fetched_at TEXT NOT NULL,
  rows INTEGER
);

-- forward-compatible enrichment tables (unused by current pipeline)
CREATE TABLE IF NOT EXISTS signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL,
  signal_date TEXT NOT NULL,
  drawdown_pct REAL,
  macd_signal_type TEXT,
  macd_signal_age_days INTEGER,
  volume_ratio REAL,
  spike_flag INTEGER DEFAULT 0,
  score_drawdown REAL,
  score_macd_freshness REAL,
  score_volume_intensity REAL,
  score_news_sentiment REAL,
  score_fundamental REAL,
  score_mtf REAL,
  catalyst_bonus REAL DEFAULT 0,
  total_score REAL,
  details_json TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS alert_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL,
  alert_date TEXT NOT NULL,
  total_score REAL,
  signal_id INTEGER,
  created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_alert_ticker_date ON alert_history(ticker, alert_date);

CREATE TABLE IF NOT EXISTS ops_meta (
  key TEXT PRIMARY KEY,
  value TEXT,
  updated_at TEXT
);

-- quarterly financials cache (PRD §7.1). One row per ticker+period.
CREATE TABLE IF NOT EXISTS fundamentals (
  ticker TEXT NOT NULL,
  period TEXT NOT NULL,              -- YYYY-MM-DD (quarter end) or YYYY-Qn
  revenue REAL,
  op_income REAL,
  net_income REAL,
  total_debt REAL,
  total_equity REAL,
  fetched_at TEXT,
  PRIMARY KEY (ticker, period)
);
CREATE INDEX IF NOT EXISTS idx_fundamentals_ticker ON fundamentals(ticker, period);

-- catalyst calendar (PRD §7.1). v1.0 tracks earnings dates only.
CREATE TABLE IF NOT EXISTS catalysts (
  ticker TEXT NOT NULL,
  event_type TEXT NOT NULL,           -- 'earnings'
  scheduled_date TEXT NOT NULL,       -- YYYY-MM-DD
  fetched_at TEXT,
  PRIMARY KEY (ticker, event_type, scheduled_date)
);
CREATE INDEX IF NOT EXISTS idx_catalysts_ticker ON catalysts(ticker);
"""


def init_db(db_path: str | Path = DEFAULT_DB) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(SCHEMA)
        _migrate(conn)
        conn.commit()
    finally:
        conn.close()


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns introduced after the first schema (CREATE IF NOT EXISTS
    won't alter an existing table)."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(tickers)")}
    if "security_type" not in cols:
        conn.execute("ALTER TABLE tickers ADD COLUMN security_type TEXT DEFAULT 'common'")


_initialized: set[str] = set()


def get_connection(db_path: str | Path = DEFAULT_DB) -> sqlite3.Connection:
    key = str(db_path)
    if key not in _initialized:
        init_db(db_path)  # idempotent; ensures schema exists once per process
        _initialized.add(key)
    # timeout/busy_timeout let concurrent writers wait instead of erroring — the
    # enrichment exports fan out fundamentals fetches across threads, each of
    # which may write to the cache.
    conn = sqlite3.connect(key, timeout=30)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def upsert_ops_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """INSERT INTO ops_meta(key, value, updated_at) VALUES (?, ?, ?)
           ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
        (key, value, now_iso()),
    )
    conn.commit()


def get_ops_meta(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM ops_meta WHERE key=?", (key,)).fetchone()
    return row[0] if row else None
