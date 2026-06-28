#!/usr/bin/env python3
"""Composite-score validation backtest (v0.5, price-only, point-in-time).

THE question this project never answered: does the composite *score* the user
sorts by actually rank deep-drawdown names by forward return? calibrate_gates.py
validated the bare gates (and found them ~coin-flips); it *explicitly excludes*
the enrichment scorers. So the score that drives every ranking has never been
backtested — only asserted from academic priors. This measures it.

Design — call the REAL production filters, don't re-implement scoring:
  For each ticker, at each quarterly rebalance date T, slice prices <= T, build a
  TickerData, and call get(key).apply(data). The backtested score is then *byte-
  for-byte* the live score (re-implementing it would validate a different number).

Point-in-time discipline (no look-ahead):
  - scoring sees only the price slice up to T.
  - benchmark is primed with one long series; RS reads only the [T-window, T]
    sub-window (dates from the <=T stock index), so no future index leaks in.
  - forward returns come from the full series AFTER scoring; never fed to a filter.
  - v0.5 is price-only: fundamentals/valuation filters get no data -> skipped.
    That's the *technical half*; v1 adds point-in-time EDGAR/DART for Piotroski/
    Altman/accruals/GP/valuation.

Survivorship:
  - KR: survivors + delisted (delisted held to last traded price — the bankruptcy
    outcome), matching survivorship_check.py.
  - US: no free delisted feed -> survivors-only (optimistic bias; documented).

Outputs (per horizon 60/120/250d):
  - per-signal Information Coefficient: pooled Spearman + mean-of-per-date IC with
    a t-stat and the share of dates with positive IC (the honest, overlap-robust
    number). Tells you WHICH signals carry predictive load -> weight/prune.
  - composite decile table: mean fwd return, win%, Sharpe per decile, plus the
    top-minus-bottom spread and a monotonicity Spearman. Tells you if the ranking
    itself is real.

Usage:
    python backtest/composite_decile_backtest.py --market US
    python backtest/composite_decile_backtest.py --market KR --start-year 2016
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from screener import benchmark, indicators  # noqa: E402
from screener.engine import LIQUIDITY_FLOORS  # noqa: E402
from screener.filters import base as fbase  # noqa: E402
from screener.models import TickerData  # noqa: E402

fbase.load_all()

HORIZONS = [60, 120, 250]
MIN_HISTORY = 252  # >=1y of prices before T for indicators to be meaningful


# --- signal set: mirror engine.apply_filters' tech_keys (price-only optionals) ---
def price_filter_keys() -> list[str]:
    keys = []
    for f in fbase.optional_filters():
        if f.needs_news or f.needs_fundamentals or f.needs_valuation or f.is_bonus:
            continue
        keys.append(f.key)
    return keys


def prime_benchmark(market: str) -> int:
    """Fetch a long benchmark series (one network call) and prime the cache so the
    RS filter reads it point-in-time. Returns row count (0 on failure -> RS neutral)."""
    try:
        if market == "US":
            import yfinance as yf
            df = yf.download("^GSPC", start="2015-01-01", progress=False, auto_adjust=True)
            s = df["Close"]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            s = s.dropna()
        else:
            import FinanceDataReader as fdr
            df = fdr.DataReader("KS11", "2015-01-01")
            s = df["Close"].dropna()
        s.index = pd.to_datetime(s.index)
        benchmark.prime({market: s})
        return len(s)
    except Exception as e:  # noqa: BLE001 — fail-soft: RS just goes neutral
        print(f"  benchmark prime failed ({market}): {e} -> RS will be neutral", flush=True)
        return 0


def load_prices(market: str):
    suffix = "us" if market == "US" else "kr"
    df = pd.read_parquet(ROOT / "exports" / f"prices_{suffix}.parquet")
    df["date"] = pd.to_datetime(df["date"])
    df = df[["ticker", "date", "adj_close", "volume"]]
    delisted: set[str] = set()
    if market == "KR":
        dp = ROOT / "exports" / "prices_kr_delisted.parquet"
        if dp.exists():
            dd = pd.read_parquet(dp)
            dd["date"] = pd.to_datetime(dd["date"])
            delisted = set(dd["ticker"].unique())
            df = pd.concat([df, dd[["ticker", "date", "adj_close", "volume"]]], ignore_index=True)
    return df, delisted


def ticker_frame(g: pd.DataFrame) -> pd.DataFrame:
    """Per-ticker OHLCV frame the filters expect. The parquet carries adj_close +
    volume only, so high/low/open := close (atr then equals |close-to-close|, its
    documented fallback; every other price filter uses close alone)."""
    g = g.sort_values("date")
    idx = pd.DatetimeIndex(g["date"].values)
    close = g["adj_close"].astype(float).values
    vol = g["volume"].astype(float).values
    return pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close, "volume": vol},
        index=idx,
    )


def rebalance_dates(start_year: int, end_year: int) -> pd.DatetimeIndex:
    out = []
    for y in range(start_year, end_year + 1):
        for md in ("03-31", "06-30", "09-30", "12-31"):
            out.append(pd.Timestamp(f"{y}-{md}"))
    return pd.DatetimeIndex(out)


def build_panel(df, delisted, market, rdates, pkeys, fund_keys=None, fund_getter=None,
                progress_every=200) -> pd.DataFrame:
    floor_turn, floor_price = LIQUIDITY_FLOORS[market]
    base = fbase.base_filters()[0]
    fund_keys = fund_keys or []
    records = []
    tickers = df["ticker"].unique()
    for ti, (ticker, g) in enumerate(df.groupby("ticker", sort=False), 1):
        if ti % progress_every == 0:
            print(f"  {ti}/{len(tickers)} tickers, {len(records)} cohort rows", flush=True)
        fr = ticker_frame(g)
        if len(fr) < MIN_HISTORY:
            continue
        dates = fr.index
        closev = fr["close"].values
        n = len(fr)
        is_delisted = ticker in delisted
        for T in rdates:
            pos = int(dates.searchsorted(T, side="right")) - 1
            if pos < MIN_HISTORY:
                continue
            slice_fr = fr.iloc[: pos + 1]
            data = TickerData(ticker=ticker, market=market, name=ticker, prices=slice_fr)
            bout = base.apply(data, {"years": 5, "min_drop_pct": 50})
            if not bout.passed:
                continue
            # production liquidity floor (computed on the <=T slice, no future leak)
            last_close = float(slice_fr["close"].iloc[-1])
            turn = indicators.median_turnover(slice_fr["close"], slice_fr["volume"], days=20)
            if last_close < floor_price or not (turn >= floor_turn):
                continue
            rec = {
                "ticker": ticker, "date": T, "pos": pos,
                "drawdown_pct": bout.value,
                "_score_drawdown": float(bout.score), "_avail_drawdown": True,
            }
            for k in pkeys:
                out = fbase.get(k).apply(data)
                rec[f"_score_{k}"] = float(out.score) if out.available else np.nan
                rec[f"_avail_{k}"] = bool(out.available)
            # point-in-time fundamentals (v1): set data.fundamentals as known at T,
            # then score the fundamental filters with the SAME production code.
            if fund_keys and fund_getter is not None:
                data.fundamentals = fund_getter(ticker, T.strftime("%Y-%m-%d"))
                for k in fund_keys:
                    out = fbase.get(k).apply(data)
                    rec[f"_score_{k}"] = float(out.score) if out.available else np.nan
                    rec[f"_avail_{k}"] = bool(out.available)
            for h in HORIZONS:
                j = pos + h
                if j < n:
                    rec[f"fwd_{h}"] = (closev[j] - closev[pos]) / closev[pos] * 100.0
                elif is_delisted:
                    rec[f"fwd_{h}"] = (closev[-1] - closev[pos]) / closev[pos] * 100.0
                else:
                    rec[f"fwd_{h}"] = np.nan
            records.append(rec)
    return pd.DataFrame(records)


def add_composites(panel: pd.DataFrame, sig_keys: list[str], tag: str = "") -> pd.DataFrame:
    weights = {k: fbase.get(k).weight for k in sig_keys}
    score_cols = [f"_score_{k}" for k in sig_keys]
    w_arr = np.array([weights[k] for k in sig_keys], dtype=float)
    S = panel[score_cols].to_numpy(dtype=float)
    avail = ~np.isnan(S)
    # production composite: sum(w*score)/sum(w) over AVAILABLE signals (dilution guard)
    num = np.nansum(np.where(avail, S * w_arr, 0.0), axis=1)
    den = (np.where(avail, w_arr, 0.0)).sum(axis=1)
    panel[f"composite{tag}"] = np.where(den > 0, num / den, np.nan)
    # equal-weight composite (a weight-free sanity check)
    eq_num = np.nansum(np.where(avail, S, 0.0), axis=1)
    eq_den = avail.sum(axis=1)
    panel[f"composite_eq{tag}"] = np.where(eq_den > 0, eq_num / eq_den, np.nan)
    return panel


def spearman(s1: pd.Series, s2: pd.Series) -> float:
    """Spearman rank correlation = Pearson on ranks. Done by hand so the backtest
    needs no scipy (pandas' method='spearman' imports scipy.stats)."""
    return s1.rank().corr(s2.rank())  # pandas Pearson default — no scipy


def pooled_ic(panel, score_col, ret_col):
    s = panel[[score_col, ret_col]].dropna()
    if len(s) < 20:
        return np.nan, len(s)
    return spearman(s[score_col], s[ret_col]), len(s)


def per_date_ic(panel, score_col, ret_col, min_names=8):
    ics = []
    for _, grp in panel.groupby("date"):
        s = grp[[score_col, ret_col]].dropna()
        if len(s) >= min_names and s[score_col].nunique() > 1:
            ic = spearman(s[score_col], s[ret_col])
            if pd.notna(ic):
                ics.append(ic)
    if not ics:
        return np.nan, np.nan, np.nan, 0
    a = np.array(ics)
    mean = a.mean()
    t = mean / (a.std(ddof=1) / np.sqrt(len(a))) if len(a) > 1 and a.std(ddof=1) > 0 else np.nan
    pos_share = (a > 0).mean()
    return mean, t, pos_share, len(a)


def decile_table(panel, score_col, ret_col, qn=10):
    s = panel[[score_col, ret_col]].dropna().copy()
    if len(s) < 30:
        return None
    qn = min(qn, max(3, len(s) // 15))
    try:
        s["q"] = pd.qcut(s[score_col].rank(method="first"), qn, labels=False)
    except Exception:
        return None
    rows = []
    for q, grp in s.groupby("q"):
        v = grp[ret_col]
        rows.append({
            "decile": int(q) + 1, "n": len(v), "mean": v.mean(),
            "win": (v > 0).mean(), "median": v.median(),
            "sharpe": v.mean() / v.std() if v.std() > 0 else 0.0,
        })
    tbl = pd.DataFrame(rows)
    mono = spearman(tbl["decile"], tbl["mean"])
    spread = tbl["mean"].iloc[-1] - tbl["mean"].iloc[0]
    return tbl, mono, spread


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", choices=["US", "KR"], required=True)
    ap.add_argument("--start-year", type=int, default=2017)
    ap.add_argument("--end-year", type=int, default=2024)
    ap.add_argument("--out", default=None)
    ap.add_argument("--fundamentals", choices=["none", "edgar", "dart"], default="none",
                    help="edgar = PIT US fundamentals (SEC EDGAR); dart = PIT KR fundamentals "
                         "(DART historical, needs DART_API_KEY) — v1")
    args = ap.parse_args()

    pkeys = price_filter_keys()
    sig_keys = ["drawdown"] + pkeys
    print(f"[{args.market}] price signals: {', '.join(sig_keys)}", flush=True)

    # v1: point-in-time fundamentals (US/EDGAR). The getter caches companyfacts per
    # ticker and slices to <=T; _signals_from_rows(rows,'KR') reuses production
    # scoring (annual rows -> KR path makes _annualized_flow a no-op).
    fund_keys: list[str] = []
    fund_getter = None
    if args.fundamentals == "edgar":
        if args.market != "US":
            print("--fundamentals edgar is US-only (KR needs DART_API_KEY → v1b)", flush=True)
            return 1
        import edgar_pit
        from screener import fundamentals as fund
        from screener.models import FundamentalsBundle
        fund_keys = [f.key for f in fbase.optional_filters() if f.needs_fundamentals]
        cmap = edgar_pit.load_cik_map()
        _facts: dict[str, object] = {}

        def fund_getter(ticker, T):
            if ticker not in _facts:
                cik = cmap.get(ticker.upper())
                _facts[ticker] = (edgar_pit.fetch_companyfacts(cik) if cik else None)
            cf = _facts[ticker]
            if not cf:
                return FundamentalsBundle(available=False)
            rows = edgar_pit.pit_rows(cf, T)
            return fund._signals_from_rows(rows, market="KR") if rows else FundamentalsBundle(available=False)

        print(f"[US] fundamentals: EDGAR point-in-time ({len(cmap)} CIKs), "
              f"signals: {', '.join(fund_keys)}", flush=True)

    elif args.fundamentals == "dart":
        if args.market != "KR":
            print("--fundamentals dart is KR-only", flush=True)
            return 1
        import os
        import dart_pit
        from screener import fundamentals as fund
        from screener.models import FundamentalsBundle
        key = os.getenv("DART_API_KEY")
        if not key:
            print("DART_API_KEY not set in env (pass it inline for the run)", flush=True)
            return 1
        fund_keys = [f.key for f in fbase.optional_filters() if f.needs_fundamentals]
        cmap = fund._load_corp_map(key)
        _missing = {"n": 0}

        def fund_getter(ticker, T):
            corp = cmap.get(ticker)
            if not corp:
                _missing["n"] += 1
                return FundamentalsBundle(available=False)
            rows = dart_pit.pit_rows(key, corp, T)
            return fund._signals_from_rows(rows, market="KR") if rows else FundamentalsBundle(available=False)

        print(f"[KR] fundamentals: DART point-in-time ({len(cmap)} corps), "
              f"signals: {', '.join(fund_keys)}", flush=True)

    nb = prime_benchmark(args.market)
    print(f"  benchmark primed: {nb} rows", flush=True)

    df, delisted = load_prices(args.market)
    print(f"  prices: {df['ticker'].nunique()} tickers"
          f"{f' (+{len(delisted)} delisted)' if delisted else ''}, "
          f"{df['date'].min().date()} -> {df['date'].max().date()}", flush=True)

    rdates = rebalance_dates(args.start_year, args.end_year)
    panel = build_panel(df, delisted, args.market, rdates, pkeys, fund_keys, fund_getter)
    if panel.empty:
        print("no cohort rows — check data range / floors", flush=True)
        return 1
    panel = add_composites(panel, sig_keys)
    if fund_keys:
        panel = add_composites(panel, sig_keys + fund_keys, tag="_full")
    print(f"  cohort rows: {len(panel)} "
          f"(unique names {panel['ticker'].nunique()}, "
          f"dates {panel['date'].nunique()})", flush=True)

    # ---- analysis ----
    lines: list[str] = []

    def emit(s=""):
        print(s, flush=True)
        lines.append(s)

    mode = "v1 (가격+펀더·point-in-time)" if fund_keys else "v0.5 (가격기반·point-in-time)"
    emit(f"# 점수 검증 백테스트 ({mode}) — {args.market}")
    emit("")
    emit(f"_생성: {datetime.now().isoformat(timespec='seconds')}_  ")
    emit(f"_코호트: {args.start_year}~{args.end_year} 분기말 리밸런스, 고가대비 -50%(5y) + 유동성하한_  ")
    emit(f"_관측: {len(panel)}행 · 종목 {panel['ticker'].nunique()} · 날짜 {panel['date'].nunique()} · "
         f"벤치마크 {nb}행_")
    if args.market == "US":
        emit("_⚠️ US는 상폐 무료피드 부재 → 생존자-only(낙관 편향). KR은 상폐 보정._")
    emit("")
    if fund_keys:
        src = ("SEC EDGAR companyfacts (`filed≤T` 연간 10-K)" if args.fundamentals == "edgar"
               else "DART 과거 사업보고서 (`T≥다음해 4/1`인 FY)" if args.fundamentals == "dart"
               else "point-in-time")
        emit(f"> **v1**: 가격신호 + **point-in-time 펀더**({src}). "
             "Piotroski·Altman·accruals·GP·share·fundamental을 production 코드로 채점 → "
             "프로젝트 핵심 가설('enrichment이 엣지')의 직접 검증. "
             "(KR은 DART에 발행주식수 부재 → share_issuance 0% 커버리지, 합성은 5신호.)")
    else:
        emit("> v0.5는 **가격기반 신호만** 검증한다(기술적 절반). 펀더(Piotroski·Altman·accruals·GP·"
             "valuation)는 point-in-time 재무가 필요 → v1(EDGAR/DART).")
    emit("")

    # cohort forward-return baseline (the 'just buy the cohort' return to beat)
    emit("## 0. 코호트 기준선 (점수 무시, 그냥 다 산다)")
    emit("")
    emit("| 지평 | 평균 | 중앙값 | 승률 | n |")
    emit("|---|---:|---:|---:|---:|")
    for h in HORIZONS:
        v = panel[f"fwd_{h}"].dropna()
        if len(v):
            emit(f"| {h}d | {v.mean():+.1f}% | {v.median():+.1f}% | {(v>0).mean():.0%} | {len(v)} |")
    emit("")

    # per-signal IC
    emit("## 1. 신호별 정보계수(IC) — 어떤 신호가 예측력을 갖나")
    emit("")
    emit("Spearman(점수, forward수익률). **per-date IC**(날짜별 횡단면 IC의 평균)이 "
         "겹치는 수익률창에 견고한 정직한 수치다. |t|≳2면 0과 유의하게 다름.")
    emit("")
    for h in HORIZONS:
        ret = f"fwd_{h}"
        emit(f"### {h}일 지평")
        emit("")
        emit("| 신호 | 가중치 | pooled IC | per-date IC | t | +IC날짜% | 데이터% |")
        emit("|---|---:|---:|---:|---:|---:|---:|")
        for k in sig_keys + fund_keys:
            sc = f"_score_{k}"
            if sc not in panel:
                continue
            p_ic, p_n = pooled_ic(panel, sc, ret)
            d_ic, d_t, d_pos, d_nd = per_date_ic(panel, sc, ret)
            avail_rate = panel[f"_avail_{k}"].mean() if f"_avail_{k}" in panel else np.nan
            w = fbase.get(k).weight
            mark = " ⓕ" if k in fund_keys else ""
            emit(f"| {k}{mark} | {w:.2f} | {p_ic:+.3f} | {d_ic:+.3f} | "
                 f"{d_t:+.1f} | {d_pos:.0%} | {avail_rate:.0%} |"
                 .replace("nan", "—").replace("+—", "—"))
        # composite rows
        comp_rows = [("composite", "합성(가격·prod)"), ("composite_eq", "합성(가격·동일)")]
        if fund_keys:
            comp_rows += [("composite_full", "합성(가격+펀더·prod)"),
                          ("composite_eq_full", "합성(가격+펀더·동일)")]
        for comp, lbl in comp_rows:
            if comp not in panel:
                continue
            p_ic, _ = pooled_ic(panel, comp, ret)
            d_ic, d_t, d_pos, _ = per_date_ic(panel, comp, ret)
            emit(f"| **{lbl}** | — | **{p_ic:+.3f}** | **{d_ic:+.3f}** | "
                 f"**{d_t:+.1f}** | {d_pos:.0%} | — |".replace("nan", "—"))
        emit("")

    # composite decile spread
    emit("## 2. 합성점수 decile — 순위가 실제로 작동하나")
    emit("")
    decile_sets = [("composite", "가격·production 가중"), ("composite_eq", "가격·동일 가중")]
    if fund_keys:
        decile_sets += [("composite_full", "가격+펀더·production 가중")]
    for comp, lbl in decile_sets:
        emit(f"### {lbl} 합성점수")
        emit("")
        for h in HORIZONS:
            res = decile_table(panel, comp, f"fwd_{h}")
            if res is None:
                emit(f"- {h}d: 표본 부족")
                continue
            tbl, mono, spread = res
            emit(f"**{h}일** — 단조성 Spearman(decile,평균) = **{mono:+.2f}**, "
                 f"상위-하위 스프레드 = **{spread:+.1f}%p**")
            emit("")
            emit("| decile | n | 평균 | 중앙값 | 승률 | Sharpe |")
            emit("|---:|---:|---:|---:|---:|---:|")
            for _, r in tbl.iterrows():
                emit(f"| {int(r['decile'])} | {int(r['n'])} | {r['mean']:+.1f}% | "
                     f"{r['median']:+.1f}% | {r['win']:.0%} | {r['sharpe']:.2f} |")
            emit("")

    # verdict scaffold (numbers filled, judgement noted)
    emit("## 3. 판정")
    emit("")
    best_h = 120
    res = decile_table(panel, "composite", f"fwd_{best_h}")
    if res is not None:
        _, mono, spread = res
        d_ic, d_t, d_pos, _ = per_date_ic(panel, "composite", f"fwd_{best_h}")
        verdict = ("순위 유효(단조+양의 IC)" if (mono > 0.5 and (d_ic or 0) > 0)
                   else "혼재/약함 — 가중치 재설계 필요" if (d_ic or 0) > 0
                   else "순위 무효 — 점수가 forward수익률과 무관/역상관")
        emit(f"- **{best_h}d 합성(가격·prod):** 단조 {mono:+.2f}, per-date IC {d_ic:+.3f} "
             f"(t {d_t:+.1f}, +날짜 {d_pos:.0%}), 상위-하위 {spread:+.1f}%p → **{verdict}**")
    if fund_keys:
        # the v1 question: does adding point-in-time fundamentals lift the composite?
        pic, _ = pooled_ic(panel, "composite", f"fwd_{best_h}")
        fic, ft, fpos, _ = per_date_ic(panel, "composite_full", f"fwd_{best_h}")
        bic, bt, bpos, _ = per_date_ic(panel, "composite", f"fwd_{best_h}")
        lift = "올라감 → 가설 지지" if (fic or 0) > (bic or 0) else "안 올라감 → 펀더 기여 약함"
        emit(f"- **펀더 추가 효과({best_h}d):** 가격합성 IC {bic:+.3f}(t{bt:+.1f}) → "
             f"가격+펀더 IC {fic:+.3f}(t{ft:+.1f}) — **{lift}**")
        emit("- 펀더 신호(ⓕ)별 IC는 §1 참조. 양(+)이 크면 enrichment 가설의 직접 증거; "
             "0/음수면 해당 펀더 신호는 폭락주 유니버스에서 재고 대상.")
    else:
        emit("- 신호별 IC 표(§1)에서 IC가 0 근처/음수인 신호는 가중치 축소·제거 후보, "
             "양의 IC가 큰 신호는 가중치 상향 후보.")
        emit("- v1(펀더 point-in-time) 후 Piotroski·Altman·accruals·GP의 IC가 채워지면 "
             "프로젝트 핵심 가설('enrichment이 엣지')이 직접 검증된다.")
    emit("")

    suffix = f"-{args.market}" + ("-v1" if fund_keys else "")
    out = args.out or str(ROOT / "docs" / f"score-validation{suffix}.md")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwritten: {out}", flush=True)

    # also stash the raw panel for later (weight optimization / re-analysis)
    panel_out = ROOT / "exports" / f"validation_panel_{args.market}{'_v1' if fund_keys else ''}.parquet"
    comp_cols = [c for c in ("composite", "composite_eq", "composite_full", "composite_eq_full")
                 if c in panel]
    keep = ["ticker", "date", "pos", "drawdown_pct"] + comp_cols + \
           [f"_score_{k}" for k in (sig_keys + fund_keys) if f"_score_{k}" in panel] + \
           [f"fwd_{h}" for h in HORIZONS]
    panel[keep].to_parquet(panel_out)
    print(f"panel: {panel_out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
