"""Scheduled daily scan — run by GitHub Actions (or locally / Task Scheduler).

1. Build candidates: base drawdown screen over the full KR+US common universe
   (this is the heavy, network-bound step; uses the SQLite price cache).
2. Export the candidates' price history to data/candidates.parquet (the small
   artifact the hosted app reads).
3. Send a Telegram summary of the top-N by score (base score; the app re-ranks
   interactively with optional indicators).

Env/secrets used (all optional): NEWSAPI_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from screener import engine, snapshot  # noqa: E402
from screener.data.universe import SECURITY_TYPES  # noqa: E402
from screener.notify.telegram import send_message  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--markets", nargs="+", default=["KR", "US"], choices=["KR", "US"])
    ap.add_argument("--types", nargs="+", default=list(SECURITY_TYPES), choices=SECURITY_TYPES,
                    help="security types to include (default: all)")
    ap.add_argument("--min-drop", type=int, default=50)
    ap.add_argument("--years", type=int, default=5)
    ap.add_argument("--top", type=int, default=15, help="how many to include in the Telegram alert")
    ap.add_argument("--out", default=str(snapshot.DEFAULT_PATH))
    args = ap.parse_args()

    base = {"years": args.years, "min_drop_pct": args.min_drop}
    print(f"daily scan: markets={args.markets} types={args.types} "
          f"base=-{args.min_drop}%/{args.years}y", flush=True)

    def cb(i, total, ticker):
        if i % 200 == 0 or i == total:
            print(f"  {i}/{total}", flush=True)

    cands = engine.build_candidates(
        args.markets, base_params=base, years=args.years,
        include_types=args.types, progress_cb=cb,
    )
    print(f"base survivors: {len(cands)}", flush=True)

    out_path = snapshot.export_candidates(cands, args.out)
    print(f"snapshot written: {out_path} ({len(cands)} tickers)", flush=True)

    # rank by base score for the alert
    rows = engine.apply_filters(cands, base_params=base, selected={})
    top = rows[: args.top]
    lines = [f"\U0001F4C9 폭락주 스캔 ({'+'.join(args.markets)}, -{args.min_drop}%) — 후보 {len(rows)}종목",
             "상위 (점수순):"]
    for i, r in enumerate(top, 1):
        lines.append(f"{i}. [{r['market']}] {r['name']} ({r['ticker']}) "
                     f"{r['점수']}점 / {r['하락률']:.0f}% / {r['close']:,}")
    msg = "\n".join(lines)
    print(msg, flush=True)
    send_message(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
