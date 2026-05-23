"""Build the ticker universe for KR and US markets.

KR: pulled live from pykrx (full KOSPI + KOSDAQ listing + names).
US: yfinance has no listing endpoint, so the US universe comes from a CSV at
``config/us_universe.csv`` (columns: ticker,name). A small seed list is used
if that file is absent. Expand it by dropping in the official NASDAQ/NYSE
listing (see README).

Each universe row is a dict: {ticker, name, market}.
"""
from __future__ import annotations

import csv
from pathlib import Path

from . import cache

ROOT = Path(__file__).resolve().parents[3]
US_CSV = ROOT / "config" / "us_universe.csv"

# Minimal seed so the tool runs before a full listing is supplied.
US_SEED = [
    ("AAPL", "Apple"), ("MSFT", "Microsoft"), ("NVDA", "NVIDIA"),
    ("AMZN", "Amazon"), ("GOOGL", "Alphabet"), ("META", "Meta"),
    ("TSLA", "Tesla"), ("INTC", "Intel"), ("PYPL", "PayPal"),
    ("DIS", "Walt Disney"), ("BA", "Boeing"), ("PFE", "Pfizer"),
    ("KO", "Coca-Cola"), ("NKE", "Nike"), ("F", "Ford"),
]


def list_kr() -> list[dict]:
    from pykrx import stock

    today = stock.get_nearest_business_day_in_a_week()
    rows: list[dict] = []
    for market in ("KOSPI", "KOSDAQ"):
        for code in stock.get_market_ticker_list(today, market=market):
            name = stock.get_market_ticker_name(code)
            rows.append({"ticker": code, "name": name, "market": "KR"})
    return rows


def list_us() -> list[dict]:
    if US_CSV.exists():
        rows: list[dict] = []
        with US_CSV.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                t = (r.get("ticker") or "").strip()
                if t:
                    rows.append({"ticker": t, "name": (r.get("name") or t).strip(), "market": "US"})
        if rows:
            return rows
    return [{"ticker": t, "name": n, "market": "US"} for t, n in US_SEED]


def build_universe(markets: list[str], use_cache: bool = True) -> list[dict]:
    if use_cache:
        cached = cache.load_universe()
        if cached is not None:
            return [r for r in cached if r["market"] in markets]
    rows: list[dict] = []
    if "KR" in markets:
        rows += list_kr()
    if "US" in markets:
        rows += list_us()
    cache.save_universe(rows)
    return rows
