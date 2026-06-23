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

from . import catalysts as catalysts_mod
from . import filters as filters_pkg
from . import fundamentals as fundamentals_mod
from . import news as news_pkg
from . import valuation as valuation_mod
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
    include_types: list[str] | tuple[str, ...] = ("common",),
) -> list[TickerData]:
    rows = universe_mod.build_universe(markets, include_types=include_types)
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
        data = TickerData(ticker=row["ticker"], market=row["market"], name=row["name"],
                          prices=df, security_type=row.get("security_type", "common"))
        if base.apply(data, base_params).passed:
            candidates.append(data)
    return candidates


def apply_filters(
    candidates: list[TickerData],
    base_params: dict | None,
    selected: dict[str, dict],
    fetch_news: bool = True,
    weights: dict[str, float] | None = None,
    diag: dict[str, list[int]] | None = None,
) -> list[dict]:
    """selected maps optional-filter-key -> its param dict.

    Returns one result row per surviving ticker, including each active filter's
    detail string and a weighted composite `점수` (0-100). `weights` overrides
    per-filter weights (key -> weight); base + active filters all contribute,
    normalized by total weight so the score stays 0-100 for any selection.

    If `diag` is provided it is filled with per-filter availability counts —
    diag[key] = [unavailable, evaluated] — so a caller can tell when a toggled
    filter got no usable data and fell back to neutral-for-all (silently inert).
    """
    def note(key: str, out) -> None:
        if diag is None:
            return
        d = diag.setdefault(key, [0, 0])
        d[1] += 1
        if not out.available:
            d[0] += 1
    base = base_filters()[0]
    news_keys = [k for k in selected if get(k).needs_news]
    fund_keys = [k for k in selected if get(k).needs_fundamentals]
    val_keys = [k for k in selected if get(k).needs_valuation]
    bonus_keys = [k for k in selected if get(k).is_bonus]
    tech_keys = [k for k in selected if not get(k).needs_news
                 and not get(k).needs_fundamentals and not get(k).needs_valuation
                 and not get(k).is_bonus]

    news_enabled = bool(news_keys) and fetch_news

    def w(key: str) -> float:
        if weights and key in weights:
            return weights[key]
        return get(key).weight

    results: list[dict] = []
    for data in candidates:
        base_out = base.apply(data, base_params)
        # The base drawdown is a live gate here too, not just a scorer: a snapshot
        # is pre-screened at the loosest threshold (-50%), so tightening the UI
        # slider (e.g. to -85%) must actually drop the shallower-drawdown names.
        if not base_out.passed:
            continue
        row = {
            "ticker": data.ticker,
            "name": data.name,
            "market": data.market,
            "close": round(float(data.prices["close"].iloc[-1]), 2),
            "하락률": base_out.value,
            base.label: base_out.detail,
        }
        wsum = w(base.key)
        sscore = w(base.key) * base_out.score

        passed = True
        for key in tech_keys:
            flt = get(key)
            out = flt.apply(data, selected[key])
            note(key, out)
            row[flt.label] = out.detail
            if not out.passed:
                passed = False
                break
            wsum += w(key)
            sscore += w(key) * out.score
        if not passed:
            continue

        # fundamentals pass (external API + cache), only for survivors.
        # getattr guards stale TickerData in session_state from before this field
        # existed (the hosted app keeps candidates across redeploys).
        for key in fund_keys:
            flt = get(key)
            if getattr(data, "fundamentals", None) is None:
                data.fundamentals = fundamentals_mod.get_fundamentals(data.market, data.ticker)
            out = flt.apply(data, selected[key])
            note(key, out)
            row[flt.label] = out.detail
            if not out.passed:
                passed = False
                break
            wsum += w(key)
            sscore += w(key) * out.score
        if not passed:
            continue

        # valuation pass (external API + cache), only for survivors
        for key in val_keys:
            flt = get(key)
            if getattr(data, "valuation", None) is None:
                last_close = float(data.prices["close"].iloc[-1]) if not data.prices.empty else None
                data.valuation = valuation_mod.get_valuation(data.market, data.ticker, last_price=last_close)
            out = flt.apply(data, selected[key])
            note(key, out)
            row[flt.label] = out.detail
            if not out.passed:
                passed = False
                break
            wsum += w(key)
            sscore += w(key) * out.score
        if not passed:
            continue

        # expensive news pass, only for survivors. Provider is chosen per ticker
        # by market (KR -> Naver Korean news, US -> NewsAPI); fetches are cached
        # for the day so repeated runs don't burn the rate limit.
        provider = news_pkg.get_provider(data.market) if news_enabled else None
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
            note(key, out)
            row[flt.label] = out.detail
            if not out.passed:
                passed = False
                break
            wsum += w(key)
            sscore += w(key) * out.score
        if not passed:
            continue

        # bonus pass: never gates, added after normalization (PRD §5.5.2 —
        # the total may exceed 100). Not part of the weighted average.
        bonus_total = 0.0
        for key in bonus_keys:
            flt = get(key)
            if flt.needs_catalyst and getattr(data, "catalyst", None) is None:
                data.catalyst = catalysts_mod.get_catalyst(data.market, data.ticker)
            out = flt.apply(data, selected[key])
            row[flt.label] = out.detail
            bonus_total += out.score

        base_score = (sscore / wsum) if wsum else 0.0
        row["점수"] = round(base_score + bonus_total, 1)
        results.append(row)

    results.sort(key=lambda r: r.get("점수", 0), reverse=True)
    return results


def ensure_filters_loaded() -> None:
    filters_pkg.base.load_all()
