"""Build the KR + US ticker universe, classified by security type.

Ported/extended from the predecessor project:
- US: NASDAQ Trader official symbol directory (NASDAQ + NYSE).
- KR: pykrx live KOSPI + KOSDAQ list with market-cap floor.

Every ticker is classified into `security_type` (not hard-excluded), so the
caller can choose which types to scan (default: common stock only). Quality
exclusion (`is_excluded`, e.g. below market cap) is kept separate from type.

Canonical row:
    {ticker, market("KR"|"US"), name, sector, market_cap, security_type,
     is_excluded, exclude_reason}
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from io import StringIO

import pandas as pd
import requests

from . import cache

log = logging.getLogger(__name__)

NASDAQ_LIST_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LIST_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"

MIN_MARKET_CAP_KRW = 100_000_000_000  # ₩100B

# selectable types
SECURITY_TYPES = ["common", "etf", "etn", "spac", "preferred", "warrant_unit", "fund"]
TYPE_LABELS = {
    "common": "보통주", "etf": "ETF", "etn": "ETN", "spac": "스팩(SPAC)",
    "preferred": "우선주", "warrant_unit": "워런트/유닛/권리", "fund": "펀드/신탁",
}


# --------------------------------------------------------------------- classify
def _classify_us(name: str, etf_flag: str, ticker: str) -> str:
    n = name or ""
    if etf_flag == "Y":
        return "etf"
    if re.search(r"\bETN\b|Exchange[- ]Traded Note", n, re.I):
        return "etn"
    if re.search(r"\bETF\b", n, re.I):
        return "etf"
    # instrument type (units/warrants/rights) takes priority over issuer type
    if re.search(r"\bWarrants?\b|\bUnits?\b|\bRights?\b", n, re.I) or re.search(r"[.\^$=]", ticker):
        return "warrant_unit"
    if re.search(r"\bAcquisition\b|\bSPAC\b|Blank Check", n, re.I):
        return "spac"
    # only "Preferred" marks preferred — ADS ("Depositary Shares ... common shares")
    # are common equity and must NOT be caught here
    if re.search(r"Preferred|\bPref\.?\b", n, re.I):
        return "preferred"
    if re.search(r"\bTrust\b|\bFund\b|\bIndex\b", n, re.I):
        return "fund"
    return "common"


def _classify_kr(name: str) -> str:
    n = name or ""
    if "ETN" in n:
        return "etn"
    if re.search(r"ETF|KODEX|TIGER|KOSEF|ARIRANG|KBSTAR|KINDEX|SOL |ACE |PLUS ", n):
        return "etf"
    if "스팩" in n:
        return "spac"
    if re.search(r"우\s*$|우[ABC]\s*$|\(우\)", n):
        return "preferred"
    return "common"


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

    df = df[df["ticker"].notna()].copy()
    df["ticker"] = df["ticker"].astype(str)
    df["name"] = df["name"].fillna("").astype(str)
    df["etf_flag"] = df["etf_flag"].fillna("N").astype(str)

    df["security_type"] = [
        _classify_us(n, f, t) for n, f, t in zip(df["name"], df["etf_flag"], df["ticker"])
    ]
    df["market"] = "US"
    df["sector"] = None
    df["market_cap"] = None
    df["is_excluded"] = 0
    df["exclude_reason"] = None
    return df[["ticker", "market", "name", "sector", "market_cap", "security_type",
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

    df["security_type"] = [_classify_kr(n) for n in df["name"]]
    df["is_excluded"] = 0
    df["exclude_reason"] = None
    # quality exclusion only (type is handled separately); apply cap to common stock
    if "market_cap" in df.columns:
        small = (df["market_cap"].fillna(0) < min_market_cap) & (df["security_type"] == "common")
        df.loc[small, "is_excluded"] = 1
        df.loc[small, "exclude_reason"] = "below_market_cap"

    df["market"] = "KR"
    df["sector"] = None
    return df[["ticker", "market", "name", "sector", "market_cap", "security_type",
               "is_excluded", "exclude_reason"]].to_dict("records")


# ----------------------------------------------------------------------- public
def build_universe(
    markets: list[str],
    include_types: list[str] | tuple[str, ...] = ("common",),
    use_cache: bool = True,
) -> list[dict]:
    """Return tickers for the requested market groups, filtered by security
    type (default: common only) and excluding quality-failed rows."""
    types = set(include_types)

    def _keep(r: dict) -> bool:
        return (bool(r.get("ticker"))
                and r["market"] in markets
                and r.get("security_type", "common") in types
                and not r.get("is_excluded"))

    if use_cache:
        cached = cache.load_universe()
        if cached is not None:
            return [r for r in cached if _keep(r)]

    rows: list[dict] = []
    if "KR" in markets:
        rows += list_kr()
    if "US" in markets:
        rows += list_us()
    cache.save_universe(rows)
    return [r for r in rows if _keep(r)]


def type_counts(markets: list[str]) -> dict:
    """Cached per-type counts for display (None if no cache yet)."""
    cached = cache.load_universe()
    if cached is None:
        return {}
    out: dict[str, int] = {}
    for r in cached:
        if r["market"] in markets and not r.get("is_excluded"):
            out[r.get("security_type", "common")] = out.get(r.get("security_type", "common"), 0) + 1
    return out
