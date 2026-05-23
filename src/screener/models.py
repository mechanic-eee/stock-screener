"""Core data structures shared across the screener."""
from __future__ import annotations

from dataclasses import dataclass, field
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
    news: Optional["NewsBundle"] = None


@dataclass
class FilterOutcome:
    """Result of applying one filter to one ticker.

    `passed` drives whether the ticker survives. `detail` is a short string
    shown in the results table (e.g. "MACD↑", "-82%", "RSI 28").
    `value` is the raw numeric for sorting/inspection when available.
    """

    passed: bool
    detail: str = ""
    value: Optional[float] = None


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
    # If True this is the always-on base screen and cannot be toggled off.
    is_base: bool = False

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
