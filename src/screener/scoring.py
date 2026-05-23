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


def obv_accumulation_score(net_ratio: float) -> float:
    """OBV net accumulation over the window as a fraction of traded volume.

    -30% (distribution) -> 0, flat -> 50, +30% (strong accumulation) -> 100.
    """
    return _piecewise(net_ratio, [(-0.30, 0), (0.0, 50), (0.30, 100)])


def contraction_score(width_pctile: float) -> float:
    """Bollinger band-width percentile (0=tightest..1=widest); tighter scores
    higher — a contracted base after a big fall."""
    return _piecewise(width_pctile, [(0.0, 100), (0.25, 75), (0.5, 50), (1.0, 0)])


def relative_strength_score(excess_return: float) -> float:
    """Return vs benchmark over the lookback (fraction): -20% -> 0, 0 -> 50,
    +20% (and up) -> 100. Outperforming a weak tape is the strong signal."""
    return _piecewise(excess_return, [(-0.20, 0), (0.0, 50), (0.20, 100)])


# --- Valuation (cheap vs merely fallen). None inputs are skipped from the avg. ---

def _val_per(per):
    if per is None or per <= 0:
        return None  # loss or NA -> not informative for "cheap"
    return _piecewise(per, [(8, 100), (15, 50), (30, 0)])


def _val_pbr(pbr):
    if pbr is None or pbr <= 0:
        return None
    return _piecewise(pbr, [(0.7, 100), (1.5, 50), (3.0, 0)])


def _val_roe(roe):
    if roe is None:
        return None
    return _piecewise(roe, [(0.0, 0), (0.10, 50), (0.20, 100)])


def _val_div(dy):
    if dy is None:
        return None
    return _piecewise(dy, [(0.0, 40), (0.02, 60), (0.05, 100)])


def valuation_score(per=None, pbr=None, roe=None, dividend_yield=None) -> float:
    """Average of available sub-scores; 50 (neutral) when none available.

    Lower PER/PBR -> higher (cheaper); higher ROE -> higher (quality); a
    dividend adds mild support for a beaten-down name.
    """
    subs = [s for s in (_val_per(per), _val_pbr(pbr), _val_roe(roe), _val_div(dividend_yield))
            if s is not None]
    return sum(subs) / len(subs) if subs else 50.0


# Weekly-MACD (multi-timeframe) state -> score, per PRD §5.4.4. Higher-timeframe
# confirmation: a fresh weekly signal-cross is best, a positive-and-rising line
# next, and a negative-and-falling line worst.
WEEKLY_MACD_SCORES: dict[str, float] = {
    "signal_cross": 100.0,   # signal-line cross within last 4 weeks
    "pos_rising": 80.0,      # positive and rising over last 4 weeks
    "pos_flat": 60.0,        # positive, change within +/-5%
    "pos_falling": 40.0,     # positive but falling
    "neg_rising": 50.0,      # negative but rising (turnaround)
    "neg_flat": 30.0,        # negative, flat
    "neg_falling": 0.0,      # negative and falling
}


def weekly_macd_score(state: str) -> float:
    return WEEKLY_MACD_SCORES.get(state, 0.0)


# --- Fundamentals (PRD §5.4.3). Inputs are fractions; missing inputs -> None. ---

def fundamental_revenue_score(yoy: float) -> float:
    """Revenue YoY: -30% -> 0, 0% -> 50, +20% (and up) -> 100."""
    return _piecewise(yoy, [(-0.30, 0), (0.0, 50), (0.20, 100)])


def fundamental_margin_score(op_margin: float) -> float:
    """Operating margin: 0% -> 0, 5% -> 50, 15% (and up) -> 100."""
    return _piecewise(op_margin, [(0.0, 0), (0.05, 50), (0.15, 100)])


def fundamental_debt_score(debt_to_equity: float) -> float:
    """Debt/equity: <=100% -> 100, 200% -> 50, >=300% -> 0 (lower is better)."""
    return _piecewise(debt_to_equity, [(1.0, 100), (2.0, 50), (3.0, 0)])


def fundamental_score(revenue_yoy: float | None, op_margin: float | None,
                      debt_to_equity: float | None) -> float:
    """Average of the available sub-scores; 50 (neutral) when none available."""
    subs: list[float] = []
    if revenue_yoy is not None:
        subs.append(fundamental_revenue_score(revenue_yoy))
    if op_margin is not None:
        subs.append(fundamental_margin_score(op_margin))
    if debt_to_equity is not None:
        subs.append(fundamental_debt_score(debt_to_equity))
    if not subs:
        return 50.0
    return sum(subs) / len(subs)
