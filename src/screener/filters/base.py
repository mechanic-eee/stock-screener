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


# UI display groups — ordered by pick-priority, grounded in the 2026-06 score
# validation (docs/score-validation-2026-06-27.md): the top group is the
# validated edge (per-date IC t4~7 across both markets), the bottom group is
# signals that tested inert/anti-predictive and carry weight 0. The app renders
# one sidebar section per group with a divider in between; keys not listed
# anywhere fall into a trailing "기타" group so new filters stay visible until
# classified. Engine logic is unaffected — it groups filters by role.
_DISPLAY_GROUPS: list[tuple[str, list[str]]] = [
    ("🟢 핵심 — 항상 켜기 (검증된 엣지)",
     ["fundamental", "piotroski", "atr_risk", "altman_z", "gross_profit"]),
    ("🔵 보강 — 함께 켜면 좋음 (가치함정 게이트·희석·바닥구조)",
     ["valuation", "share_issuance", "vcp_contraction"]),
    ("🟡 확증·타이밍 — 약신호 (낮은 가중, 선택)",
     ["relative_strength", "weekly_macd", "macd_cross",
      "rsi", "bollinger", "moving_average", "news", "catalyst"]),
    ("⚪ 예측력 없음 — 꺼두기 권장 (검증 음성, 가중 0)",
     ["obv_accumulation", "volume_surge", "accruals"]),
]

_DISPLAY_ORDER = ["drawdown"] + [k for _, keys in _DISPLAY_GROUPS for k in keys]


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


TIER_SHORT = ["핵심", "보강", "확증", "제외"]


def label_tiers() -> dict[str, tuple[int, str]]:
    """Filter label -> (tier index, short tier name) per _DISPLAY_GROUPS.

    Used by the UI to color/aggregate score contributions by signal tier
    (핵심 = the validated edge). Labels not in any group (e.g. the base
    drawdown) are simply absent — callers treat them as '기본'.
    """
    out: dict[str, tuple[int, str]] = {}
    for gi, (_title, keys) in enumerate(_DISPLAY_GROUPS):
        short = TIER_SHORT[gi] if gi < len(TIER_SHORT) else "기타"
        for k in keys:
            if k in _REGISTRY:
                out[_REGISTRY[k].label] = (gi, short)
    return out


def display_groups() -> list[tuple[str, list[Filter]]]:
    """Optional filters bucketed for the sidebar, in pick-priority order.

    Unregistered keys are skipped; registered filters missing from
    ``_DISPLAY_GROUPS`` come back in a trailing "기타" group.
    """
    grouped: list[tuple[str, list[Filter]]] = []
    listed: set[str] = set()
    for title, keys in _DISPLAY_GROUPS:
        listed.update(keys)
        flts = [_REGISTRY[k] for k in keys if k in _REGISTRY]
        if flts:
            grouped.append((title, flts))
    rest = [f for f in optional_filters() if f.key not in listed]
    if rest:
        grouped.append(("기타 (미분류)", rest))
    return grouped


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
