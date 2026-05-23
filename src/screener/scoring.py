"""0-100 scoring curves, ported from the predecessor project's PRD §5.

Each gate factor is both a pass/fail filter and a continuous score. These
helpers encode the PRD's non-linear mappings (drawdown bell curve, MACD age
decay, volume zones) plus simple monotonic curves for the extra indicators.
"""
from __future__ import annotations


def _piecewise(x: float, points: list[tuple[float, float]]) -> float:
    """Linear interpolation across (x, y) breakpoints (points sorted by x)."""
    if x <= points[0][0]:
        return points[0][1]
    if x >= points[-1][0]:
        return points[-1][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y1
            t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return points[-1][1]


def drawdown_score(drop_pct: float) -> float:
    """Bell curve peaking at 65-80% drawdown (PRD §5 price gate scorer).

    `drop_pct` is a positive number (e.g. 82 means -82% from the high).
    """
    if drop_pct < 50:
        return 0.0
    if drop_pct > 95:
        return 0.0  # delisting-risk zone
    return _piecewise(drop_pct, [
        (50, 50), (65, 100), (80, 70), (90, 20), (95, 0),
    ])


def macd_score(age_days: int, is_zero_cross: bool) -> float:
    """Fresher cross scores higher; zero-line cross gets a +10 bonus."""
    base = max(0.0, 100.0 - 20.0 * (age_days - 1))
    bonus = 10.0 if is_zero_cross else 0.0
    return min(100.0, base + bonus)


def volume_score(ratio: float) -> float:
    """Volume confirmation zones; >=10x flagged as possible manipulation."""
    if ratio < 1.5:
        return 0.0
    if ratio >= 10.0:
        return 50.0
    return _piecewise(ratio, [
        (1.5, 50), (3, 100), (5, 100), (10, 80),
    ])


def rsi_score(rsi: float, threshold: float, oversold: bool) -> float:
    """Oversold: deeper below threshold scores higher (and vice-versa)."""
    if oversold:
        # rsi 0 -> 100, threshold -> 50, 100 -> 0
        return _piecewise(rsi, [(0, 100), (threshold, 50), (100, 0)])
    return _piecewise(rsi, [(0, 0), (threshold, 50), (100, 100)])


def bollinger_score(pctb: float, lower_mode: bool) -> float:
    """Lower-band mode: closer to/below lower band scores higher."""
    if lower_mode:
        return _piecewise(pctb, [(-0.5, 100), (0, 100), (0.5, 50), (1.0, 0)])
    return _piecewise(pctb, [(0, 0), (0.5, 50), (1.0, 100), (1.5, 100)])


def linear(x: float, x0: float, x1: float, y0: float = 0.0, y1: float = 100.0) -> float:
    return _piecewise(x, [(x0, y0), (x1, y1)])
