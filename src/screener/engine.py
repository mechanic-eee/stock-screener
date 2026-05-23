"""Screening engine.

Two stages, deliberately split:

1. build_candidates(): the heavy, cacheable pass. Walks the universe, fetches
   (cached) price history, applies the always-on base screen (drawdown). The
   survivors — usually a small set — are returned as TickerData.

2. apply_filters(): the fast, interactive pass over those candidates. Applies
   the user-selected optional filters with their current params. Technical
   filters run first; the news filter (network I/O) runs last and only on rows
   that survived everything else.
"""
from __future__ import annotations

from typing import Callable, Optional

from . import filters as filters_pkg
from . import news as news_pkg
from .data import prices as prices_mod
from .data import universe as universe_mod
from .filters.base import base_filters, get
from .models import TickerData

ProgressCb = Optional[Callable[[int, int, str], None]]


def build_candidates(
    markets: list[str],
    base_params: dict | None = None,
    years: int = 5,
    max_age_days: float = 1.0,
    limit: Optional[int] = None,
    progress_cb: ProgressCb = None,
) -> list[TickerData]:
    rows = universe_mod.build_universe(markets)
    if limit:
        rows = rows[:limit]
    base = base_filters()[0]  # the drawdown screen
    total = len(rows)
    candidates: list[TickerData] = []
    for i, row in enumerate(rows):
        if progress_cb:
            progress_cb(i + 1, total, row["ticker"])
        df = prices_mod.get_prices(row["market"], row["ticker"], years=years, max_age_days=max_age_days)
        if df is None or df.empty:
            continue
        data = TickerData(ticker=row["ticker"], market=row["market"], name=row["name"], prices=df)
        if base.apply(data, base_params).passed:
            candidates.append(data)
    return candidates


def apply_filters(
    candidates: list[TickerData],
    base_params: dict | None,
    selected: dict[str, dict],
    fetch_news: bool = True,
) -> list[dict]:
    """selected maps optional-filter-key -> its param dict.

    Returns one result row per surviving ticker with each active filter's
    detail string, ready for a table.
    """
    base = base_filters()[0]
    # split selected into cheap (technical) and expensive (news) filters
    news_keys = [k for k in selected if get(k).needs_news]
    tech_keys = [k for k in selected if not get(k).needs_news]

    provider = news_pkg.get_provider() if (news_keys and fetch_news) else None

    results: list[dict] = []
    for data in candidates:
        base_out = base.apply(data, base_params)
        row = {
            "ticker": data.ticker,
            "name": data.name,
            "market": data.market,
            "close": float(data.prices["close"].iloc[-1]),
            "하락률": base_out.value,
            base.label: base_out.detail,
        }
        passed = True
        for key in tech_keys:
            flt = get(key)
            out = flt.apply(data, selected[key])
            row[flt.label] = out.detail
            if not out.passed:
                passed = False
                break
        if not passed:
            continue

        # expensive news pass, only for survivors
        for key in news_keys:
            flt = get(key)
            params = selected[key]
            if provider is not None and provider.available():
                query = data.name or data.ticker
                data.news = news_pkg.build_bundle(
                    provider, query,
                    lookback_days=int(params.get("lookback_days", 30)),
                    recent_days=int(params.get("recent_days", 7)),
                )
            out = flt.apply(data, params)
            row[flt.label] = out.detail
            if not out.passed:
                passed = False
                break
        if passed:
            results.append(row)

    results.sort(key=lambda r: (r.get("하락률") or 0), reverse=True)
    return results


def ensure_filters_loaded() -> None:
    filters_pkg.base.load_all()
