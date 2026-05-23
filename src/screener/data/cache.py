"""Local on-disk cache for price history and the candidate universe.

Uses pandas pickle (no pyarrow dependency, which avoids wheel gaps on very new
Python versions). Cache lives under ``data/`` (gitignored). Freshness is by
file mtime: data older than ``max_age_days`` is treated as stale.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Optional

import pandas as pd

# project root = .../stock-screener  (this file: src/screener/data/cache.py)
ROOT = Path(__file__).resolve().parents[3]
PRICE_DIR = ROOT / "data" / "prices"
META_PATH = ROOT / "data" / "universe.json"


def _price_path(market: str, ticker: str) -> Path:
    safe = ticker.replace("/", "_")
    return PRICE_DIR / market / f"{safe}.pkl"


def is_fresh(path: Path, max_age_days: float) -> bool:
    if not path.exists():
        return False
    age = dt.datetime.now() - dt.datetime.fromtimestamp(path.stat().st_mtime)
    return age <= dt.timedelta(days=max_age_days)


def load_prices(market: str, ticker: str, max_age_days: float = 1.0) -> Optional[pd.DataFrame]:
    path = _price_path(market, ticker)
    if not is_fresh(path, max_age_days):
        return None
    try:
        return pd.read_pickle(path)
    except Exception:
        return None


def save_prices(market: str, ticker: str, df: pd.DataFrame) -> None:
    path = _price_path(market, ticker)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(path)


def load_universe(max_age_days: float = 7.0) -> Optional[list[dict]]:
    if not is_fresh(META_PATH, max_age_days):
        return None
    try:
        return json.loads(META_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_universe(rows: list[dict]) -> None:
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    META_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
