"""Core data structures shared across the screener."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable, Optional

import pandas as pd


@dataclass
class TickerData:
    """Everything a filter might need about one ticker.

    `prices` is a daily OHLCV DataFrame indexed by date (ascending), with
    columns: open, high, low, close, volume. `news` is filled lazily and only
    when a news-based filter is active (news fetch is expensive).
    """

    ticker: str
    market: str  # "KR" | "US"
    name: str
    prices: pd.DataFrame
    security_type: str = "common"
    news: Optional["NewsBundle"] = None
    # filled lazily by the engine, only for survivors of a fundamentals filter
    # (external API + cache, like news). None = not fetched yet.
    fundamentals: Optional["FundamentalsBundle"] = None
    catalyst: Optional["CatalystInfo"] = None
    valuation: Optional["ValuationBundle"] = None


@dataclass
class FilterOutcome:
    """Result of applying one filter to one ticker.

    `passed` drives whether the ticker survives (gate role). `score` is the
    0-100 contribution to the composite score (scorer role) — the predecessor
    project's "gate AND scorer" idea. `detail` is a short table string;
    `value` is the raw numeric for sorting/inspection.
    """

    passed: bool
    detail: str = ""
    value: Optional[float] = None
    score: float = 0.0
    # False when the filter could not get the data it needs and fell back to a
    # neutral score (e.g. benchmark/valuation/fundamentals fetch failed, no news
    # key). The engine aggregates these so the UI can warn that a toggled filter
    # is silently inert — neutral-for-all changes neither the count nor the rank.
    available: bool = True


@dataclass
class Param:
    """A single tunable parameter for a filter.

    The Streamlit UI renders a control from this spec, so a new indicator gets
    adjustable controls for free just by declaring its params.
    """

    key: str
    label: str
    kind: str  # "int" | "float" | "bool" | "select"
    default: Any
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    choices: Optional[list] = None
    help: str = ""


@dataclass
class Filter:
    key: str
    label: str
    description: str
    params: list[Param]
    fn: Callable[["TickerData", dict], FilterOutcome]
    needs_news: bool = False
    needs_fundamentals: bool = False
    needs_catalyst: bool = False
    needs_valuation: bool = False
    # Bonus filters never gate and aren't part of the weighted average; their
    # FilterOutcome.score is added to the composite *after* normalization
    # (PRD §5.5.2 catalyst bonus — total may exceed 100).
    is_bonus: bool = False
    # If True this is the always-on base screen and cannot be toggled off.
    is_base: bool = False
    # Default weight in the composite score (relative; normalized at runtime).
    weight: float = 0.10

    def defaults(self) -> dict:
        return {p.key: p.default for p in self.params}

    def apply(self, data: "TickerData", params: dict | None = None) -> FilterOutcome:
        merged = self.defaults()
        if params:
            merged.update(params)
        return self.fn(data, merged)


@dataclass
class NewsBundle:
    """Aggregated recent news for a ticker."""

    article_count: int
    recent_count: int  # within the lookback window
    avg_sentiment: float  # -1..1
    headlines: list[str] = field(default_factory=list)


@dataclass
class FundamentalsBundle:
    """Derived quarterly-fundamentals signals for one ticker (PRD §5.4.3).

    Ratios are fractions (e.g. revenue_yoy=-0.30 means -30%, debt_to_equity=3.0
    means 300%). `available` is False when no usable financials were found (no
    DART key for KR, missing data, fetch failure) — callers then treat the
    ticker as neutral (score 50, no exclusion) rather than excluding it.
    """

    available: bool
    revenue_yoy: Optional[float] = None
    op_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    four_quarters_all_loss: bool = False
    capital_impairment: bool = False  # equity <= 0
    periods: int = 0


@dataclass
class CatalystInfo:
    """Upcoming/recent earnings dates for one ticker (PRD §5.4.5).

    `available` is False when no earnings calendar was found (treated as no
    catalyst — no warning, no bonus). Dates are calendar dates.
    """

    available: bool
    next_earnings: Optional[date] = None
    days_until: Optional[int] = None       # calendar days from today to next_earnings
    last_earnings: Optional[date] = None


@dataclass
class ValuationBundle:
    """Valuation/quality multiples for one ticker (cheap vs merely fallen).

    Ratios are plain multiples (per, pbr); roe and dividend_yield are fractions
    (0.15 = 15%). `available` is False when nothing usable was found -> neutral
    50, never excluded (fail-soft). US via yfinance .info; KR computed from DART
    equity/net-income + market cap.
    """

    available: bool
    per: Optional[float] = None
    pbr: Optional[float] = None
    roe: Optional[float] = None
    dividend_yield: Optional[float] = None
