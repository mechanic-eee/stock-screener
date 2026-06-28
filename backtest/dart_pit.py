#!/usr/bin/env python3
"""Point-in-time KR fundamentals from DART historical annual reports (needs DART_API_KEY).

The KR counterpart of edgar_pit.py. For a cohort date T, fetches the most recent
ANNUAL report (사업보고서, reprt 11011) that was PUBLIC by T — conservatively, FY Y
is treated public once T >= Apr 1 of Y+1 (DART's 90-day filing deadline + buffer),
so there is never look-ahead. FY Y + FY Y-1 feed `_signals_from_rows(rows, 'KR')`,
reusing the production scoring (no re-implementation). Reuses fundamentals'
`_dart_report` / `_row_from_report` / `_load_corp_map`.

Caveats (documented, not bugs):
- Live distress signals (audit opinion / 주요사항보고서) in fundamentals._fetch_kr
  are `date.today()`-anchored → look-ahead, so they're SKIPPED here. The IC signals
  (Altman/Piotroski/accruals/GP) come from the financial rows, which ARE PIT.
- DART's fnlttSinglAcntAll has no shares-outstanding line → share_issuance is
  unavailable for KR and Piotroski drops its dilution signal (it normalizes over
  the evaluable signals, so the F-score still computes).
- corpCode.xml maps mostly *currently/recently listed* stock codes; some delisted
  names in the survivorship-corrected price set may have no corp_code → their
  fundamentals are unavailable (coverage shows this; prices stay PIT-correct).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from screener import fundamentals as fund  # noqa: E402

CACHE = ROOT / "exports" / "dart_cache"


def fiscal_year_asof(T: str) -> int:
    """Largest fiscal year Y whose annual report is public by T.

    DART 사업보고서 is due within 90 days of the Dec-31 fiscal-year end (~Mar 31);
    we require T >= Apr 1 of Y+1 as a safe buffer (conservative, never look-ahead).
    """
    y, m, d = int(T[:4]), int(T[5:7]), int(T[8:10])
    return y - 1 if (m, d) >= (4, 1) else y - 2


def cached_report(key: str, corp: str, year: int, throttle: float = 0.0) -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    fp = CACHE / f"{corp}_{year}.json"
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            pass
    rep = fund._dart_report(key, corp, year, "11011")  # annual (사업보고서)
    if throttle:
        time.sleep(throttle)
    try:
        fp.write_text(json.dumps(rep), encoding="utf-8")
    except Exception:
        pass
    return rep


def pit_rows(key: str, corp: str, T: str, throttle: float = 0.03) -> list[dict]:
    """Annual rows public by T (current FY + prior FY for YoY), _signals_from_rows shape."""
    Y = fiscal_year_asof(T)
    rows = []
    for yr in (Y, Y - 1):
        rep = cached_report(key, corp, yr, throttle)
        if rep:
            rows.append(fund._row_from_report(rep, yr, "11011"))
    return rows


def _selftest():
    key = fund._dart_key()
    if not key:
        print("no DART_API_KEY"); return
    cmap = fund._load_corp_map(key)
    for tk in ("005930", "000660"):  # Samsung, SK hynix
        corp = cmap.get(tk)
        for T in ("2020-06-30", "2022-06-30", "2024-06-30"):
            rows = pit_rows(key, corp, T)
            fb = fund._signals_from_rows(rows, market="KR")
            z = f"{fb.altman_z:.2f}" if fb.altman_z is not None else "None"
            ac = f"{fb.accrual_ratio:+.3f}" if fb.accrual_ratio is not None else "None"
            gp = f"{fb.gross_profitability:.3f}" if fb.gross_profitability is not None else "None"
            cur = rows[0]["period"] if rows else "—"
            print(f"{tk} @ {T}: annual<=T {cur} | F={fb.f_score} Z={z} accr={ac} GP={gp} "
                  f"revYoY={fb.revenue_yoy}")


if __name__ == "__main__":
    _selftest()
