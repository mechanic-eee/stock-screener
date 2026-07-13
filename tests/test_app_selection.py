"""Regression tests for the app's result table + score-breakdown pane.

Guards the two 2026-07-12 incidents:
  1. A persisted dataframe row selection surviving a shrinking/re-sorted result
     set (orphaned positional index -> IndexError / wrong-ticker breakdown).
  2. The breakdown pane must follow the visible (searched/filtered) rows.

Runs against a small SYNTHETIC snapshot (no network) via streamlit AppTest.
Invoke directly:  python tests/test_app_selection.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _make_snapshot(path: Path, n: int = 12) -> None:
    """Small candidates.parquet: n tickers, 300 days, deep-drawdown shapes."""
    rng = np.random.default_rng(7)
    frames = []
    dates = pd.bdate_range(end="2026-07-10", periods=300)
    for i in range(n):
        tk = f"TST{i:02d}"
        peak = 100.0 + i
        # decline to between -55% and -90% so the -50% base gate passes
        end = peak * (0.45 - 0.035 * i / n)
        close = np.linspace(peak, end, len(dates)) * (1 + rng.normal(0, 0.01, len(dates)))
        close = np.maximum(close, 0.5)
        df = pd.DataFrame({
            "ticker": tk, "market": "US" if i % 2 else "KR", "name": f"테스트{i:02d}",
            "security_type": "common", "date": dates,
            "open": close * 1.01, "high": close * 1.03, "low": close * 0.97,
            "close": close, "volume": 1_000_000,
        })
        frames.append(df)
    pd.concat(frames, ignore_index=True).to_parquet(path)


def main() -> int:
    from streamlit.testing.v1 import AppTest

    tmp = Path(tempfile.mkdtemp())
    snap = tmp / "candidates.parquet"
    _make_snapshot(snap)
    os.environ["SNAPSHOT_URL"] = str(snap)  # local path is a valid source

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    at.run()
    assert not at.exception, at.exception

    # table + breakdown pane render for the synthetic snapshot
    assert at.main.dataframe, "results table missing"
    metrics = [str(m.label) for m in at.main.metric]
    assert any("합성점수" in m for m in metrics), metrics

    # 1) shrink the result set hard (drawdown 50 -> 85) — must not raise
    #    (the 07-12 orphaned-selection crash path)
    sliders = [s for s in at.sidebar.slider if "최소 하락률" in str(s.label)]
    assert sliders, [str(s.label) for s in at.sidebar.slider]
    sliders[0].set_value(85)
    at.run()
    assert not at.exception, at.exception
    sliders = [s for s in at.sidebar.slider if "최소 하락률" in str(s.label)]
    sliders[0].set_value(50)
    at.run()
    assert not at.exception, at.exception

    # 2) search narrows to one ticker and the breakdown pane follows it
    ti = [t for t in at.main.text_input if str(t.key) == "table.q"]
    assert ti, "search input missing"
    ti[0].set_value("TST03").run()
    assert not at.exception, at.exception
    md = " ".join(str(m.value) for m in at.main.markdown)
    assert "TST03" in md, "breakdown pane does not follow the searched row"

    # 3) nonsense search -> graceful empty state, no exception
    ti = [t for t in at.main.text_input if str(t.key) == "table.q"]
    ti[0].set_value("zzz-none").run()
    assert not at.exception, at.exception
    assert any("검색 결과가 없습니다" in str(i.value) for i in at.info)

    print("OK: selection/search regression tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
