"""Risk-based position sizing — turn an entry + stop into 'how many shares'.

The watchlist now drafts an ATR stop (close - 2.5*ATR); this closes the gap to
*acting* on it: size so that a stop-out loses a fixed fraction (R%) of the
account, capped at a max position weight. This is the standard volatility/risk
sizing (Van Tharp): shares = (account * R%) / (entry - stop).

  python scripts/position_size.py --entry 10050 --stop 9144
  python scripts/position_size.py --entry 160.30 --stop 150 --market US --account 50000 --risk 1 --max-pos 15

Account/risk defaults come from an optional gitignored data/portfolio.json
({"account_krw":..,"account_usd":..,"risk_pct":1.0,"max_pos_pct":20}); --flags
override. Account size is personal, so it is never committed.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:  # Windows consoles default to cp949; the output is Korean + a minus sign
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO = ROOT / "data" / "portfolio.json"
DEFAULTS = {"account_krw": 10_000_000, "account_usd": 10_000, "risk_pct": 1.0, "max_pos_pct": 20.0}


def _load_portfolio() -> dict:
    cfg = dict(DEFAULTS)
    try:
        if PORTFOLIO.exists():
            cfg.update(json.loads(PORTFOLIO.read_text(encoding="utf-8")))
    except Exception:  # noqa: BLE001
        pass
    return cfg


def size_position(entry: float, stop: float, account: float,
                  risk_pct: float = 1.0, max_pos_pct: float = 20.0) -> dict:
    """Risk-based long position size.

    Returns a dict with shares, position value/%, the R-risk amount, the actual
    account-% at risk if stopped, and whether the max-position cap bound it.
    `ok=False` with a reason when the inputs are unusable (stop not below entry).
    """
    if entry <= 0:
        return {"ok": False, "reason": "진입가가 0 이하"}
    if stop >= entry:
        return {"ok": False, "reason": "손절가가 진입가 이상 — 롱 사이징 불가(손절은 진입 아래)"}
    risk_per_share = entry - stop
    risk_amount = account * (risk_pct / 100.0)
    raw_shares = risk_amount / risk_per_share
    max_value = account * (max_pos_pct / 100.0)
    cap_shares = max_value / entry
    capped = raw_shares > cap_shares
    shares = int(math.floor(min(raw_shares, cap_shares)))
    pos_value = shares * entry
    actual_risk = shares * risk_per_share
    return {
        "ok": True,
        "shares": shares,
        "position_value": pos_value,
        "position_pct": (pos_value / account * 100.0) if account else 0.0,
        "risk_per_share": risk_per_share,
        "stop_pct": risk_per_share / entry * 100.0,
        "risk_amount": actual_risk,
        "risk_pct_actual": (actual_risk / account * 100.0) if account else 0.0,
        "capped_by_max_position": capped,
    }


def _fmt(market: str, v: float) -> str:
    return f"{v:,.0f}원" if market == "KR" else f"${v:,.2f}"


def main() -> int:
    cfg = _load_portfolio()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entry", type=float, required=True, help="진입가")
    ap.add_argument("--stop", type=float, required=True, help="손절가 (워치리스트 ATR 자동초안 참고)")
    ap.add_argument("--market", choices=["KR", "US"], default="KR")
    ap.add_argument("--account", type=float, help="계좌 크기 (기본: data/portfolio.json 또는 내장 기본값)")
    ap.add_argument("--risk", type=float, default=cfg["risk_pct"], help="1트레이드 리스크 %% (기본 %(default)s)")
    ap.add_argument("--max-pos", type=float, default=cfg["max_pos_pct"], help="1종목 최대 비중 %% (기본 %(default)s)")
    args = ap.parse_args()

    account = args.account if args.account is not None else (
        cfg["account_krw"] if args.market == "KR" else cfg["account_usd"])

    r = size_position(args.entry, args.stop, account, args.risk, args.max_pos)
    if not r["ok"]:
        print(f"❌ {r['reason']}")
        return 1

    m = args.market
    print(f"진입 {_fmt(m, args.entry)} · 손절 {_fmt(m, args.stop)} (-{r['stop_pct']:.1f}%) · "
          f"계좌 {_fmt(m, account)} · 리스크 {args.risk:.1f}%")
    print(f"  → 권장 수량 {r['shares']:,}주  |  포지션 {_fmt(m, r['position_value'])} "
          f"(계좌 {r['position_pct']:.1f}%)")
    print(f"  → 손절 시 손실 {_fmt(m, r['risk_amount'])} (계좌 {r['risk_pct_actual']:.2f}%)"
          + ("  [최대비중 한도에 막힘 — 리스크%보다 작게]" if r["capped_by_max_position"] else ""))
    if r["shares"] == 0:
        print("  ⚠️ 0주 — 손절폭이 너무 넓거나(변동성↑) 계좌 대비 리스크가 작음. 손절을 좁히거나 리스크%↑.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
