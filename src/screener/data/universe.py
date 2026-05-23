"""Build the KR + US ticker universe.

Ported from the predecessor project:
- US: NASDAQ Trader official symbol directory (NASDAQ + NYSE) with ETF / SPAC /
  preferred / warrant exclusion heuristics.
- KR: pykrx live KOSPI + KOSDAQ list with market-cap floor and preferred / SPAC
  / ETF exclusion.

Rows are normalized to our canonical shape:
    {ticker, market("KR"|"US"), name, sector, market_cap, is_excluded, exclude_reason}
`build_universe(markets)` caches into SQLite and returns only ACTIVE
(is_excluded == 0) rows for the requested market groups.
"""
from __future__ import annotations

import logging
from datetime import datetime
from io import StringIO

import pandas as pd
import requests

from . import cache

log = logging.getLogger(__name__)

NASDAQ_LIST_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LIST_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"

MIN_MARKET_CAP_KRW = 100_000_000_000  # ₩100B
MIN_MARKET_CAP_USD = 500_000_000      # $500M (applied lazily during price fetch)


# --------------------------------------------------------------------------- US
def _fetch_pipe_separated(url: str) -> pd.DataFrame:
    r = requests.get(url, timeout=60, headers={"User-Agent": "screener/1.0"})
    r.raise_for_status()
    lines = r.text.strip().split("\n")
    if lines[-1].startswith("File Creation"):
        lines = lines[:-1]
    return pd.read_csv(StringIO("\n".join(lines)), sep="|")


def list_us() -> list[dict]:
    nasdaq = _fetch_pipe_separated(NASDAQ_LIST_URL)
    nasdaq = nasdaq[nasdaq["Test Issue"] == "N"].rename(
        columns={"Symbol": "ticker", "Security Name": "name"})
    nasdaq["etf_flag"] = nasdaq.get("ETF", "N")

    other = _fetch_pipe_separated(OTHER_LIST_URL)
    other = other[other["Test Issue"] == "N"].rename(
        columns={"ACT Symbol": "ticker", "Security Name": "name"})
    exch = {"N": "NYSE", "A": "NYSE_AMERICAN", "P": "NYSE_ARCA", "Z": "BATS"}
    other["exchange"] = other["Exchange"].map(exch).fillna("OTHER")
    other = other[other["exchange"] == "NYSE"]
    other["etf_flag"] = other.get("ETF", "N")

    df = pd.concat(
        [nasdaq[["ticker", "name", "etf_flag"]], other[["ticker", "name", "etf_flag"]]],
        ignore_index=True,
    ).drop_duplicates(subset=["ticker"]).reset_index(drop=True)

    df["is_excluded"] = 0
    df["exclude_reason"] = None

    def _exclude(mask, reason):
        m = mask & (df["is_excluded"] == 0)
        df.loc[m, "is_excluded"] = 1
        df.loc[m, "exclude_reason"] = reason

    _exclude(df["etf_flag"] == "Y", "etf")
    _exclude(df["name"].str.contains(
        r"\bETF\b|\bTrust\b|\bFund\b|\bIndex\b|\bAcquisition Corp\b",
        case=False, regex=True, na=False), "fund_or_spac")
    _exclude(df["ticker"].str.contains(r"\.|\^|\$|=", regex=True, na=False), "non_common_share")
    _exclude(df["name"].str.contains(r"Preferred|Pref\.", case=False, regex=True, na=False),
             "preferred_share")

    df["market"] = "US"
    df["sector"] = None
    df["market_cap"] = None
    return df[["ticker", "market", "name", "sector", "market_cap",
               "is_excluded", "exclude_reason"]].to_dict("records")


# --------------------------------------------------------------------------- KR
def list_kr(min_market_cap: float = MIN_MARKET_CAP_KRW) -> list[dict]:
    from pykrx import stock

    date = datetime.now().strftime("%Y%m%d")
    rows = []
    for _exchange in ("KOSPI", "KOSDAQ"):
        for t in stock.get_market_ticker_list(date, market=_exchange):
            try:
                rows.append({"ticker": t, "name": stock.get_market_ticker_name(t)})
            except Exception as e:  # noqa: BLE001
                log.warning("name fetch failed %s: %s", t, e)
    df = pd.DataFrame(rows)
    if df.empty:
        return []

    cap = stock.get_market_cap_by_ticker(date)
    if "시가총액" in cap.columns:
        cap = cap.rename(columns={"시가총액": "market_cap"})
        df = df.merge(cap[["market_cap"]], left_on="ticker", right_index=True, how="left")
    else:
        df["market_cap"] = None

    df["is_excluded"] = 0
    df["exclude_reason"] = None

    def _exclude(mask, reason):
        m = mask & (df["is_excluded"] == 0)
        df.loc[m, "is_excluded"] = 1
        df.loc[m, "exclude_reason"] = reason

    _exclude(df["name"].str.contains(r"우\s*$|우[ABC]\s*$|\(우\)", regex=True, na=False),
             "preferred_share")
    _exclude(df["name"].str.contains("스팩", na=False), "spac")
    _exclude(df["name"].str.contains(r"ETF|ETN|KODEX|TIGER|KOSEF|ARIRANG", regex=True, na=False),
             "etf_etn")
    if "market_cap" in df.columns:
        _exclude(df["market_cap"].fillna(0) < min_market_cap, "below_market_cap")

    df["market"] = "KR"
    df["sector"] = None
    return df[["ticker", "market", "name", "sector", "market_cap",
               "is_excluded", "exclude_reason"]].to_dict("records")


# ----------------------------------------------------------------------- public
def build_universe(markets: list[str], use_cache: bool = True) -> list[dict]:
    """Return ACTIVE (non-excluded) tickers for the requested groups, caching all."""
    if use_cache:
        cached = cache.load_universe()
        if cached is not None:
            return [r for r in cached if r["market"] in markets and not r.get("is_excluded")]

    rows: list[dict] = []
    if "KR" in markets:
        rows += list_kr()
    if "US" in markets:
        rows += list_us()
    cache.save_universe(rows)
    return [r for r in rows if not r.get("is_excluded")]
