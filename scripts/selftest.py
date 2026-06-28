"""selftest.py — fast regression guard for the validated config + core pipeline.

The 2026-06 validation arc derived a specific scoring config (IC-recalibrated
weights, accruals cut) and a closed loop (decide/monitor/track). This asserts the
load-bearing pieces still hold, so an unrelated edit can't silently revert the
validated weights or break the composite. Runs in ~1s, no network.

  python scripts/selftest.py     # exits non-zero on any failure
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(f"{name}: {detail}")


# 1) filter registry loads, all 20 filters present
from screener.filters import base as fbase  # noqa: E402
fbase.load_all()
keys = {f.key for f in fbase.all_filters()}
check("필터 레지스트리 로드", len(keys) >= 20, f"{len(keys)} filters")

# 2) IC-validated weights (score-validation-2026-06-27) — the config the
#    validation derived; an accidental revert here silently degrades the score.
EXPECT = {
    "atr_risk": 0.20,        # strongest signal, was 0 (turned on)
    "accruals": 0.0,         # cut (negative IC both markets)
    "obv_accumulation": 0.0, "volume_surge": 0.0,   # anti-predictive, out of composite
    "relative_strength": 0.05, "weekly_macd": 0.05,  # ~0 IC, were 0.15
    "rsi": 0.05, "bollinger": 0.05, "moving_average": 0.05,
    "drawdown": 0.10, "vcp_contraction": 0.10, "macd_cross": 0.10,
    "fundamental": 0.25, "altman_z": 0.18, "piotroski": 0.20, "gross_profit": 0.10,
}
for k, w in EXPECT.items():
    actual = fbase.get(k).weight
    check(f"가중치 {k}={w}", abs(actual - w) < 1e-9, f"실제 {actual}")

# 3) composite scoring runs on synthetic prices and stays in 0-100
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from screener import engine  # noqa: E402
from screener.models import TickerData  # noqa: E402

n = 600
idx = pd.bdate_range(end="2026-06-01", periods=n)
# a name down ~60% from an early peak, then basing — should pass the drawdown gate
path = np.concatenate([np.linspace(100, 250, 150), np.linspace(250, 95, 300),
                       np.linspace(95, 100, 150)])
df = pd.DataFrame({"open": path, "high": path * 1.01, "low": path * 0.99,
                   "close": path, "volume": np.full(n, 1_000_000.0)}, index=idx)
data = TickerData(ticker="SYN", market="US", name="SYN", prices=df)
# base-only composite (optional filters can legitimately GATE on synthetic data
# that lacks their signal; the base drawdown gate is the deterministic check).
rows = engine.apply_filters([data], base_params={"years": 5, "min_drop_pct": 50},
                            selected={}, fetch_news=False)
check("기본 스크린 통과(−60% 합성)", len(rows) == 1, f"{len(rows)} rows")
if rows:
    sc = rows[0]["점수"]
    check("합성점수 0~100 범위", 0 <= sc <= 100, f"점수 {sc}")
    check("점수 분해(_parts) 존재", bool(rows[0].get("_parts")), "no _parts")
    # adding a pure scorer (atr_risk, never gates at default) keeps it 0-100
    rows2 = engine.apply_filters([data], base_params={"years": 5, "min_drop_pct": 50},
                                 selected={"atr_risk": {}}, fetch_news=False)
    check("스코어러 합성 0~100", rows2 and 0 <= rows2[0]["점수"] <= 100,
          f"점수 {rows2[0]['점수'] if rows2 else 'no row'}")

# 4) the loop scripts import cleanly (decide/monitor/track + key backtests)
for mod in ("decide", "monitor", "track", "position_size"):
    try:
        __import__(mod)
        check(f"스크립트 import: {mod}", True)
    except Exception as e:  # noqa: BLE001
        check(f"스크립트 import: {mod}", False, str(e))

# 5) scoring curves sanity (accruals: low ratio -> high score, the Sloan prior)
from screener import scoring  # noqa: E402
check("accruals 곡선 방향", scoring.accruals_score(-0.10) > scoring.accruals_score(0.10),
      "부호 역전")
check("altman 곡선 방향", scoring.altman_z_score(3.0) > scoring.altman_z_score(1.0),
      "부호 역전")

print()
if FAILS:
    print(f"❌ {len(FAILS)}건 실패:")
    for f in FAILS:
        print("   - " + f)
    sys.exit(1)
print("✅ 전부 통과 — 검증된 설정·파이프라인 정상.")
