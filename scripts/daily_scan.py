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
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:  # local runs: pick up TELEGRAM_*/DART_API_KEY from the project .env
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

from screener import cooldown, engine, snapshot  # noqa: E402
from screener.data import db as db_mod  # noqa: E402
from screener.data.universe import SECURITY_TYPES  # noqa: E402
from screener.filters.base import display_groups, label_tiers  # noqa: E402
from screener.notify.telegram import send_message  # noqa: E402

_NAME_NOISE = re.compile(
    r"\s*[-–—]?\s*(Class [A-Z] )?(Common Stock|Common Shares|Ordinary Shares?|"
    r"American Depositary Shares?|Depositary Units.*|ADS|Units?)\s*$", re.IGNORECASE)


def _shorten(name: str, cap: int = 32) -> str:
    """Alert-line name: strip US listing boilerplate, keep the brand."""
    s = str(name).split(" - ")[0]
    s = _NAME_NOISE.sub("", s).strip(" ,")
    return (s[: cap - 1] + "…") if len(s) > cap else s


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
    ap.add_argument("--alert-types", nargs="+", default=["common", "preferred"],
                    choices=SECURITY_TYPES,
                    help="security types eligible for the Telegram alert (default: "
                         "common preferred — the types the enrichment/validation covers; "
                         "funds/ETFs rank on neutral fundamentals = un-validated ties). "
                         "The snapshot keeps ALL scanned types for the app.")
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
    ap.add_argument("--max-price-age-hours", type=float, default=12.0,
                    help="price-cache freshness for this scan (default 12h — strictly shorter "
                         "than the 24h cron cycle so a run can never serve the previous day's "
                         "prices from cache; the 2026-07-16 stale-snapshot incident)")
    ap.add_argument("--no-fresh-guard", action="store_true",
                    help="skip the price-freshness abort/warn (backfills, offline runs)")
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
        max_age_days=args.max_price_age_hours / 24.0,
    )
    print(f"base survivors: {len(cands)} (liquidity floor "
          f"{'off' if args.no_liquidity else 'on'})", flush=True)

    # Fail-loud floor: publishing an empty/tiny snapshot force-pushes over the
    # last good one (orphan data branch = no history to recover). Normal runs
    # see 1000+ survivors; a collapse means an upstream outage, and a FAILED
    # job (dead-man telegram ping) is strictly better than green-but-empty.
    per_market = {m: sum(1 for c in cands if c.market == m) for m in args.markets}
    if len(cands) < 100 or any(n == 0 for n in per_market.values()):
        print(f"ABORT: survivors {len(cands)} (per market {per_market}) below "
              "floor — refusing to overwrite the last good snapshot", flush=True)
        return 1

    # Price-freshness guard (2026-07-16 incident: cron jitter × 1d cache TTL let
    # a run finish in 10min on full cache hits, republishing Wednesday's prices
    # as Thursday's snapshot — a green run with stale data that the paper cohort
    # then recorded as entry prices). >1 business day behind = abort before the
    # good snapshot is overwritten; exactly 1 behind (holiday or one stale day)
    # = loud warning that also rides the Telegram alert.
    stale_warn: list[str] = []
    if not args.no_fresh_guard:
        import datetime as _dt

        def _biz_days_behind(last: _dt.date, today: _dt.date) -> int:
            n, cur = 0, last
            while cur < today:
                cur += _dt.timedelta(days=1)
                if cur.weekday() < 5:
                    n += 1
            return n

        today_utc = _dt.datetime.now(_dt.timezone.utc).date()
        for m in args.markets:
            dates = [c.prices.index.max() for c in cands
                     if c.market == m and c.prices is not None and not c.prices.empty]
            if not dates:
                continue
            last = max(dates).date()
            behind = _biz_days_behind(last, today_utc)
            if behind > 1:
                print(f"ABORT: {m} last price {last} is {behind} business days old — "
                      "stale cache; refusing to publish (see --no-fresh-guard)", flush=True)
                return 1
            if behind == 1:
                msg = f"{m} 시세 {last} (1영업일 낡음 — 휴장 또는 캐시 확인)"
                stale_warn.append(msg)
                print(f"WARN: {msg}", flush=True)

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

    # OHLC tripwire: adjustment-base mixing (raw O/H/L vs adjusted close) hit
    # 39% of US rows on 2026-07-12. Healthy baselines: ~0% US, ~0.9% KR
    # (suspended/기세 rows). Warn via the alert health line at >5%; hard-fail
    # only at the egregious producer-bug level so one bad source day can't
    # kill the whole daily alert.
    try:
        import json as _json

        _h = _json.loads(Path(health_path).read_text(encoding="utf-8"))
        _worst_oh = max((_h.get("ohlc_inconsistent") or {}).values(), default=0.0)
        if _worst_oh > 0.20:
            print(f"ABORT: OHLC inconsistency {_worst_oh:.0%} — adjustment-base "
                  "mixing regression, refusing to publish", flush=True)
            return 1
    except Exception:  # noqa: BLE001 — tripwire must not break a healthy run
        pass

    # Rank the alert by the enrichment composite, not base-only — base alone ties
    # most names at 100 (the falling-knife population the backtest + cohort
    # tracking proved has no edge). The sidecars/SQLite cache are warm from the
    # export step above, so this adds no fetches; no-data signals stay neutral.
    alert_selected = {k: {} for k in (args.alert_indicators or [])}
    rows = engine.apply_filters(cands, base_params=base, selected=alert_selected)
    if alert_selected:
        print(f"alert ranking: base + {'+'.join(args.alert_indicators)} ({len(rows)} after gates)", flush=True)

    # Only validated security types reach the phone: funds/ETFs carry neutral
    # fundamentals, so they'd rank on the un-validated base+ATR tie (a CEF hit
    # #4 on 2026-07-12). Applied BEFORE cooldown so suppressed counts stay
    # coherent. The snapshot itself keeps all types for the app's 표시 필터.
    n_pre = len(rows)
    rows = [r for r in rows if r.get("_security_type", "common") in set(args.alert_types)]
    if len(rows) != n_pre:
        print(f"alert types {'/'.join(args.alert_types)}: {n_pre} -> {len(rows)}", flush=True)

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
    if stale_warn:
        lines.append("⚠️ " + " · ".join(stale_warn))
    if health:
        sf = health.get("signal_fill") or {}
        fa = health.get("fundamentals_available")
        fill = min(sf.values()) if sf else None
        oh = max((health.get("ohlc_inconsistent") or {}).values(), default=None) \
            if health.get("ohlc_inconsistent") else None
        warn = "⚠️ " if ((fa is not None and fa < 0.8)
                         or (fill is not None and fill < 0.5)
                         or (oh is not None and oh > 0.15)) else ""
        hp = [f"시세 {health.get('last_price_date', '?')}"]
        if fa is not None:
            hp.append(f"펀더 {fa:.0%}")
        if fill is not None:
            hp.append(f"신규신호 {fill:.0%}")
        if oh is not None and oh > 0.05:
            hp.append(f"OHLC불일치 {oh:.0%}")
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
    n_new = sum(1 for r in top if r.get("_cooldown") == "신규")
    lines.append(f"상위 (점수순){f' · 🆕 신규 {n_new}' if n_new else ''}:")
    # 핵심(엣지) 기여 태그 — '펀더가 받치는 점수인가'를 폰에서 바로 판별.
    # None(핵심 신호 전부 데이터 없음)은 0%와 다른 상태라 '—'로 구분한다.
    _tiers = label_tiers()
    _core_labels = {lbl for lbl, (gi, _s) in _tiers.items() if gi == 0}
    _groups = display_groups()
    _core_keys = {f.key for f in _groups[0][1]} if _groups else set()
    core_tag = bool(_core_keys & set(args.alert_indicators or []))

    def _core_share(r: dict):
        parts = [p["기여"] for p in r.get("_parts", []) if p["요소"] in _core_labels]
        if not parts:
            return None
        total = r.get("점수") or 0.0
        return round(sum(parts) / total * 100) if total > 0 else 0

    for i, r in enumerate(top, 1):
        new = " 🆕" if r.get("_cooldown") == "신규" else ""  # 처음 알림되는 종목(쿨다운 이력 없음)
        close_s = f"₩{r['close']:,.0f}" if r["market"] == "KR" else f"${r['close']:,.2f}"
        tag = ""
        if core_tag:
            cs = _core_share(r)
            tag = f"·핵심{cs:.0f}%" if cs is not None else "·핵심—"
        lines.append(f"{i}. [{r['market']}] {_shorten(r['name'])} ({r['ticker']}){new} "
                     f"{r['점수']}점{tag} / -{r['하락률']:.0f}% / {close_s}")
    msg = "\n".join(lines)
    # stdout goes to the public repo's Actions log — print WITHOUT the app URL
    # (the dashboard address shouldn't be world-readable even though it is
    # password-gated); only the telegram message carries the tap-through link.
    print(msg, flush=True)
    app_url = os.environ.get("APP_URL", "").strip()
    if app_url:
        msg += f"\n🔗 {app_url}"
    ok = send_message(msg)

    # Record cooldown ONLY for alerts a human could actually see: the month of
    # [telegram-stub] runs proved unconditional recording suppresses the top
    # names precisely when delivery is broken. On failure, log loudly but exit
    # 0 — failing the job over a Telegram hiccup would skip the snapshot
    # publish and stale the app (fail-soft).
    if not ok:
        print("⚠️ 텔레그램 전송 실패 — 쿨다운 미기록 (다음 런에서 재알림)", flush=True)
    elif not args.no_cooldown and top:
        conn = db_mod.get_connection()
        try:
            cooldown.record_alerts(conn, top)
        finally:
            conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
