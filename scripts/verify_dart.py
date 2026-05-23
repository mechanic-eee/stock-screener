"""Ad-hoc verification of the KR DART fundamentals path (PRD §5.4.3).

Run after putting a real DART_API_KEY in .env:
    .venv/Scripts/python.exe scripts/verify_dart.py

Prints the corp_code lookup and derived bundle for a few large KR tickers so we
can confirm the DART client works end-to-end (it's untested without a key).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from screener import fundamentals as F  # noqa: E402

KEY = F._dart_key()
print("DART_API_KEY present:", bool(KEY))
if not KEY:
    print("  -> set DART_API_KEY in .env first; aborting.")
    raise SystemExit(1)

cmap = F._load_corp_map(KEY)
print(f"corp_code map size: {len(cmap)}")

SAMPLES = [("005930", "삼성전자"), ("000660", "SK하이닉스"),
           ("035720", "카카오"), ("068270", "셀트리온")]
for ticker, name in SAMPLES:
    corp = cmap.get(ticker)
    b = F.get_fundamentals("KR", ticker, use_cache=False)
    print(f"\n[{ticker}] {name}  corp_code={corp}")
    print(f"  available={b.available} periods={b.periods}")
    if b.available:
        yoy = None if b.revenue_yoy is None else round(b.revenue_yoy, 3)
        m = None if b.op_margin is None else round(b.op_margin, 3)
        d = None if b.debt_to_equity is None else round(b.debt_to_equity, 2)
        print(f"  revenue_yoy={yoy} op_margin={m} debt_to_equity={d} "
              f"4Qloss={b.four_quarters_all_loss} impair={b.capital_impairment}")
