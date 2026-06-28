#!/usr/bin/env python3
"""Point-in-time US fundamentals from SEC EDGAR companyfacts (free, no key).

For a cohort date T, reconstructs the ANNUAL (10-K/FY) financial rows that were
PUBLIC by T — every fact carries a `filed` date, so we keep only `filed <= T`.
Rows come out in the exact schema `fundamentals._signals_from_rows` expects, so
the production fundamental signals (Piotroski / Altman / accruals / gross-
profitability / share-issuance) score with NO look-ahead and NO re-implementation.

Annual data is labeled `YYYY-12-31` and fed with market='KR' so the library's
`_annualized_flow` is a no-op (the figure is already a full year) — annual is in
fact the *correct* periodicity for Piotroski/Sloan/Novy-Marx (production computes
them on quarters, which is rougher).

Instant facts (Assets, equity, shares) and flow facts (revenue, NI, CFO, GP) are
joined on the XBRL `fy` (fiscal year), not the calendar end date, so non-December
fiscal-year-ends still align. Restatements are honored as-known-at-T: for each fy
we keep the latest fact filed on/before T.

total_debt is set to total liabilities (Assets − Equity): EDGAR has no single
interest-bearing "Total Debt" tag that's reliably populated, and Altman needs
total liabilities anyway. (debt_to_equity then reads as liabilities/equity — a
valid leverage proxy; the headline signals don't depend on the distinction.)
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

UA = "stock-screener-research yoobg1234@gmail.com"  # EDGAR requires a descriptive UA
CACHE = ROOT / "exports" / "edgar_cache"
_CIK_PATH = CACHE / "_cik_map.json"

# concept tag candidates (first present wins). dei fallback for shares handled below.
TAGS = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
                "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"],
    "op_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss"],
    "op_cash_flow": ["NetCashProvidedByUsedInOperatingActivities",
                     "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "gross_profit": ["GrossProfit"],
    "cogs": ["CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold"],
    "total_assets": ["Assets"],
    "total_equity": ["StockholdersEquity",
                     "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "current_assets": ["AssetsCurrent"],
    "current_liabilities": ["LiabilitiesCurrent"],
    "retained_earnings": ["RetainedEarningsAccumulatedDeficit"],
    "shares": ["CommonStockSharesOutstanding", "CommonStockSharesIssued"],
}
FLOW = {"revenue", "op_income", "net_income", "op_cash_flow", "gross_profit", "cogs"}


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read()


def load_cik_map() -> dict[str, str]:
    """ticker (upper) -> 10-digit zero-padded CIK."""
    CACHE.mkdir(parents=True, exist_ok=True)
    if _CIK_PATH.exists() and (time.time() - _CIK_PATH.stat().st_mtime) < 30 * 86400:
        return json.loads(_CIK_PATH.read_text(encoding="utf-8"))
    raw = json.loads(_get("https://www.sec.gov/files/company_tickers.json"))
    out = {}
    for row in raw.values():
        out[str(row["ticker"]).upper()] = f"{int(row['cik_str']):010d}"
    _CIK_PATH.write_text(json.dumps(out), encoding="utf-8")
    return out


def fetch_companyfacts(cik: str, throttle: float = 0.12):
    """Cached companyfacts JSON for one CIK (None if EDGAR has none)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    fp = CACHE / f"CIK{cik}.json"
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            pass
    try:
        data = _get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        time.sleep(throttle)  # EDGAR fair-access: <10 req/s
        fp.write_bytes(data)
        return json.loads(data)
    except Exception:
        # negative-cache so we don't re-hit a 404 (foreign filer / no XBRL)
        fp.write_text("null", encoding="utf-8")
        return None


def _facts_for(cf: dict, field: str) -> list[dict]:
    g = cf.get("facts", {}).get("us-gaap", {})
    for tag in TAGS[field]:
        node = g.get(tag)
        if node:
            units = node["units"]
            unit = "USD" if "USD" in units else ("shares" if "shares" in units else next(iter(units)))
            return units[unit]
    if field == "shares":
        dei = cf.get("facts", {}).get("dei", {}).get("EntityCommonStockSharesOutstanding")
        if dei:
            u = dei["units"]
            return u[next(iter(u))]
    return []


def _annual_by_end(facts: list[dict], T: str, is_flow: bool) -> dict[str, float]:
    """end-date -> val for annual (FY/10-K) facts public by T (latest filed per end).

    KEY ON `end`, NOT on `fy`: a fact's `fy`/`fp` describe the *filing* it came in,
    so each 10-K's embedded prior-year comparatives all share the filing's fy —
    grouping by fy lets a comparative column overwrite the current-year figure
    (the scramble bug found in adversarial review). The `end` date is the true
    period end, so grouping by it aligns instant + flow facts to the same fiscal
    year. Restatements are honored as-known-at-T: latest `filed <= T` per end.
    """
    out: dict[str, tuple[str, float]] = {}  # end -> (filed, val)
    for f in facts:
        filed = str(f.get("filed", ""))
        if not filed or filed > T:
            continue
        if f.get("fp") != "FY" or f.get("form") not in ("10-K", "10-K/A"):
            continue
        e = f.get("end")
        val = f.get("val")
        if not e or val is None:
            continue
        if is_flow:
            s = f.get("start")
            if not s:
                continue
            try:
                dur = (date.fromisoformat(e[:10]) - date.fromisoformat(s[:10])).days
            except ValueError:
                continue
            if not (350 <= dur <= 380):  # full fiscal year only (drops quarters/9-mo)
                continue
        if e not in out or filed > out[e][0]:
            out[e] = (filed, float(val))
    return {e: v[1] for e, v in out.items()}


def pit_rows(cf: dict, T: str, max_years: int = 3) -> list[dict]:
    """Annual rows public by date T (newest first), in the _signals_from_rows schema.

    Rows are joined on the fiscal-year-END date so instant (Assets/equity) and flow
    (revenue/NI/CFO) figures come from the SAME fiscal year. The period is still
    labeled `YYYY-12-31` (calendar year of the end) so the KR-path annualization
    no-op holds (months=12 -> x1) and consecutive years are ~365d apart for YoY.
    """
    series = {fld: _annual_by_end(_facts_for(cf, fld), T, fld in FLOW) for fld in TAGS}
    ends = sorted(series["total_assets"].keys(), reverse=True) or \
        sorted(series["net_income"].keys(), reverse=True)
    rows = []
    for end in ends[:max_years]:
        def g(fld):
            return series[fld].get(end)
        rev, gp = g("revenue"), g("gross_profit")
        if gp is None and rev is not None and g("cogs") is not None:
            gp = rev - g("cogs")
        ta, eq = g("total_assets"), g("total_equity")
        total_debt = (ta - eq) if (ta is not None and eq is not None) else None
        rows.append({
            "period": f"{int(end[:4])}-12-31",
            "revenue": rev, "op_income": g("op_income"), "net_income": g("net_income"),
            "total_debt": total_debt, "total_equity": eq, "shares": g("shares"),
            "op_cash_flow": g("op_cash_flow"), "gross_profit": gp,
            "current_assets": g("current_assets"), "current_liabilities": g("current_liabilities"),
            "total_assets": ta, "retained_earnings": g("retained_earnings"),
        })
    return rows


def _selftest():
    """Sanity check: AAPL as of a few dates should produce sensible signals."""
    from screener import fundamentals as fund
    cmap = load_cik_map()
    for tk in ("AAPL", "F", "GE"):
        cik = cmap.get(tk)
        if not cik:
            print(f"{tk}: no CIK"); continue
        cf = fetch_companyfacts(cik)
        if not cf:
            print(f"{tk}: no companyfacts"); continue
        for T in ("2019-06-30", "2022-06-30", "2024-06-30"):
            rows = pit_rows(cf, T)
            fb = fund._signals_from_rows(rows, market="KR")
            cur = rows[0]["period"] if rows else "—"
            z = f"{fb.altman_z:.2f}" if fb.altman_z is not None else "None"
            gp = f"{fb.gross_profitability:.3f}" if fb.gross_profitability is not None else "None"
            ac = f"{fb.accrual_ratio:+.3f}" if fb.accrual_ratio is not None else "None"
            ds = f"{fb.share_change_yoy:+.3f}" if fb.share_change_yoy is not None else "None"
            print(f"{tk} @ {T}: annual≤T {cur} ({len(rows)}r) | "
                  f"F={fb.f_score} Z={z} accr={ac} GP={gp} dShares={ds}")


if __name__ == "__main__":
    _selftest()
