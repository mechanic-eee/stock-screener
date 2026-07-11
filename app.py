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

import pandas as pd
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

try:
    # Streamlit Cloud can serve a fresh app.py against a stale cached submodule
    # (happened before — see LOG 2026-05-25). Guard the newest import so the app
    # degrades (no tier colors / 핵심기여) instead of dying until a reboot.
    from screener.filters.base import label_tiers  # noqa: E402
except ImportError:  # pragma: no cover — stale-deploy fallback
    def label_tiers() -> dict:  # type: ignore[misc]
        return {}

st.set_page_config(page_title="폭락주 스크리너", page_icon="📉", layout="wide",
                   initial_sidebar_state="auto")

# Global CSS: trim Streamlit's oversized paddings and make the layout usable on
# phones (640px is Streamlit's own column-stacking breakpoint). Only stable
# data-testid selectors — never .st-emotion-cache-* (those churn per release).
st.html("""
<style>
[data-testid="stMainBlockContainer"] { padding-top: 2.6rem; padding-bottom: 3rem; }
@media (max-width: 640px) {
  /* keep top padding >= the fixed header height or the title hides under it */
  [data-testid="stMainBlockContainer"] {
    padding-left: 0.9rem; padding-right: 0.9rem; padding-top: 3.2rem;
  }
  /* metric tiles: tighter on small screens */
  [data-testid="stMetric"] { padding: 0.25rem 0.5rem; }
  [data-testid="stMetricValue"] { font-size: 1.35rem; }
}
</style>
""")


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
with st.sidebar:  # render_param uses bare st.* — anchor it to the sidebar
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
def _toggle_group(gkey: str, keys: list[str]) -> None:
    # master checkbox: push its new value down to every filter in the group
    val = st.session_state[gkey]
    for k in keys:
        st.session_state[f"on.{k}"] = val


st.sidebar.header("보조지표 필터")
selected: dict[str, dict] = {}
for gi, (gtitle, gfilters) in enumerate(display_groups()):
    if gi:
        st.sidebar.divider()
    st.sidebar.caption(gtitle)
    gkeys = [f.key for f in gfilters]
    for k in gkeys:
        st.session_state.setdefault(f"on.{k}", False)
    st.sidebar.checkbox(
        "**전체 켜기/끄기**", key=f"grpon.{gi}",
        on_change=_toggle_group, args=(f"grpon.{gi}", gkeys),
        help="이 그룹의 지표를 한번에 켜고 끕니다. 이후 개별 체크는 자유롭게 조정하세요.",
    )
    for flt in gfilters:
        on = st.sidebar.checkbox(flt.label, key=f"on.{flt.key}", help=flt.description)
        if not on:
            continue
        # collapsed: the group master turns on up to 5 filters at once — five
        # auto-opened settings panels would swallow the sidebar
        with st.sidebar.expander(f"⚙️ {flt.label} 설정", expanded=False):
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
def _regime_badges() -> str:
    """시장 레짐(200일선) 배지 — 점수가 '무엇'이라면 200일선은 '언제'.

    검증(KR, 250d): 지수가 200일선 위에서 배치 −2.8% vs 아래 −16.6%
    (docs/regime — 일일 알림의 '시장:' 라인과 동일 기준). 벤치마크는 스냅샷
    사이드카로 primed — 없으면 배지 생략(fail-soft).
    """
    try:
        from screener import benchmark as _bench

        # cached/primed only (peek) — get_benchmark() would live-fetch on a
        # cache miss and block first paint on the hosted app. getattr guards
        # the stale-deploy case where the cached module predates peek().
        _peek = getattr(_bench, "peek", None)
        if _peek is None:
            return ""
        chips = []
        for mk in ("KR", "US"):
            s = _peek(mk)
            if s is None or len(s) < 200:
                continue
            above = float(s.iloc[-1]) >= float(s.tail(200).mean())
            chips.append(
                f":green-badge[▲ {mk} 200일선 위 · 배치 양호]" if above
                else f":red-badge[▼ {mk} 200일선 아래 · 신규 배치 주의]"
            )
        return "  ".join(chips)
    except Exception:  # noqa: BLE001 — 배지는 보너스, 앱을 깨뜨리지 않는다
        return ""


st.markdown("## 📉 폭락주 스크리너")
st.caption("5년 고가 대비 폭락주 중 **회복 가능성 순 랭킹** — 점수는 매수 신호가 아니라 *먼저 볼 순서*입니다.")
_reg = _regime_badges()
if _reg:
    st.markdown(_reg)

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
사이드바 지표는 **선택 우선순위 4그룹**으로 묶여 있어요 (그룹마다 **전체 켜기/끄기** 한 방):
- 🟢 **핵심 — 항상 켜기**: `펀더멘털`·`피오트로스키 F`·`ATR`·`알트만 Z`·`퀄리티(GP)` — 백테스트로 검증된 엣지 그 자체. **이 그룹 마스터 하나면 검증된 랭킹**이 됩니다.
- 🔵 **보강**: `밸류에이션`(비싼 것 게이트) · `발행주식수`(희석 회피) · `VCP`(바닥 구조)
- 🟡 **확증·타이밍**: RS·MACD류·RSI·볼린저·MA·뉴스 — 검증에서 약신호라 낮은 가중
- ⚪ **예측력 없음**: OBV·거래량·발생액 — 검증 음성, 켜지 않는 게 기본

**표의 `핵심기여` 칼럼** = 점수 중 🟢 엣지 신호의 비중 — 높을수록 *펀더가 받치는 점수*라 믿을 만해요.
**행을 클릭**하면 아래 `🔍 점수 분해`에서 요소별 기여·ATR 손절 초안까지 확인.
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
    diag: dict[str, list[int]] = {}
    rows = engine.apply_filters(shown, base_params=base_params, selected=selected,
                                weights=weights, diag=diag)
    # One consolidated notice for filters that got no usable data for *every*
    # evaluated ticker (neutral-for-all → no effect on count or ranking; common
    # on the hosted app where live external fetches are blocked).
    inert = [get(k).label for k in selected
             if (d := diag.get(k)) and d[1] > 0 and d[0] == d[1]]
    if inert:
        st.warning(
            "⚠️ 데이터를 못 받아 **중립(50) 처리**된 지표 — 순위·결과 수에 영향 없음: "
            + " · ".join(f"`{lbl}`" for lbl in inert)
            + "  \n(배포 환경에선 외부 데이터(벤치마크·재무·밸류) 실시간 호출이 차단될 수 있어요.)"
        )

    _tiers = label_tiers()                      # label -> (tier idx, 핵심/보강/확증/제외)
    _core_labels = {lbl for lbl, (gi, _s) in _tiers.items() if gi == 0}
    _groups = display_groups()
    _core_keys = {f.key for f in _groups[0][1]} if _groups else set()

    def _core_share(r: dict):
        """점수 중 🟢 핵심(검증 엣지) 신호가 차지하는 비중(%) — '펀더가 받치는 점수' 판별기.

        None = 이 종목은 핵심 신호가 전부 데이터 없음(중립 처리) — 0%(신호가 낮게
        평가됨)와는 다른 상태라 빈 칸으로 구분한다.
        """
        core_parts = [p["기여"] for p in r.get("_parts", []) if p["요소"] in _core_labels]
        if not core_parts:
            return None
        total = r.get("점수") or 0.0
        if total <= 0:
            return 0.0
        return round(sum(core_parts) / total * 100.0)

    def _fmt_price(market: str, v: float) -> str:
        return f"₩{v:,.0f}" if market == "KR" else f"${v:,.2f}"

    hdr_l, hdr_m, hdr_r = st.columns([5, 3, 2], vertical_alignment="bottom")
    with hdr_l:
        st.subheader(f"결과 {len(rows)}종목")
        st.caption(f"점수순 · 표시 {len(shown)}/{meta.get('n', len(cands))}종목"
                   f"({meta.get('src', '?')}) · 보조지표 {len(selected)}개 활성"
                   " · **행을 클릭하면 아래에 점수 분해**")
    with hdr_m:
        q = st.text_input("종목 검색", key="table.q", label_visibility="collapsed",
                          placeholder="🔎 티커/종목명 검색")
    with hdr_r:
        view = st.segmented_control("표시 컬럼", ["핵심", "전체"], default="핵심",
                                    key="table.view", label_visibility="collapsed")

    if not selected and len(rows) > 1:
        st.info("ℹ️ 지금은 **기본 폭락 점수뿐**이라 동점이 많아 순위 변별력이 없습니다 — "
                "사이드바 **🟢 핵심 그룹 '전체 켜기'** 하나로 검증된 랭킹(펀더·F·ATR·Altman·GP)이 됩니다.")

    if rows:
        # column visibility follows the *selection* (not rows[0]'s data
        # availability — a top row with no fundamentals data would otherwise
        # hide the 핵심기여 column for everyone)
        core_active = bool(_core_keys & set(selected))
        for i, r in enumerate(rows, 1):
            r["_rank"] = i          # global rank, stable across the search filter
        ql = (q or "").strip().lower()
        rows_view = [r for r in rows
                     if not ql
                     or ql in r["ticker"].lower() or ql in str(r["name"]).lower()]
        if not rows_view:
            st.info(f"🔎 '{q}' 검색 결과가 없습니다 — 검색어를 지우면 전체 {len(rows)}종목이 다시 보입니다.")
            st.stop()

        table_rows = []
        detail_cols: list[str] = []
        base_label = base.label
        for r in rows_view:
            tr = {"순위": r["_rank"], "ticker": r["ticker"], "name": r["name"],
                  "market": r["market"], "점수": r["점수"],
                  "가격": _fmt_price(r["market"], r["close"]), "하락률": r["하락률"]}
            if core_active:
                tr["핵심기여"] = _core_share(r)
            for k, v in r.items():
                if k.startswith("_") or k in tr or k in ("close", base_label):
                    continue
                tr[k] = v
                if k not in detail_cols:
                    detail_cols.append(k)
            table_rows.append(tr)

        front = ["순위", "ticker", "name", "market", "점수"]
        if core_active:
            front.append("핵심기여")
        front += ["가격", "하락률"]
        cols = front + (detail_cols if view == "전체" else [])

        colcfg: dict[str, object] = {
            "순위": st.column_config.NumberColumn("순위", width="small", format="%d"),
            "ticker": st.column_config.TextColumn("티커", width="small", pinned=True),
            "name": st.column_config.TextColumn("종목명", width="medium"),
            "market": st.column_config.TextColumn("시장", width="small"),
            "점수": st.column_config.ProgressColumn(
                "점수", min_value=0, max_value=100, format="%.1f",
                help="가중평균 합성점수(0~100) — 매수 신호가 아니라 '먼저 볼 순서'인 랭킹 필터"),
            "핵심기여": st.column_config.NumberColumn(
                "핵심기여", format="%.0f%%",
                help="점수 중 🟢 검증된 엣지(펀더·피오트로스키·ATR·Altman·GP)의 비중 — "
                     "높을수록 '펀더가 받치는 점수'라 신뢰도가 높습니다"),
            "가격": st.column_config.TextColumn("현재가", width="small"),
            "하락률": st.column_config.NumberColumn(
                "하락률", format="-%.0f%%", help="N년 최고가 대비 낙폭(종가 기준)"),
        }
        for lbl in detail_cols:
            colcfg[lbl] = st.column_config.TextColumn(lbl)

        # Fold a fingerprint of the visible row set into the widget key: Streamlit
        # keeps a keyed dataframe's positional selection across reruns even when
        # the data changes, so a shrunken/re-sorted result set would otherwise
        # leave an orphaned index (crash) or silently select the wrong ticker.
        import hashlib

        _fp = hashlib.md5("|".join(tr["ticker"] for tr in table_rows).encode()).hexdigest()[:10]
        event = st.dataframe(
            table_rows, width="stretch", hide_index=True, column_order=cols,
            column_config=colcfg, height=min(521, 42 + 35 * len(table_rows)),
            row_height=35, on_select="rerun", selection_mode="single-row",
            key=f"results.table.{_fp}",
        )
        try:
            _sel = event.selection.rows  # positional index into table_rows
        except Exception:  # noqa: BLE001 — older streamlit or no selection support
            _sel = []
        # belt-and-braces bounds check on top of the fingerprint key
        sel_idx = _sel[0] if _sel and _sel[0] < len(rows_view) else 0

        st.download_button(
            "⬇ 결과 CSV",
            data=_to_csv([{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]),
            file_name="screener_results.csv",
            mime="text/csv",
        )

        # ---- 🔍 점수 분해 2.0: 행 클릭 → 왜 이 점수인지 ----
        r = rows_view[sel_idx]
        parts = r.get("_parts") or []
        with st.container(border=True):
            t_l, t_r = st.columns([8, 2], vertical_alignment="center")
            with t_l:
                st.markdown(f"#### 🔍 점수 분해 — {r['name']} ({r['ticker']})")
                stype = TYPE_LABELS.get(r.get("_security_type", ""), "")
                chips = [f":gray-badge[{r['market']}]"]
                if stype:
                    chips.append(f":gray-badge[{stype}]")
                chips.append(f":orange-badge[고점 대비 −{r['하락률']:.0f}%]")
                if r.get("_missing"):
                    chips.append(f":violet-badge[데이터 없음 {len(r['_missing'])}]")
                st.markdown(" ".join(chips))
            with t_r:
                churl = (f"https://finance.naver.com/item/main.naver?code={r['ticker']}"
                         if r["market"] == "KR"
                         else f"https://finance.yahoo.com/quote/{r['ticker']}")
                st.link_button("차트 ↗", churl, width="stretch")

            scores_all = [x["점수"] for x in rows]
            med = sorted(scores_all)[len(scores_all) // 2]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("합성점수", f"{r['점수']:.1f}",
                      delta=f"{r['점수'] - med:+.1f} vs 중앙값",
                      help="가중평균 0~100 (카탈리스트 보너스는 가산). 랭킹용 — 절대 매수신호 아님")
            _cs = _core_share(r)
            m2.metric("핵심(엣지) 기여", f"{_cs:.0f}%" if _cs is not None else "—",
                      help="🟢 검증된 엣지 5신호(펀더·F·ATR·Altman·GP)가 점수에서 차지하는 비중. "
                           "가격만으로 높은 점수는 최상위에서 역전됩니다(검증) — 펀더가 받치는지 확인하세요. "
                           "'—'는 핵심 지표가 꺼져 있거나 이 종목의 데이터가 없는 상태")
            m3.metric("순위", f"{r.get('_rank', sel_idx + 1)} / {len(rows)}")
            _atr = (r.get("_values") or {}).get("atr_risk")
            if _atr is not None and "atr_risk" in selected:
                _mult = float(selected["atr_risk"].get("stop_mult", 2.5))
                # floor at 0 like scripts/to_watchlist.py — extreme-ATR names
                # would otherwise show a negative 'stop price'
                _stop = max(0.0, r["close"] * (1 - _mult * _atr / 100.0))
                if _stop > 0:
                    m4.metric("ATR 손절 초안", _fmt_price(r["market"], _stop),
                              delta=f"-{_mult * _atr:.0f}% (ATR {_atr:.1f}%)", delta_color="off",
                              help=f"현재가 − {_mult}×ATR — 워치리스트 시드와 같은 공식. "
                                   "변동성이 클수록 손절이 멀어져 포지션을 줄여야 합니다")
                else:
                    m4.metric("ATR 손절 초안", "TBD", delta=f"ATR {_atr:.1f}% 과대", delta_color="off",
                              help="손절폭(배수×ATR)이 가격을 넘어 의미 있는 손절가가 없습니다 — "
                                   "이런 초고변동 종목은 사이징 자체를 재고하세요")
            else:
                m4.metric("ATR 손절 초안", "—",
                          help="ATR 리스크/손절 지표를 켜면 손절 초안가가 계산됩니다")

            try:
                _dark = st.context.theme.type == "dark"
            except Exception:  # noqa: BLE001
                _dark = True
            txt_color = "#d1d5db" if _dark else "#374151"

            if len(parts) <= 1:
                st.info("보조지표를 켜면 요소별 기여가 여기 분해됩니다 — 지금은 기본 폭락 점수뿐이에요. "
                        "사이드바 🟢 핵심 그룹부터 켜보세요.")
            else:
                import altair as alt

                bdf = pd.DataFrame(parts)
                bdf["티어"] = bdf["요소"].map(
                    lambda l: "보너스" if l.endswith("(보너스)")
                    else (_tiers.get(l, (None, "기본(낙폭)"))[1] if l in _tiers else "기본(낙폭)"))
                bdf = bdf.sort_values("기여", ascending=False).reset_index(drop=True)

                tier_domain = ["핵심", "보강", "확증", "제외", "기본(낙폭)", "보너스"]
                tier_range = ["#10b981", "#3b82f6", "#f59e0b", "#9ca3af", "#94a3b8", "#a855f7"]

                c1, c2 = st.columns([5, 6])
                with c1:
                    enc_y = alt.Y("요소:N", sort=None, title=None,
                                  axis=alt.Axis(labelLimit=140))
                    chart = alt.Chart(bdf).mark_bar(cornerRadiusEnd=3).encode(
                        x=alt.X("기여:Q", title="점수 기여"),
                        y=enc_y,
                        color=alt.Color("티어:N",
                                        scale=alt.Scale(domain=tier_domain, range=tier_range),
                                        legend=alt.Legend(orient="bottom", title=None,
                                                          columns=3)),
                        tooltip=["요소", "티어", "점수", "가중치", "기여"],
                    )
                    text = alt.Chart(bdf).mark_text(align="left", dx=4, color=txt_color).encode(
                        x="기여:Q", y=enc_y, text=alt.Text("기여:Q", format=".1f"))
                    st.altair_chart((chart + text).properties(
                        height=max(190, 34 * len(bdf) + 60)), width="stretch")
                with c2:
                    bdf2 = bdf.copy()
                    bdf2["상세"] = bdf2["요소"].map(
                        lambda l: r.get(l.removesuffix(" (보너스)"), ""))
                    st.dataframe(
                        bdf2[["요소", "점수", "가중치", "기여", "상세"]],
                        hide_index=True, width="stretch",
                        height=min(421, 42 + 35 * len(bdf2)), row_height=35,
                        column_config={
                            "요소": st.column_config.TextColumn("요소", width="medium"),
                            "점수": st.column_config.ProgressColumn(
                                "점수", min_value=0, max_value=100, format="%.0f",
                                help="이 지표가 매긴 0~100점 (가중 전)"),
                            "가중치": st.column_config.NumberColumn("가중치", format="%.2f"),
                            "기여": st.column_config.NumberColumn(
                                "기여", format="%.1f",
                                help="가중치 × 점수 ÷ Σ가중치 — 합성점수에 실제로 더해진 양"),
                            "상세": st.column_config.TextColumn("상세"),
                        },
                    )
                if r.get("_missing"):
                    st.caption("⚪ **데이터 없음(중립 처리, 점수 미반영):** "
                               + " · ".join(r["_missing"])
                               + " — 종목 간 분해 요소가 다르면 이 때문입니다.")
                st.caption("**기여** = 가중치 × 점수 ÷ Σ가중치 (활성 요소로 정규화) · 기여 합 = 점수 "
                           "(카탈리스트 보너스는 정규화 후 가산이라 100을 넘을 수 있음)")

            # ---- 📈 가격 맥락: 캐시된 시계열로 낙폭·손절 초안을 그림으로 ----
            _cand = next((c for c in shown if c.ticker == r["ticker"]), None)
            _px = getattr(_cand, "prices", None) if _cand is not None else None
            if _px is not None and not _px.empty and "close" in _px:
                with st.expander(f"📈 가격 차트 — {r['ticker']} (스냅샷 시세, 고점·손절 초안 표시)",
                                 expanded=False):
                    import altair as alt

                    pdf = _px.reset_index()
                    date_col = pdf.columns[0]
                    pdf = pdf.rename(columns={date_col: "date"})[["date", "close"]].dropna()
                    pdf["date"] = pd.to_datetime(pdf["date"])
                    peak = float(pdf["close"].max())
                    rules = [{"y": peak, "lbl": f"최고가 {_fmt_price(r['market'], peak)}",
                              "color": "#9ca3af"}]
                    _atr2 = (r.get("_values") or {}).get("atr_risk")
                    if _atr2 is not None and "atr_risk" in selected:
                        _m2 = float(selected["atr_risk"].get("stop_mult", 2.5))
                        _s2 = max(0.0, r["close"] * (1 - _m2 * _atr2 / 100.0))
                        if _s2 > 0:
                            rules.append({"y": _s2,
                                          "lbl": f"손절 초안 {_fmt_price(r['market'], _s2)}",
                                          "color": "#ef4444"})
                    line = alt.Chart(pdf).mark_line(color="#10b981", strokeWidth=1.5).encode(
                        x=alt.X("date:T", title=None),
                        y=alt.Y("close:Q", title=None,
                                scale=alt.Scale(zero=False)),
                        tooltip=[alt.Tooltip("date:T", title="날짜"),
                                 alt.Tooltip("close:Q", title="종가", format=",.2f")],
                    )
                    rdf = pd.DataFrame(rules)
                    rule = alt.Chart(rdf).mark_rule(strokeDash=[5, 4]).encode(
                        y="y:Q", color=alt.Color("color:N", scale=None))
                    rtxt = alt.Chart(rdf).mark_text(align="left", dx=4, dy=-6,
                                                    color=txt_color).encode(
                        y="y:Q", text="lbl:N", x=alt.value(4))
                    st.altair_chart((line + rule + rtxt).properties(height=260),
                                    width="stretch")
                    st.caption("일일 스캔 캐시 시세(지연) — 현재가 기준선이 아니라 *맥락* 확인용입니다.")
    else:
        st.warning("조건을 만족하는 종목이 없습니다. 임계값을 완화해 보세요.")
