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
from screener.filters.base import base_filters, display_groups, get  # noqa: E402
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

# ---- Sidebar: optional indicator filters (grouped by pick-priority) ----
st.sidebar.header("보조지표 필터")
selected: dict[str, dict] = {}
for gi, (gtitle, gfilters) in enumerate(display_groups()):
    if gi:
        st.sidebar.divider()
    st.sidebar.caption(gtitle)
    for flt in gfilters:
        on = st.sidebar.checkbox(flt.label, value=False, key=f"on.{flt.key}", help=flt.description)
        if not on:
            continue
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

with st.expander("ℹ️ 점수는 어떻게 매겨지나 · 보조지표 활용법 (처음이면 펼쳐보세요)", expanded=False):
    st.markdown(
        """
#### 📊 `점수` 칼럼은 이렇게 만들어져요
- 켜둔 **모든 지표 + 기본 폭락 스크린**이 각각 **0~100점**을 매기고, 그 점수들을 **가중치로 가중평균**합니다. 가중치 합으로 정규화하니 점수는 **항상 0~100**이에요.
- **보조지표를 하나도 안 켜면** 점수 = 기본 폭락 점수뿐이라 **여러 종목이 동점(예: 100점)**이 됩니다 — 변별이 안 돼요. **지표를 켤수록 순위가 정교**해집니다.
- 기본 폭락 점수는 **종 모양 곡선**: 고가 대비 **−65% 부근에서 정점(100점)**, 너무 얕거나(−50%) 너무 깊으면(−95%↑ = 상폐 위험) 점수가 낮아져요. *"적당히 빠진"* 게 회복 확률이 높다는 가정.
- **카탈리스트(실적)**만 예외 — 가중평균이 아니라 **보너스로 가산**(합계 100 초과 가능).

#### 🎛 보조지표 = 게이트 + 스코어러 (한 지표, 두 역할)
- 각 지표 설정의 **`통과 최소 점수`** 슬라이더가 스위치예요:
  - **`0`(기본)** → 제외 없이 **점수에만** 기여 → *순위만* 바뀜
  - **올리면** → 그 점수 미만 종목을 **탈락**시킴 → *후보 수가 줄어듦*
- **`가중치` 슬라이더** → 중요하게 보는 지표를 올리면 순위에 더 크게 반영돼요.
- **외부 데이터 지표(상대강도·펀더멘털·밸류·뉴스)**는 데이터를 못 받으면 **중립 50점**으로 처리되고 위에 ⚠️ 경고가 떠요 — *"켰는데 안 걸러지는"* 건 버그가 아니라 **데이터 부재 신호**입니다.

#### 🧪 어떤 조합으로 쓰면 좋나 — 폭락주 *회복 후보* 찾기
사이드바 지표는 **위에서부터 중요한 순서**로 정렬돼 있어요. 차원별로 한 개씩 켜는 게 기본기:
- 🥇 **가치함정 거르기** — `펀더멘털`(자동제외) · `알트만 Z`(부도위험) · `피오트로스키 F`(재무 개선 중?) → 폭락엔 이유가 있으니 *망해가는 회사부터* 걷어냄
- 🥈 **싸고 좋은가** — `밸류에이션`(저 PER/PBR) · `퀄리티(매출총이익률)` · `이익의 질(발생액)` → *"빠진 것 ≠ 싼 것"*, 진짜 저평가 우량 분리
- 🥉 **바닥 다지고 도는가** — `변동성 수축(VCP)` · `상대강도(RS)` · `주봉/일봉 MACD` → falling knife 피하고 전환 타이밍
- 🛡 **리스크 체크** — `ATR 리스크/손절` → 변동성·권장 손절폭(사이징)

**후보를 확 줄이려면** 한두 지표의 `통과 최소 점수`를 60~70으로 올려 게이트로 쓰세요.

#### 🔬 백테스트로 검증된 것 (2026-06, point-in-time)
- **점수는 랭킹 필터다** — 폭락주를 *그냥* 사면 동전던지기(승률~40%). 점수 상위는 코호트 평균 대비 **+1~4%p/픽**(KR) 더 번다. 큰돈은 *여러 종목·몇 달 홀드*의 누적에서.
- ★ **랭킹엔 펀더를 반드시 켜라** — 가격지표만으론 *최상위가 역전*(겉만 싼 함정 못 거름). `펀더멘털·알트만·피오트로스키·퀄리티`를 켜야 최상위까지 신뢰. 펀더가 합성 IC를 ~2배로.
- **최강 단일 신호 = `ATR 리스크`**(차분한 종목이 회복, 미친 복권주는 죽음) — 이제 점수에 반영됨. **`이익의 질(발생액)`은 폭락주선 역설**이라 점수에서 빠짐(게이트로만).
- **언제 사나 = 시장 200일선** — 지수가 200일선 위(상승국면)일 때 회복, 아래(하락국면)면 폭락주는 무더기로 같이 깨진다(KR 250d −2.8% vs −16.6%). 일일 알림 "시장:" 라인 참고.
- 자세히: `docs/점수-활용-가이드.md` · `docs/서비스-개요.md`.

> ⚠️ 이 도구는 매수 추천이 아니라 **검토 후보 발굴기**입니다. 점수는 *"먼저 볼 순서"*일 뿐, 최종 판단은 직접 하세요. 개별 보장 없음(최악 −100%) — **분산·손절** 필수.
"""
    )

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
        # hide private keys (e.g. _parts, used only for the breakdown below)
        display_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
        front = ["ticker", "name", "market", "점수", "close", "하락률"]
        cols = front + [c for c in display_rows[0].keys() if c not in front]
        st.dataframe(display_rows, width="stretch", hide_index=True, column_order=cols)
        st.download_button(
            "결과 CSV 다운로드",
            data=_to_csv(display_rows),
            file_name="screener_results.csv",
            mime="text/csv",
        )

        # ---- Score breakdown: why did this name get this score? ----
        st.markdown("##### 🔍 점수 분해 — 왜 이 점수인지")
        opts = {f"{r['name']} ({r['ticker']}) · {r['점수']}점": i for i, r in enumerate(rows)}
        pick = st.selectbox("종목 선택", list(opts.keys()), key="breakdown.pick")
        parts = rows[opts[pick]].get("_parts") or []
        if len(parts) <= 1:
            st.caption("보조지표를 켜면 각 요소의 기여가 여기 분해됩니다 (지금은 기본 폭락 점수뿐).")
        else:
            import pandas as _pd

            bdf = _pd.DataFrame(parts)
            c1, c2 = st.columns([3, 4])
            with c1:
                st.dataframe(bdf, hide_index=True, width="stretch")
            with c2:
                st.bar_chart(bdf.set_index("요소")["기여"], horizontal=True)
            st.caption("**기여** = 가중치 × 점수 ÷ Σ가중치 (활성 요소로 정규화). 기여 합 = 점수"
                       "(카탈리스트 보너스는 정규화 후 가산이라 합이 100을 넘을 수 있음).")
    else:
        st.warning("조건을 만족하는 종목이 없습니다. 임계값을 완화해 보세요.")
