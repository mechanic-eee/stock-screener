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

from screener import cooldown, engine, snapshot  # noqa: E402
from screener.data import db as db_mod  # noqa: E402
from screener.data.universe import SECURITY_TYPES  # noqa: E402
from screener.notify.telegram import send_message  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--markets", nargs="+", default=["KR", "US"], choices=["KR", "US"])
    ap.add_argument("--types", nargs="+", default=list(SECURITY_TYPES), choices=SECURITY_TYPES,
                    help="security types to include (default: all)")
    ap.add_argument("--min-drop", type=int, default=50)
    ap.add_argument("--years", type=int, default=5)
    ap.add_argument("--no-liquidity", action="store_true",
                    help="disable the per-market liquidity floor (median daily "
                         "turnover + min price; default on, drops un-tradable names)")
    ap.add_argument("--top", type=int, default=15, help="how many to include in the Telegram alert")
    ap.add_argument("--alert-indicators", nargs="*",
                    default=["fundamental", "valuation", "altman_z", "piotroski",
                             "gross_profit", "atr_risk"],
                    help="rank the alert by base + these enrichment signals (sidecars are warm from "
                         "this run, so no extra fetch). Empty list = base-only (legacy). Default is the "
                         "value-trap/distress/quality set — base alone is the falling-knife tie.")
    ap.add_argument("--out", default=str(snapshot.DEFAULT_PATH))
    ap.add_argument("--cooldown-days", type=int, default=cooldown.DEFAULT_BASE_DAYS,
                    help="suppress re-alerts within this many calendar days (PRD §5.6)")
    ap.add_argument("--reset-increase", type=float, default=cooldown.DEFAULT_RESET_INCREASE,
                    help="re-alert sooner if score beats the last alert by this much")
    ap.add_argument("--no-cooldown", action="store_true", help="disable cooldown (alert top-N regardless)")
    ap.add_argument("--no-enrich", action="store_true",
                    help="skip valuation/fundamentals precompute sidecars")
    ap.add_argument("--enrich-types", nargs="+", default=["common", "preferred"], choices=SECURITY_TYPES,
                    help="security types to precompute valuation/fundamentals for (default: common preferred)")
    ap.add_argument("--enrich-workers", type=int, default=8,
                    help="parallel workers for the valuation/fundamentals fetch")
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
        apply_liquidity=not args.no_liquidity,
    )
    print(f"base survivors: {len(cands)} (liquidity floor "
          f"{'off' if args.no_liquidity else 'on'})", flush=True)

    out_path = snapshot.export_candidates(cands, args.out)
    print(f"snapshot written: {out_path} ({len(cands)} tickers)", flush=True)

    # Bake the benchmark series next to the snapshot so the hosted app can run
    # relative-strength without a live ^GSPC/KS11 fetch (blocked on the host).
    bench_path = snapshot.export_benchmarks(args.markets)
    print(f"benchmark snapshot: {bench_path}", flush=True)

    # Precompute valuation/fundamentals bundles into sidecars so the hosted app
    # can run those filters without live yfinance.info / DART calls (blocked on
    # the host). Fundamentals first so KR valuation reuses its warmed cache.
    if not args.no_enrich:
        def ecb(i, total, ticker):
            if i % 100 == 0 or i == total:
                print(f"  enrich {i}/{total}", flush=True)

        fund_path = snapshot.export_fundamentals(
            cands, types=args.enrich_types, max_workers=args.enrich_workers, progress_cb=ecb)
        print(f"fundamentals snapshot: {fund_path}", flush=True)
        val_path = snapshot.export_valuations(
            cands, types=args.enrich_types, max_workers=args.enrich_workers, progress_cb=ecb)
        print(f"valuation snapshot: {val_path}", flush=True)

    # health sidecar (dead-man-switch): lets the app/human tell a succeeded-but-
    # stale run from a healthy one. Written after the sidecars so its available
    # ratios reflect this run.
    health_path = snapshot.export_health(cands, args.markets)
    print(f"health written: {health_path}", flush=True)

    # Rank the alert by the enrichment composite, not base-only — base alone ties
    # most names at 100 (the falling-knife population the backtest + cohort
    # tracking proved has no edge). The sidecars/SQLite cache are warm from the
    # export step above, so this adds no fetches; no-data signals stay neutral.
    alert_selected = {k: {} for k in (args.alert_indicators or [])}
    rows = engine.apply_filters(cands, base_params=base, selected=alert_selected)
    if alert_selected:
        print(f"alert ranking: base + {'+'.join(args.alert_indicators)} ({len(rows)} after gates)", flush=True)

    # cooldown: drop tickers alerted recently unless their score jumped (PRD §5.6)
    suppressed = []
    if args.no_cooldown:
        ranked = rows
    else:
        conn = db_mod.get_connection()
        try:
            ranked, suppressed = cooldown.filter_alerts(
                conn, rows, base_days=args.cooldown_days, reset_increase=args.reset_increase)
        finally:
            conn.close()
        print(f"cooldown: {len(ranked)} alertable, {len(suppressed)} suppressed", flush=True)

    top = ranked[: args.top]
    header = f"\U0001F4C9 폭락주 스캔 ({'+'.join(args.markets)}, -{args.min_drop}%) — 후보 {len(rows)}종목"
    if suppressed:
        header += f" (쿨다운 {len(suppressed)} 제외)"
    # health line: a 'succeeded-but-degraded' run (e.g. new signals 7% filled) is
    # a green Actions run, so surface freshness + fill% in the push itself.
    health = snapshot.load_health(None)
    lines = [header]
    if health:
        sf = health.get("signal_fill") or {}
        fa = health.get("fundamentals_available")
        fill = min(sf.values()) if sf else None
        warn = "⚠️ " if ((fa is not None and fa < 0.8) or (fill is not None and fill < 0.5)) else ""
        hp = [f"시세 {health.get('last_price_date', '?')}"]
        if fa is not None:
            hp.append(f"펀더 {fa:.0%}")
        if fill is not None:
            hp.append(f"신규신호 {fill:.0%}")
        lines.append(f"{warn}건강: " + " · ".join(hp))
    # market-regime line: deep-drawdown picks crash together in a market downtrend
    # and recover in an uptrend (regime-analysis.md — KR 250d -2.8% above the 200DMA
    # vs -16.6% below). Surface whether now is a deploy-friendly window. Fail-soft:
    # if the benchmark isn't available (host fetch blocked), just omit the line.
    try:
        from screener import benchmark as _bench
        reg = []
        for mk in args.markets:
            s = _bench.get_benchmark(mk)
            if s is not None and len(s) >= 200:
                above = float(s.iloc[-1]) >= float(s.tail(200).mean())
                reg.append(f"{mk} {'200일선↑(배치양호)' if above else '200일선↓(주의)'}")
        if reg:
            lines.append("시장: " + " · ".join(reg))
    except Exception:  # noqa: BLE001 — regime line is a bonus, never break the alert
        pass
    lines.append("상위 (점수순):")
    for i, r in enumerate(top, 1):
        lines.append(f"{i}. [{r['market']}] {r['name']} ({r['ticker']}) "
                     f"{r['점수']}점 / {r['하락률']:.0f}% / {r['close']:,}")
    msg = "\n".join(lines)
    print(msg, flush=True)
    send_message(msg)

    # log what we actually alerted so future runs can honor the cooldown
    if not args.no_cooldown and top:
        conn = db_mod.get_connection()
        try:
            cooldown.record_alerts(conn, top)
        finally:
            conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
