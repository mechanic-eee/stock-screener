"""Filter registry.

Each filter is a small module that calls ``@register`` with a Filter spec.
The engine and the Streamlit UI both read from the registry, so adding a new
indicator is: drop a file in this package, call ``@register``, done. No other
file needs to change.
"""
from __future__ import annotations

from ..models import Filter

_REGISTRY: dict[str, Filter] = {}


def register(flt: Filter) -> Filter:
    if flt.key in _REGISTRY:
        raise ValueError(f"duplicate filter key: {flt.key}")
    _REGISTRY[flt.key] = flt
    return flt


def get(key: str) -> Filter:
    return _REGISTRY[key]


def all_filters() -> list[Filter]:
    """Base filter(s) first, then the rest in registration order."""
    items = list(_REGISTRY.values())
    return sorted(items, key=lambda f: (not f.is_base,))


def optional_filters() -> list[Filter]:
    return [f for f in all_filters() if not f.is_base]


def base_filters() -> list[Filter]:
    return [f for f in all_filters() if f.is_base]


def load_all() -> None:
    """Import every filter module so its ``@register`` runs.

    Importing the package's ``__init__`` triggers this; kept explicit so the
    engine can guarantee the registry is populated.
    """
    from . import (drawdown, macd, weekly_macd, rsi, volume, moving_average,  # noqa: F401
                   bollinger, obv, vcp, rs, fundamental, valuation, catalyst, news,
                   atr_risk)
