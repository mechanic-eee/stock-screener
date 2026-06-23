"""KR market-action exclusions: 관리종목 / 투자주의환기종목.

A deep-drawdown screen's worst failure mode is buying a name that is already on
its way off the exchange. The KRX flags these administratively, and that flag is
an *exchange-confirmed* signal independent of the fundamental estimates the
screener computes — so it belongs at the universe stage, not as a soft score.

Two free sources, no key:
  • ``fdr.StockListing('KRX-ADMINISTRATIVE')`` — the authoritative 관리종목 list
    (Symbol, Name, DesignationDate, Reason).
  • the ``Dept`` column already present on ``fdr.StockListing('KRX')`` — carries
    '관리종목' and '투자주의환기종목' markers inline (no extra fetch).

The administrative list is fetched once per UTC day (small JSON cache) so repeated
local runs don't re-hit the network. Everything is fail-soft: if a fetch fails we
log and return what we have, never blocking the scan.
"""
from __future__ import annotations

import json
import logging
from datetime import date

import pandas as pd

from . import db

log = logging.getLogger(__name__)

_CACHE = db.ROOT / "data" / "kr_admin_cache.json"


def _code6(symbol) -> str:
    """KRX-ADMINISTRATIVE 'Symbol' comes as 1470 / '1470'; KRX 'Code' is 6-digit."""
    return str(symbol).strip().zfill(6)


def kr_admin_issues(use_cache: bool = True) -> dict[str, str]:
    """{code6: reason} for current 관리종목, from the dedicated KRX list.

    Daily-cached (valid only for the same UTC date). Returns {} on any failure
    so the caller degrades gracefully rather than dropping the whole KR scan.
    """
    today = date.today().isoformat()
    if use_cache and _CACHE.exists():
        try:
            blob = json.loads(_CACHE.read_text(encoding="utf-8"))
            if blob.get("date") == today and isinstance(blob.get("issues"), dict):
                return blob["issues"]
        except Exception:  # noqa: BLE001 - corrupt cache -> refetch
            pass

    try:
        import FinanceDataReader as fdr
        df = fdr.StockListing("KRX-ADMINISTRATIVE")
        issues = {
            _code6(s): (str(r).strip() or "관리종목")
            for s, r in zip(df["Symbol"], df.get("Reason", ["관리종목"] * len(df)))
        }
    except Exception as e:  # noqa: BLE001 - network/source failure is non-fatal
        log.warning("KR administrative list fetch failed (%s); skipping admin gate", e)
        return {}

    try:
        _CACHE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE.write_text(json.dumps({"date": today, "issues": issues},
                                     ensure_ascii=False), encoding="utf-8")
    except Exception:  # noqa: BLE001 - cache write best-effort
        pass
    return issues


def kr_flags_from_listing(listing_df: pd.DataFrame) -> dict[str, str]:
    """{code6: reason} from the 'Dept' column of an already-fetched KRX listing.

    Catches '관리종목' and '투자주의환기종목' with zero extra network cost.
    """
    if listing_df is None or "Dept" not in listing_df.columns or "Code" not in listing_df.columns:
        return {}
    dept = listing_df["Dept"].fillna("").astype(str)
    out: dict[str, str] = {}
    for code, d in zip(listing_df["Code"].astype(str), dept):
        if "관리종목" in d:
            out[_code6(code)] = "관리종목"
        elif "투자주의환기" in d:
            out[_code6(code)] = "투자주의환기종목"
    return out


def kr_excluded(listing_df: pd.DataFrame | None = None, use_cache: bool = True) -> dict[str, str]:
    """Merge both sources into {code6: reason}. Administrative list wins on conflict."""
    merged = dict(kr_flags_from_listing(listing_df)) if listing_df is not None else {}
    merged.update(kr_admin_issues(use_cache=use_cache))  # admin reasons override Dept marker
    return merged
