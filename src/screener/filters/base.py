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


# UI display priority — most decision-relevant first so the sidebar surfaces the
# filters that actually separate recoverable names from value traps before the
# confirmatory/weak ones. Order: value-trap/distress/quality → momentum/flow →
# risk meta → confirmatory & weak signals. Keys not listed sort last (then by
# registration order). Engine logic is unaffected — it groups filters by role.
_DISPLAY_ORDER = [
    "drawdown",                                                      # base (always first)
    "fundamental", "altman_z", "piotroski",                         # value-trap / distress
    "relative_strength", "vcp_contraction",                        # relative strength / base-building
    "valuation", "gross_profit", "accruals", "share_issuance",     # cheap-and-good / earnings quality
    "weekly_macd", "macd_cross", "volume_surge", "obv_accumulation",  # momentum / flow
    "atr_risk",                                                     # risk / sizing meta
    "rsi", "bollinger", "moving_average", "news", "catalyst",       # confirmatory / weak
]


def _order_key(f: Filter):
    try:
        idx = _DISPLAY_ORDER.index(f.key)
    except ValueError:
        idx = len(_DISPLAY_ORDER)
    return (not f.is_base, idx)


def all_filters() -> list[Filter]:
    """Base filter(s) first, then the rest in UI display-priority order."""
    return sorted(_REGISTRY.values(), key=_order_key)


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
                   atr_risk, piotroski, altman_z, accruals, gross_profit, share_issuance)
