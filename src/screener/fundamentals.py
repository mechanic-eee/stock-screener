"""Quarterly fundamentals: fetch + cache + derived signals (PRD §5.4.3).

US via yfinance (no key). KR via DART OpenAPI (needs ``DART_API_KEY``); without
the key, KR returns an *unavailable* bundle so the ticker is scored neutral
(50) and never excluded — matching the PRD's fail-soft rule for missing data.

Period rows are normalized to a common shape across markets:
    {period: 'YYYY-MM-DD', revenue, op_income, net_income, total_debt, total_equity}
ordered most-recent first. `_signals_from_rows` then derives the bundle the same
way for both markets — the year-over-year comparison row is found by *date
distance* (~365 days), not a fixed index, so it tolerates missing quarters and
KR's single prior-year figure alike.

Results cache to the `fundamentals` SQLite table and refresh quarterly.
"""
from __future__ import annotations

import io
import logging
import os
import time
import zipfile
from datetime import date, datetime, timezone
from typing import Optional

import pandas as pd

from .data import db as db_mod
from .models import FundamentalsBundle

log = logging.getLogger(__name__)

REFRESH_DAYS = 80          # financials change at most quarterly
_YOY_TOLERANCE_DAYS = 60   # how far from "exactly 1 year ago" a YoY match may be


# --------------------------------------------------------------------------- #
# Derived-signal computation (market-agnostic)
# --------------------------------------------------------------------------- #
def _to_date(s: str) -> Optional[date]:
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _signals_from_rows(rows: list[dict]) -> FundamentalsBundle:
    """Compute the PRD §5.4.3 signals from normalized period rows."""
    rows = [r for r in rows if r.get("period")]
    if not rows:
        return FundamentalsBundle(available=False)
    rows = sorted(rows, key=lambda r: r["period"], reverse=True)
    cur = rows[0]

    revenue = cur.get("revenue")
    op_income = cur.get("op_income")
    equity = cur.get("total_equity")
    debt = cur.get("total_debt")

    op_margin = (op_income / revenue) if (op_income is not None and revenue) else None
    debt_to_equity = (debt / equity) if (debt is not None and equity and equity > 0) else None
    capital_impairment = equity is not None and equity <= 0

    # revenue YoY: the row closest to ~1 year before `cur` (within tolerance)
    revenue_yoy = None
    cur_d = _to_date(cur["period"])
    if cur_d is not None and revenue:
        best, best_gap = None, 1e9
        for r in rows[1:]:
            d = _to_date(r["period"])
            if d is None or r.get("revenue") in (None, 0):
                continue
            gap = abs((cur_d - d).days - 365)
            if gap < best_gap:
                best, best_gap = r, gap
        if best is not None and best_gap <= _YOY_TOLERANCE_DAYS:
            prev_rev = best["revenue"]
            revenue_yoy = (revenue - prev_rev) / abs(prev_rev)

    # 4 consecutive quarters of losses (needs >=4 quarterly net-income points)
    ni = [r.get("net_income") for r in rows[:4] if r.get("net_income") is not None]
    four_q_all_loss = len(ni) >= 4 and all(x < 0 for x in ni)

    return FundamentalsBundle(
        available=True,
        revenue_yoy=revenue_yoy,
        op_margin=op_margin,
        debt_to_equity=debt_to_equity,
        four_quarters_all_loss=four_q_all_loss,
        capital_impairment=capital_impairment,
        periods=len(rows),
    )


# --------------------------------------------------------------------------- #
# US — yfinance
# --------------------------------------------------------------------------- #
def _series_row(df: Optional[pd.DataFrame], *names: str):
    if df is None or df.empty:
        return None
    for n in names:
        if n in df.index:
            return df.loc[n]
    return None


def _fetch_us(ticker: str) -> list[dict]:
    import yfinance as yf

    tk = yf.Ticker(ticker)
    inc = tk.quarterly_income_stmt
    bs = tk.quarterly_balance_sheet
    if inc is None or inc.empty:
        return []
    rev = _series_row(inc, "Total Revenue", "Operating Revenue")
    opi = _series_row(inc, "Operating Income", "Total Operating Income As Reported")
    ni = _series_row(inc, "Net Income", "Net Income Common Stockholders")
    debt = _series_row(bs, "Total Debt")
    eq = _series_row(bs, "Stockholders Equity", "Common Stock Equity")

    def val(s, col):
        if s is None or col not in s.index:
            return None
        v = s.get(col)
        return None if pd.isna(v) else float(v)

    rows: list[dict] = []
    for col in inc.columns:
        rows.append({
            "period": pd.Timestamp(col).strftime("%Y-%m-%d"),
            "revenue": val(rev, col),
            "op_income": val(opi, col),
            "net_income": val(ni, col),
            "total_debt": val(debt, col),
            "total_equity": val(eq, col),
        })
    return [r for r in rows
            if any(r[k] is not None for k in ("revenue", "op_income", "net_income", "total_equity"))]


# --------------------------------------------------------------------------- #
# KR — DART OpenAPI (key-gated; best-effort, untested without a key)
# --------------------------------------------------------------------------- #
_DART_BASE = "https://opendart.fss.or.kr/api"
_corp_map: Optional[dict[str, str]] = None
# Match by canonical IFRS account_id first (exactly one consolidated-total line
# each — avoids grabbing a segment/sub-line that merely *contains* "매출"), then
# fall back to Korean account_nm for entity-specific tags.
_DART_ACCOUNT_IDS = {
    "revenue": ("ifrs-full_Revenue", "ifrs_Revenue", "dart_OperatingRevenue"),
    "op_income": ("dart_OperatingIncomeLoss", "ifrs-full_ProfitLossFromOperatingActivities"),
    "net_income": ("ifrs-full_ProfitLoss", "ifrs_ProfitLoss"),
    "total_debt": ("ifrs-full_Liabilities", "ifrs_Liabilities"),
    "total_equity": ("ifrs-full_Equity", "ifrs_Equity", "ifrs-full_EquityAttributableToOwnersOfParent"),
}
_DART_ACCOUNT_NAMES = {
    "revenue": ("수익(매출액)", "매출액", "영업수익"),
    "op_income": ("영업이익", "영업이익(손실)"),
    "net_income": ("당기순이익", "당기순이익(손실)", "분기순이익"),
    "total_debt": ("부채총계",),
    "total_equity": ("자본총계",),
}


def _dart_key() -> Optional[str]:
    return os.getenv("DART_API_KEY") or None


_CORP_MAP_PATH = db_mod.ROOT / "data" / "dart_corp_map.json"
_CORP_MAP_REFRESH_DAYS = 30


def _parse_corp_xml(xml: bytes) -> dict[str, str]:
    import xml.etree.ElementTree as ET

    out: dict[str, str] = {}
    for el in ET.fromstring(xml).iter("list"):
        stock = (el.findtext("stock_code") or "").strip()
        corp = (el.findtext("corp_code") or "").strip()
        if stock and corp:
            out[stock] = corp
    return out


def _load_corp_map(key: str) -> dict[str, str]:
    """stock_code (6-digit) -> DART corp_code (8-digit).

    DART's corpCode.xml endpoint is heavily rate-limited (it returns an HTML
    error page instead of the zip when throttled), so we download it at most
    once and cache to disk for `_CORP_MAP_REFRESH_DAYS`; later runs read the
    JSON. In-memory cache short-circuits within a process.
    """
    global _corp_map
    if _corp_map is not None:
        return _corp_map

    import json
    import requests

    # disk cache
    try:
        if _CORP_MAP_PATH.exists():
            age = time.time() - _CORP_MAP_PATH.stat().st_mtime
            if age < _CORP_MAP_REFRESH_DAYS * 86400:
                _corp_map = json.loads(_CORP_MAP_PATH.read_text(encoding="utf-8"))
                return _corp_map
    except Exception as e:  # noqa: BLE001
        log.warning("DART corp map disk-cache read failed: %s", e)

    # download
    try:
        resp = requests.get(f"{_DART_BASE}/corpCode.xml", params={"crtfc_key": key}, timeout=30)
        resp.raise_for_status()
        if not resp.content[:2] == b"PK":  # zip magic; HTML/JSON error page otherwise
            raise ValueError("corpCode endpoint returned non-zip (rate-limited or error)")
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            xml = zf.read(zf.namelist()[0])
        _corp_map = _parse_corp_xml(xml)
        try:
            _CORP_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
            _CORP_MAP_PATH.write_text(json.dumps(_corp_map), encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            log.warning("DART corp map disk-cache write failed: %s", e)
    except Exception as e:  # noqa: BLE001
        log.warning("DART corp map load failed: %s", e)
        _corp_map = {}
    return _corp_map


def _dart_report(key: str, corp: str, year: int, reprt: str) -> list[dict]:
    """One fnlttSinglAcntAll report -> normalized account rows.

    Each row: {account_id, account, sj, thstrm, frmtrm}. CFS (consolidated)
    first; if the company files no consolidated statements, retry OFS.
    """
    import requests

    def fetch(fs_div):
        params = {"crtfc_key": key, "corp_code": corp, "bsns_year": str(year),
                  "reprt_code": reprt, "fs_div": fs_div}
        r = requests.get(f"{_DART_BASE}/fnlttSinglAcntAll.json", params=params, timeout=30)
        data = r.json()
        if data.get("status") != "000":
            return []
        return [{
            "account_id": (item.get("account_id") or "").strip(),
            "account": (item.get("account_nm") or "").strip(),
            "sj": item.get("sj_div"),
            "thstrm": _parse_won(item.get("thstrm_amount")),
            "frmtrm": _parse_won(item.get("frmtrm_amount")),
        } for item in data.get("list", [])]

    return fetch("CFS") or fetch("OFS")


def _parse_won(s) -> Optional[float]:
    if s in (None, "", "-"):
        return None
    try:
        return float(str(s).replace(",", ""))
    except ValueError:
        return None


def _pick(report: list[dict], field: str):
    """Find the line for a field: by canonical IFRS account_id first, else name.

    Matching by id avoids picking a segment/sub-line whose Korean name merely
    contains the keyword; the name fallback covers entity-specific tags.
    """
    ids = _DART_ACCOUNT_IDS[field]
    for it in report:
        if it.get("account_id") in ids:
            return it
    names = _DART_ACCOUNT_NAMES[field]
    for it in report:
        if it["account"] in names:
            return it
    return None


# DART report code -> the quarter-end (MM-DD) the cumulative figures cover.
_REPRT_MONTH_DAY = {"11013": "03-31", "11012": "06-30", "11014": "09-30", "11011": "12-31"}


def _row_from_report(report: list[dict], year: int, reprt: str) -> dict:
    """Normalize one DART report's current-period (thstrm) amounts to a row."""
    def amt(field: str):
        it = _pick(report, field)
        return it["thstrm"] if it else None
    return {
        "period": f"{year}-{_REPRT_MONTH_DAY.get(reprt, '12-31')}",
        "revenue": amt("revenue"),
        "op_income": amt("op_income"),
        "net_income": amt("net_income"),
        "total_debt": amt("total_debt"),
        "total_equity": amt("total_equity"),
    }


def _fetch_kr(ticker: str) -> list[dict]:
    key = _dart_key()
    if not key:
        return []  # no key -> unavailable -> neutral (fail-soft)
    corp = _load_corp_map(key).get(ticker)
    if not corp:
        return []

    # Find the most recent available report, newest-likely first. (DART IS lines
    # often omit prior-period comparatives, so we don't rely on frmtrm.)
    ty = date.today().year
    candidates = [(ty, "11013"), (ty - 1, "11011"), (ty - 1, "11014"),
                  (ty - 1, "11012"), (ty - 1, "11013"), (ty - 2, "11011")]
    cur_year = cur_rc = None
    report: list[dict] = []
    for yr, rc in candidates:
        report = _dart_report(key, corp, yr, rc)
        if report:
            cur_year, cur_rc = yr, rc
            break
    if not report:
        return []

    rows = [_row_from_report(report, cur_year, cur_rc)]
    # prior-year, same period -> a clean same-period YoY baseline
    prior = _dart_report(key, corp, cur_year - 1, cur_rc)
    if prior:
        rows.append(_row_from_report(prior, cur_year - 1, cur_rc))
    return rows


# --------------------------------------------------------------------------- #
# Cache + public entry point
# --------------------------------------------------------------------------- #
def _load_cached(conn, ticker: str) -> Optional[list[dict]]:
    row = conn.execute(
        "SELECT MAX(fetched_at) FROM fundamentals WHERE ticker=?", (ticker,)
    ).fetchone()
    if not row or not row[0]:
        return None
    fetched = _to_date(row[0])
    if fetched and (date.today() - fetched).days > REFRESH_DAYS:
        return None  # stale
    cur = conn.execute(
        "SELECT period, revenue, op_income, net_income, total_debt, total_equity "
        "FROM fundamentals WHERE ticker=? ORDER BY period DESC", (ticker,)
    )
    cols = ("period", "revenue", "op_income", "net_income", "total_debt", "total_equity")
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _save(conn, ticker: str, rows: list[dict]) -> None:
    now = db_mod.now_iso()
    conn.executemany(
        "INSERT OR REPLACE INTO fundamentals"
        "(ticker, period, revenue, op_income, net_income, total_debt, total_equity, fetched_at)"
        " VALUES (?,?,?,?,?,?,?,?)",
        [(ticker, r["period"], r.get("revenue"), r.get("op_income"), r.get("net_income"),
          r.get("total_debt"), r.get("total_equity"), now) for r in rows],
    )
    conn.commit()


def latest_raw(ticker: str) -> Optional[dict]:
    """Latest cached period's raw figures (for valuation). None if not cached."""
    conn = db_mod.get_connection()
    try:
        r = conn.execute(
            "SELECT period, net_income, total_equity FROM fundamentals "
            "WHERE ticker=? ORDER BY period DESC LIMIT 1", (ticker,)
        ).fetchone()
        return {"period": r[0], "net_income": r[1], "total_equity": r[2]} if r else None
    finally:
        conn.close()


def get_fundamentals(market: str, ticker: str, use_cache: bool = True,
                     max_retries: int = 3) -> FundamentalsBundle:
    """Fetch (or load cached) fundamentals and return the derived bundle.

    Always returns a bundle; `available=False` means no usable data (treat as
    neutral, never exclude).
    """
    conn = db_mod.get_connection()
    try:
        if use_cache:
            cached = _load_cached(conn, ticker)
            if cached is not None:
                return _signals_from_rows(cached)

        rows: list[dict] = []
        for attempt in range(max_retries):
            try:
                rows = _fetch_kr(ticker) if market == "KR" else _fetch_us(ticker)
                break
            except Exception as e:  # noqa: BLE001 — fail-soft, never kill the scan
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    log.warning("fundamentals fetch failed %s/%s: %s", market, ticker, e)
        if not rows:
            return FundamentalsBundle(available=False)
        try:
            _save(conn, ticker, rows)
        except Exception as e:  # noqa: BLE001
            log.warning("fundamentals cache save failed %s/%s: %s", market, ticker, e)
        return _signals_from_rows(rows)
    finally:
        conn.close()
