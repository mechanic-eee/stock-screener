"""Streamlit dashboard for the drawdown stock screener.

Run:  streamlit run app.py
The base drawdown screen is always on; optional filters are toggled in the
sidebar and their parameters are rendered automatically from each filter's
Param spec — so a newly added filter appears here with no UI code changes.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

# make src importable when run via `streamlit run app.py`
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# Streamlit Cloud exposes secrets via st.secrets, not as environment variables.
# Bridge scalar secrets into os.environ so modules that read os.getenv
# (DART_API_KEY, NEWSAPI_KEY, telegram tokens, ...) see them on the hosted app.
try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, str) and _k not in os.environ:
            os.environ[_k] = _v
except Exception:
    pass

from screener import engine, snapshot  # noqa: E402
from screener.data.universe import SECURITY_TYPES, TYPE_LABELS  # noqa: E402
from screener.filters.base import base_filters, get, optional_filters  # noqa: E402
from screener.models import Param  # noqa: E402

st.set_page_config(page_title="폭락주 스크리너", layout="wide")


def _secret(key: str, default: str = "") -> str:
    """Read from st.secrets, falling back to env, then default."""
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


def _check_password() -> bool:
    """Gate the app behind a password if APP_PASSWORD secret is set.

    No secret -> open (local dev). Returns True when access is granted.
    """
    pw = _secret("APP_PASSWORD", "")
    if not pw:
        return True
    if st.session_state.get("_authed"):
        return True
    st.title("🔒 폭락주 스크리너")
    entered = st.text_input("비밀번호", type="password")
    if entered:
        if entered == pw:
            st.session_state["_authed"] = True
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다.")
    st.stop()


_check_password()


def _to_csv(rows: list[dict]) -> str:
    import csv
    import io

    if not rows:
        return ""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def _freshness_banner(source) -> None:
    """Dead-man-switch banner: surface a succeeded-but-stale snapshot.

    A green Actions run only means the script didn't crash. This reads the
    health sidecar (falling back to snapshot meta) and shows a loud warning when
    the price data is old, with how to diagnose it.
    """
    from datetime import date

    h = snapshot.load_health(source)
    last_run = h.get("last_run_utc")
    last_price = h.get("last_price_date") or snapshot.snapshot_meta(source).get("last_date")

    stale_days = None
    if last_price:
        try:
            stale_days = (date.today() - date.fromisoformat(str(last_price)[:10])).days
        except ValueError:
            pass

    parts = []
    if last_run:
        parts.append(f"마지막 스캔 {str(last_run)[:16]}Z")
    if last_price:
        parts.append(f"시세 {last_price}")
    if h.get("snapshot_tickers") is not None:
        parts.append(f"{h['snapshot_tickers']}종목")
    fa, va = h.get("fundamentals_available"), h.get("valuations_available")
    if fa is not None:
        parts.append(f"펀더 {fa:.0%}")
    if va is not None:
        parts.append(f"밸류 {va:.0%}")
    info = " · ".join(parts)

    if stale_days is not None and stale_days > 5:
        st.error(
            f"⚠️ 스냅샷이 오래됐습니다 — 마지막 시세가 {stale_days}일 전. 일일 스캔이 멈췄을 수 "
            f"있어요. 진단: `gh run list`(Actions 성공 여부) · `git fetch origin data`(원격 신선도). "
            + (f"\n\n{info}" if info else "")
        )
    elif info:
        st.caption(f"🟢 {info}")


def render_param(p: Param, key_prefix: str):
    wkey = f"{key_prefix}.{p.key}"
    if p.kind == "int":
        return st.slider(p.label, int(p.min), int(p.max), int(p.default),
                         step=int(p.step or 1), help=p.help, key=wkey)
    if p.kind == "float":
        return st.number_input(p.label, float(p.min), float(p.max), float(p.default),
                               step=float(p.step or 0.1), help=p.help, key=wkey)
    if p.kind == "bool":
        return st.checkbox(p.label, bool(p.default), help=p.help, key=wkey)
    if p.kind == "select":
        return st.selectbox(p.label, p.choices, index=p.choices.index(p.default),
                            help=p.help, key=wkey)
    return p.default


# ---- Sidebar: base screen + universe ----
st.sidebar.header("기본 스크린")
base = base_filters()[0]
base_params = {}
for p in base.params:
    base_params[p.key] = render_param(p, "base")

weights: dict[str, float] = {}
weights[base.key] = st.sidebar.slider(
    f"가중치 · {base.label}", 0.0, 1.0, float(base.weight), step=0.05, key="w.base",
    help="합성 점수에서 이 요소의 상대 비중 (활성 요소들로 정규화됨).",
)

def _stype(c):
    # getattr fallback: tolerate older cached candidates without security_type
    return getattr(c, "security_type", "common")


# ---- Sidebar: data source (+ load action, run before the display filter) ----
st.sidebar.header("데이터 소스")
SNAP_URL = _secret("SNAPSHOT_URL", "")  # raw GitHub URL on the hosted app
snap_available = bool(SNAP_URL) or snapshot.DEFAULT_PATH.exists()
source = st.sidebar.radio(
    "후보 가져오기",
    ["최신 스냅샷 (빠름)", "라이브 스캔 (로컬)"],
    index=0 if snap_available else 1,
    help="스냅샷: 매일 자동 스캔된 후보를 즉시 로드. 라이브: 지금 시세를 받아 스캔(로컬·느림).",
)
live_mode = source.startswith("라이브")
years = base_params.get("years", 5)

if live_mode:
    markets = st.sidebar.multiselect("시장", ["KR", "US"], default=["KR", "US"])
    type_labels = st.sidebar.multiselect(
        "종목 유형", [TYPE_LABELS[t] for t in SECURITY_TYPES], default=[TYPE_LABELS["common"]],
        help="스캔에 포함할 증권 유형. 기본은 보통주만.",
    )
    _label_to_type = {v: k for k, v in TYPE_LABELS.items()}
    include_types = [_label_to_type[lbl] for lbl in type_labels] or ["common"]
    limit = st.sidebar.number_input("스캔 종목 수 제한 (0=전체)", 0, 10000, 200, step=50,
                                    help="처음엔 작게. 전체 스캔은 오래 걸립니다.")
    if st.sidebar.button("🔄 라이브 스캔", type="primary"):
        if not markets:
            st.sidebar.error("시장을 하나 이상 선택하세요.")
        else:
            prog = st.sidebar.progress(0.0, text="시작…")

            def cb(i, total, ticker):
                prog.progress(i / total, text=f"{i}/{total}  {ticker}")

            cands = engine.build_candidates(
                markets, base_params=base_params, years=int(years),
                limit=(int(limit) or None), progress_cb=cb, include_types=include_types,
            )
            prog.empty()
            st.session_state["candidates"] = cands
            st.session_state["scan_meta"] = {"src": "라이브", "n": len(cands)}
else:
    smeta = snapshot.snapshot_meta(SNAP_URL or None)
    if smeta.get("tickers"):
        st.sidebar.caption(f"스냅샷 {smeta['tickers']}종목 · 최종 {smeta.get('last_date','?')} · "
                           f"{'+'.join(smeta.get('markets', []))}")
    if st.sidebar.button("📥 최신 스냅샷 불러오기", type="primary") or (
        st.session_state.get("candidates") is None and snap_available
    ):
        with st.spinner("스냅샷 로드 중…"):
            loaded = snapshot.load_candidates(SNAP_URL or None)

            # Prime the enrichment caches from the sidecars so relative-strength,
            # valuation and fundamentals work on the host without live fetches
            # (^GSPC/KS11, yfinance.info, DART are blocked/rate-limited there).
            # Each is an optimization: if a sidecar is missing/old or priming
            # fails, the filter just falls back to live/neutral — never crash the
            # whole app on load.
            # getattr-by-name (not snapshot.fn directly) so a stale/old snapshot
            # module missing a newer prime_* function degrades gracefully instead
            # of raising AttributeError before the try/except can catch it.
            def _prime(fn_name):
                fn = getattr(snapshot, fn_name, None)
                if fn is None:
                    st.sidebar.caption(f"⚠️ {fn_name} 없음 — 배포 코드 갱신 필요(앱 Reboot)")
                    return {}
                try:
                    return fn(SNAP_URL or None)
                except Exception as e:  # noqa: BLE001
                    st.sidebar.caption(f"⚠️ 사전계산 로드 일부 실패: {type(e).__name__}")
                    return {}

            primed = _prime("prime_benchmarks")
            primed_val = _prime("prime_valuations")
            primed_fund = _prime("prime_fundamentals")
        st.session_state["candidates"] = loaded
        st.session_state["scan_meta"] = {"src": "스냅샷", "n": len(loaded),
                                          "bench": sorted(primed.keys())}
        st.session_state["primed"] = {"val": len(primed_val), "fund": len(primed_fund)}

cands = st.session_state.get("candidates")

# ---- Sidebar: display filters (between data source and indicator filters) ----
shown: list = []
if cands:
    st.sidebar.header("표시 필터 (시장·유형)")
    present_markets = sorted({c.market for c in cands})
    present_types = [t for t in SECURITY_TYPES if any(_stype(c) == t for c in cands)]
    sel_markets = st.sidebar.multiselect("시장", present_markets, default=present_markets,
                                         key="disp.markets")
    _l2t = {v: k for k, v in TYPE_LABELS.items()}
    sel_type_labels = st.sidebar.multiselect(
        "종목 유형", [TYPE_LABELS[t] for t in present_types],
        default=[TYPE_LABELS[t] for t in present_types], key="disp.types",
    )
    sel_types = {_l2t[lbl] for lbl in sel_type_labels}
    shown = [c for c in cands
             if c.market in set(sel_markets) and _stype(c) in sel_types]

# ---- Sidebar: optional indicator filters ----
st.sidebar.header("보조지표 필터")
selected: dict[str, dict] = {}
for flt in optional_filters():
    on = st.sidebar.checkbox(flt.label, value=False, key=f"on.{flt.key}", help=flt.description)
    if on:
        with st.sidebar.expander(f"⚙️ {flt.label} 설정", expanded=True):
            params = {p.key: render_param(p, flt.key) for p in flt.params}
            # bonus filters add to the score directly (no weighted-average slot)
            if not flt.is_bonus:
                weights[flt.key] = st.slider(
                    f"가중치 · {flt.label}", 0.0, 1.0, float(flt.weight),
                    step=0.05, key=f"w.{flt.key}",
                )
        selected[flt.key] = params

news_us = bool(os.getenv("NEWSAPI_KEY", "").strip())                    # US: NewsAPI
news_kr = bool(os.getenv("NAVER_CLIENT_ID", "").strip()
               and os.getenv("NAVER_CLIENT_SECRET", "").strip())        # KR: Naver
if any(get(k).needs_news for k in selected):
    if not news_us and not news_kr:
        st.sidebar.warning("뉴스 필터가 켜졌지만 키가 없습니다 — US는 NEWSAPI_KEY, KR은 "
                           "NAVER_CLIENT_ID/SECRET이 .env에 필요합니다. 결과가 비게 됩니다.")
    elif news_us and not news_kr:
        st.sidebar.info("뉴스: US만 동작합니다(NewsAPI). KR은 NAVER_CLIENT_ID/SECRET이 없어 중립 처리됩니다.")
    elif news_kr and not news_us:
        st.sidebar.info("뉴스: KR만 동작합니다(네이버). US는 NEWSAPI_KEY가 없어 중립 처리됩니다.")

_fund_primed = st.session_state.get("primed", {}).get("fund", 0)
if (any(get(k).needs_fundamentals for k in selected)
        and not os.getenv("DART_API_KEY", "").strip() and not _fund_primed):
    st.sidebar.info("펀더멘털 필터: DART_API_KEY가 없어 KR 종목은 중립(50점, 제외 안 함) 처리됩니다. US는 정상 동작합니다.")

# ---- Main ----
st.title("📉 5년 고가 대비 폭락주 스크리너")
st.caption("기본: 종가 기준 N년 최고가 대비 하락률 ≥ 임계. 보조지표는 사이드바에서 켜고 값 조정.")

if not live_mode:
    _freshness_banner(SNAP_URL or None)

if not cands:
    if live_mode:
        st.info("좌측에서 시장·기준을 정하고 **라이브 스캔**을 누르세요.")
    else:
        st.info("매일 자동 스캔된 **스냅샷**을 불러오세요. 보조지표·가중치는 즉시 반영됩니다.")
else:
    meta = st.session_state.get("scan_meta", {})
    st.success(f"후보 {meta.get('n', len(cands))}종목 ({meta.get('src','?')}) · "
               f"표시 필터·보조지표로 즉시 좁혀집니다.")
    diag: dict[str, list[int]] = {}
    rows = engine.apply_filters(shown, base_params=base_params, selected=selected,
                                weights=weights, diag=diag)
    # Warn about any active filter that got no usable data for *every* evaluated
    # ticker: it fell back to neutral-for-all, so it changes neither the result
    # count nor the ranking (common on the hosted app where live external fetches
    # — RS benchmark, valuation, fundamentals — are blocked/rate-limited).
    for key in selected:
        d = diag.get(key)
        if d and d[1] > 0 and d[0] == d[1]:
            st.warning(
                f"⚠️ '{get(key).label}' 필터: 필요한 데이터를 가져오지 못해 평가된 전 종목이 "
                f"중립(50)으로 처리됐습니다 — 결과 수·순위에 영향이 없습니다. "
                f"(배포 환경에서는 외부 데이터(벤치마크·재무·밸류) 실시간 호출이 차단될 수 있어요.)"
            )
    st.subheader(f"결과: {len(rows)}종목 (점수순) · 후보 {len(shown)}/{len(cands)}")
    if rows:
        front = ["ticker", "name", "market", "점수", "close", "하락률"]
        cols = front + [c for c in rows[0].keys() if c not in front]
        st.dataframe(rows, width="stretch", hide_index=True, column_order=cols)
        st.download_button(
            "결과 CSV 다운로드",
            data=_to_csv(rows),
            file_name="screener_results.csv",
            mime="text/csv",
        )
    else:
        st.warning("조건을 만족하는 종목이 없습니다. 임계값을 완화해 보세요.")
