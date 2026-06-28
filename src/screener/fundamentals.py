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
# Rows cached before this date predate the extended-fundamentals columns
# (op_cash_flow / total_assets / Altman / Piotroski inputs / audit signals), so
# their derived signals come back empty. Treat them as stale and refetch once,
# so the new filters actually populate instead of waiting out the 80-day cache.
_SCHEMA_CUTOFF = "2026-06-23"

# Per-process cache of precomputed derived bundles, keyed by ticker. The hosted
# app has neither a DART key nor the SQLite cache (screener.db isn't published),
# so the daily scan bakes the derived FundamentalsBundle into a sidecar and the
# app primes them here — get_fundamentals() then returns it without any fetch.
_primed: dict[str, FundamentalsBundle] = {}


def prime(mapping: dict[str, FundamentalsBundle]) -> None:
    """Seed the per-process fundamentals cache from a precomputed source (snapshot)."""
    for ticker, fb in mapping.items():
        if fb is not None:
            _primed[str(ticker)] = fb


# --------------------------------------------------------------------------- #
# Derived-signal computation (market-agnostic)
# --------------------------------------------------------------------------- #
def _to_date(s: str) -> Optional[date]:
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _yoy_row(rows: list[dict], cur_d: Optional[date]) -> Optional[dict]:
    """The row whose period is closest to ~1 year before cur_d (within tolerance).

    Used for the trend signals (Piotroski deltas, share issuance) — guards each
    field itself, so unlike the revenue-YoY finder it has no field requirement.
    """
    if cur_d is None:
        return None
    best, best_gap = None, 1e9
    for r in rows[1:]:
        d = _to_date(r.get("period"))
        if d is None:
            continue
        gap = abs((cur_d - d).days - 365)
        if gap < best_gap:
            best, best_gap = r, gap
    return best if best_gap <= _YOY_TOLERANCE_DAYS else None


def _annualized_flow(rows: list[dict], cur: dict, field: str, market: str) -> Optional[float]:
    """Annualize a flow line so GP/assets and accruals/assets match their annual
    thresholds (Novy-Marx / Sloan). US rows are single quarters -> trailing-12-month
    sum; KR DART rows are YTD-cumulative -> scaled to a full year by months covered.
    """
    if market == "KR":
        v = cur.get(field)
        if v is None:
            return None
        d = _to_date(cur.get("period"))
        months = d.month if d else 12  # YTD cumulative: 03-31->3mo, 06-30->6, 09-30->9, 12-31->12
        return v * 12.0 / months if months else None
    vals = [r.get(field) for r in rows[:4] if r.get(field) is not None]  # US: TTM
    if not vals:
        return None
    return sum(vals) * (4.0 / len(vals)) if len(vals) < 4 else sum(vals)


def _signals_from_rows(rows: list[dict], market: str = "US") -> FundamentalsBundle:
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

    # 4 consecutive quarters of losses — US-only by design. US (yfinance) gives
    # discrete quarterly rows so this fires; KR (DART) rows are cumulative/annual,
    # so it stays inert for KR ON PURPOSE. Rationale (score-validation-2026-06-27):
    # KR distress is already covered by *solvency* signals that ARE validated/
    # factual — altman_z (bankruptcy distance, per-date IC t5.1), capital_impairment
    # (equity<=0), and DART audit_qualified / risk_event. Adding KR 4-quarter fetch
    # would cost ~8 extra DART calls/name + a serialization round-trip for a LETHAL
    # gate built on mere *unprofitability* — which over-excludes the very recovery
    # candidates this screen targets (a fallen name with loss quarters that is
    # solvent and turning around). So it is intentionally not implemented for KR.
    ni_hist = [r.get("net_income") for r in rows[:4] if r.get("net_income") is not None]
    four_q_all_loss = len(ni_hist) >= 4 and all(x < 0 for x in ni_hist)

    # --- extra derived signals (all guard their own inputs; None when missing) ---
    ni = cur.get("net_income")
    cfo = cur.get("op_cash_flow")
    gp = cur.get("gross_profit")
    ta = cur.get("total_assets")
    ca = cur.get("current_assets")
    cl = cur.get("current_liabilities")
    re = cur.get("retained_earnings")
    shares = cur.get("shares")
    prev = _yoy_row(rows, cur_d)

    # GP/assets and accruals/assets use ANNUAL thresholds, so annualize the flow
    # numerators (quarterly US / YTD KR) before dividing by point-in-time assets.
    ni_ann = _annualized_flow(rows, cur, "net_income", market)
    cfo_ann = _annualized_flow(rows, cur, "op_cash_flow", market)
    gp_ann = _annualized_flow(rows, cur, "gross_profit", market)
    accrual_ratio = ((ni_ann - cfo_ann) / ta) if (ni_ann is not None and cfo_ann is not None and ta and ta > 0) else None
    gross_profitability = (gp_ann / ta) if (gp_ann is not None and ta and ta > 0) else None

    # Altman Z'' (emerging-market / non-manufacturing). Total liabilities is
    # derived (assets - equity) since `total_debt` is interest-bearing only.
    # Guard the denominators; EBIT/RE may legitimately be negative (that lowers Z).
    altman_z = None
    if (ta and ta > 0 and ca is not None and cl is not None and re is not None
            and op_income is not None and equity is not None):
        tl = ta - equity
        if tl and tl > 0:
            wc = ca - cl
            altman_z = (3.25 + 6.56 * (wc / ta) + 3.26 * (re / ta)
                        + 6.72 * (op_income / ta) + 1.05 * (equity / tl))

    share_change_yoy = None
    if shares is not None and prev is not None:
        ps = prev.get("shares")
        if ps and ps > 0:
            share_change_yoy = (shares - ps) / ps

    f_score = _piotroski(cur, prev)

    return FundamentalsBundle(
        available=True,
        revenue_yoy=revenue_yoy,
        op_margin=op_margin,
        debt_to_equity=debt_to_equity,
        four_quarters_all_loss=four_q_all_loss,
        capital_impairment=capital_impairment,
        periods=len(rows),
        f_score=f_score,
        altman_z=altman_z,
        accrual_ratio=accrual_ratio,
        gross_profitability=gross_profitability,
        share_change_yoy=share_change_yoy,
        audit_qualified=bool(cur.get("audit_qualified")),
        risk_event=(cur.get("risk_event") or None),
    )


def _piotroski(cur: dict, prev: Optional[dict]) -> Optional[int]:
    """Piotroski F-score from current + year-ago rows.

    Counts the 9 binary signals where inputs exist; if at least 5 are evaluable,
    normalizes earned/evaluable to a 0-9 scale so partial data (e.g. financials
    without a current ratio) isn't unfairly penalized. None when too sparse.
    """
    def _ratio(row, num, den):
        if row is None:
            return None
        a, b = row.get(num), row.get(den)
        return (a / b) if (a is not None and b and b > 0) else None

    ni, cfo = cur.get("net_income"), cur.get("op_cash_flow")
    roa_c = _ratio(cur, "net_income", "total_assets")
    roa_p = _ratio(prev, "net_income", "total_assets")
    lev_c = _ratio(cur, "total_debt", "total_assets")
    lev_p = _ratio(prev, "total_debt", "total_assets")
    cur_c = _ratio(cur, "current_assets", "current_liabilities")
    cur_p = _ratio(prev, "current_assets", "current_liabilities")
    mar_c = _ratio(cur, "gross_profit", "revenue")
    mar_p = _ratio(prev, "gross_profit", "revenue")
    to_c = _ratio(cur, "revenue", "total_assets")
    to_p = _ratio(prev, "revenue", "total_assets")
    sh_c = cur.get("shares")
    sh_p = prev.get("shares") if prev else None

    signals: list[bool] = []
    if roa_c is not None:                         signals.append(roa_c > 0)          # 1 profitability
    if cfo is not None:                           signals.append(cfo > 0)            # 2 cash flow
    if roa_c is not None and roa_p is not None:   signals.append(roa_c > roa_p)      # 3 ΔROA
    if cfo is not None and ni is not None:         signals.append(cfo > ni)           # 4 accrual quality
    if lev_c is not None and lev_p is not None:   signals.append(lev_c < lev_p)      # 5 Δleverage
    if cur_c is not None and cur_p is not None:   signals.append(cur_c > cur_p)      # 6 Δliquidity
    if sh_c is not None and sh_p is not None:     signals.append(sh_c <= sh_p)       # 7 no dilution
    if mar_c is not None and mar_p is not None:   signals.append(mar_c > mar_p)      # 8 Δmargin
    if to_c is not None and to_p is not None:     signals.append(to_c > to_p)        # 9 Δturnover

    evaluable = len(signals)
    if evaluable < 5:
        return None
    earned = sum(1 for s in signals if s)
    return round(earned * 9 / evaluable)


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
    try:
        cf = tk.quarterly_cashflow
    except Exception:  # noqa: BLE001 — cash flow is optional (accruals/F-score degrade)
        cf = None
    if inc is None or inc.empty:
        return []
    rev = _series_row(inc, "Total Revenue", "Operating Revenue")
    opi = _series_row(inc, "Operating Income", "Total Operating Income As Reported")
    ni = _series_row(inc, "Net Income", "Net Income Common Stockholders")
    gp = _series_row(inc, "Gross Profit")
    debt = _series_row(bs, "Total Debt")
    eq = _series_row(bs, "Stockholders Equity", "Common Stock Equity")
    ta = _series_row(bs, "Total Assets")
    ca = _series_row(bs, "Current Assets", "Total Current Assets")
    cl = _series_row(bs, "Current Liabilities", "Total Current Liabilities")
    re = _series_row(bs, "Retained Earnings")
    ocf = _series_row(cf, "Operating Cash Flow", "Cash Flow From Continuing Operating Activities")
    # shares outstanding -> price-based market cap (yfinance .info/.fast_info are
    # blocked on datacenter IPs, but the balance sheet endpoint works there)
    shr = _series_row(bs, "Ordinary Shares Number", "Share Issued")

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
            "shares": val(shr, col),
            "op_cash_flow": val(ocf, col),
            "gross_profit": val(gp, col),
            "current_assets": val(ca, col),
            "current_liabilities": val(cl, col),
            "total_assets": val(ta, col),
            "retained_earnings": val(re, col),
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
    # extras for Piotroski / Altman / accruals / gross-profitability
    "total_assets": ("ifrs-full_Assets",),
    "current_assets": ("ifrs-full_CurrentAssets",),
    "current_liabilities": ("ifrs-full_CurrentLiabilities",),
    "retained_earnings": ("ifrs-full_RetainedEarnings",),
    "gross_profit": ("ifrs-full_GrossProfit",),
    "cogs": ("ifrs-full_CostOfSales",),
    "op_cash_flow": ("ifrs-full_CashFlowsFromUsedInOperatingActivities",),
}
_DART_ACCOUNT_NAMES = {
    "revenue": ("수익(매출액)", "매출액", "영업수익"),
    "op_income": ("영업이익", "영업이익(손실)"),
    "net_income": ("당기순이익", "당기순이익(손실)", "분기순이익"),
    "total_debt": ("부채총계",),
    "total_equity": ("자본총계",),
    "total_assets": ("자산총계",),
    "current_assets": ("유동자산",),
    "current_liabilities": ("유동부채",),
    "retained_earnings": ("이익잉여금", "이익잉여금(결손금)", "결손금"),
    "gross_profit": ("매출총이익", "매출총이익(손실)"),
    "cogs": ("매출원가",),
    "op_cash_flow": ("영업활동현금흐름", "영업활동으로인한현금흐름", "영업활동으로 인한 현금흐름"),
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
    revenue = amt("revenue")
    gross_profit = amt("gross_profit")
    if gross_profit is None:  # fall back to revenue - cost of sales
        cogs = amt("cogs")
        if revenue is not None and cogs is not None:
            gross_profit = revenue - cogs
    return {
        "period": f"{year}-{_REPRT_MONTH_DAY.get(reprt, '12-31')}",
        "revenue": revenue,
        "op_income": amt("op_income"),
        "net_income": amt("net_income"),
        "total_debt": amt("total_debt"),
        "total_equity": amt("total_equity"),
        "total_assets": amt("total_assets"),
        "current_assets": amt("current_assets"),
        "current_liabilities": amt("current_liabilities"),
        "retained_earnings": amt("retained_earnings"),
        "gross_profit": gross_profit,
        "op_cash_flow": amt("op_cash_flow"),
        # KR shares outstanding isn't in fnlttSinglAcntAll; left None (share
        # issuance / price-based cap stay US-only until a KR shares source lands).
        "shares": None,
    }


# KR exchange-confirmed distress signals (DART). These are *facts* (a disclaimed
# audit opinion or a bankruptcy filing), not estimates — so the fundamental filter
# treats them as lethal standalone exclusions.
_BAD_OPINIONS = ("한정", "부적정", "의견거절")
_RISK_ENDPOINTS = {
    "dfOcr": "부도", "bsnSp": "영업정지",
    "ctrcvsBgrq": "회생절차", "bnkMngtPcbg": "채권은행관리",
}


def _dart_audit_opinion(key: str, corp: str) -> bool:
    """True if the most recent annual audit opinion is non-적정 (한정/부적정/의견거절).

    Checks the latest year with data; fail-soft (no data / error -> False).
    """
    import requests

    for yr in (date.today().year - 1, date.today().year - 2):
        try:
            r = requests.get(f"{_DART_BASE}/accnutAdtorNmNdAdtOpinion.json",
                             params={"crtfc_key": key, "corp_code": corp,
                                     "bsns_year": str(yr), "reprt_code": "11011"}, timeout=20)
            d = r.json()
        except Exception:  # noqa: BLE001
            continue
        if d.get("status") != "000":
            continue
        ops = [str(it.get("adt_opinion") or "") for it in d.get("list", [])]
        if not ops:
            continue
        return any(any(bad in op for bad in _BAD_OPINIONS) for op in ops)  # most recent year decides
    return False


def _dart_risk_events(key: str, corp: str) -> Optional[str]:
    """Name of a recent (≤1y) 주요사항보고서 distress event, else None. Fail-soft."""
    import requests
    from datetime import timedelta

    end = date.today()
    bgn = end - timedelta(days=365)
    for ep, label in _RISK_ENDPOINTS.items():
        try:
            r = requests.get(f"{_DART_BASE}/{ep}.json",
                             params={"crtfc_key": key, "corp_code": corp,
                                     "bgn_de": bgn.strftime("%Y%m%d"), "end_de": end.strftime("%Y%m%d")},
                             timeout=20)
            d = r.json()
        except Exception:  # noqa: BLE001
            continue
        if d.get("status") != "000" or not d.get("list"):
            continue
        if ep == "bsnSp":
            # 영업정지(bsnSp)는 전사 부도가 아니라 부분/행정 사업라인 정지도 포함한다.
            # 영향 매출비중(sl_vs)이 높을 때만 치명으로 본다(예: 호텔신라 10.9% 제외,
            # 대우건설 72.8% 유지).
            ratios = [_parse_won(it.get("sl_vs")) for it in d["list"]]
            ratios = [v for v in ratios if v is not None]
            if not ratios or max(ratios) < 50.0:
                continue  # partial line suspension -> not a lethal exclusion
        return label
    return None


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

    # exchange-confirmed distress (annual audit opinion + recent major events).
    # Best-effort: a failure here must not lose the financial rows above.
    try:
        rows[0]["audit_qualified"] = _dart_audit_opinion(key, corp)
        rows[0]["risk_event"] = _dart_risk_events(key, corp)
    except Exception as e:  # noqa: BLE001
        log.warning("DART risk-signal fetch failed %s: %s", ticker, e)
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
    if row[0] < _SCHEMA_CUTOFF:
        return None  # pre-extended-schema row -> refetch once to populate new columns
    fetched = _to_date(row[0])
    if fetched and (date.today() - fetched).days > REFRESH_DAYS:
        return None  # stale
    cur = conn.execute(
        "SELECT period, revenue, op_income, net_income, total_debt, total_equity, shares, "
        "op_cash_flow, gross_profit, current_assets, current_liabilities, "
        "total_assets, retained_earnings, audit_qualified, risk_event "
        "FROM fundamentals WHERE ticker=? ORDER BY period DESC", (ticker,)
    )
    cols = ("period", "revenue", "op_income", "net_income", "total_debt", "total_equity",
            "shares", "op_cash_flow", "gross_profit", "current_assets",
            "current_liabilities", "total_assets", "retained_earnings",
            "audit_qualified", "risk_event")
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _save(conn, ticker: str, rows: list[dict]) -> None:
    now = db_mod.now_iso()
    conn.executemany(
        "INSERT OR REPLACE INTO fundamentals"
        "(ticker, period, revenue, op_income, net_income, total_debt, total_equity, shares,"
        " op_cash_flow, gross_profit, current_assets, current_liabilities,"
        " total_assets, retained_earnings, audit_qualified, risk_event, fetched_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(ticker, r["period"], r.get("revenue"), r.get("op_income"), r.get("net_income"),
          r.get("total_debt"), r.get("total_equity"), r.get("shares"),
          r.get("op_cash_flow"), r.get("gross_profit"), r.get("current_assets"),
          r.get("current_liabilities"), r.get("total_assets"), r.get("retained_earnings"),
          (1 if r.get("audit_qualified") else 0) if r.get("audit_qualified") is not None else None,
          r.get("risk_event"), now) for r in rows],
    )
    conn.commit()


def latest_raw(ticker: str) -> Optional[dict]:
    """Latest cached period's raw figures (for valuation). None if not cached."""
    conn = db_mod.get_connection()
    try:
        r = conn.execute(
            "SELECT period, net_income, total_equity, shares FROM fundamentals "
            "WHERE ticker=? ORDER BY period DESC LIMIT 1", (ticker,)
        ).fetchone()
        return {"period": r[0], "net_income": r[1], "total_equity": r[2], "shares": r[3]} if r else None
    finally:
        conn.close()


def get_fundamentals(market: str, ticker: str, use_cache: bool = True,
                     max_retries: int = 3) -> FundamentalsBundle:
    """Fetch (or load cached) fundamentals and return the derived bundle.

    Always returns a bundle; `available=False` means no usable data (treat as
    neutral, never exclude).
    """
    if use_cache:
        primed = _primed.get(ticker)
        if primed is not None:
            return primed

    conn = db_mod.get_connection()
    try:
        if use_cache:
            cached = _load_cached(conn, ticker)
            if cached is not None:
                return _signals_from_rows(cached, market)

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
        return _signals_from_rows(rows, market)
    finally:
        conn.close()
