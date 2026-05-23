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

markets = ["KR", "US"]
include_types = ["common"]
limit = 0
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

# ---- Sidebar: optional filters ----
st.sidebar.header("보조지표 필터")
selected: dict[str, dict] = {}
for flt in optional_filters():
    on = st.sidebar.checkbox(flt.label, value=False, key=f"on.{flt.key}", help=flt.description)
    if on:
        with st.sidebar.expander(f"⚙️ {flt.label} 설정", expanded=True):
            params = {p.key: render_param(p, flt.key) for p in flt.params}
            weights[flt.key] = st.slider(
                f"가중치 · {flt.label}", 0.0, 1.0, float(flt.weight),
                step=0.05, key=f"w.{flt.key}",
            )
        selected[flt.key] = params

news_ready = bool(os.getenv("NEWSAPI_KEY", "").strip())
if any(get(k).needs_news for k in selected) and not news_ready:
    st.sidebar.warning("뉴스 필터가 켜졌지만 NEWSAPI_KEY가 없습니다 (.env 설정 필요) — 결과가 비게 됩니다.")

# ---- Main ----
st.title("📉 5년 고가 대비 폭락주 스크리너")
st.caption("기본: 종가 기준 N년 최고가 대비 하락률 ≥ 임계. 보조지표는 사이드바에서 켜고 값 조정.")

if live_mode:
    if st.button("🔄 라이브 스캔 (시세 수집·기본 필터)", type="primary"):
        if not markets:
            st.error("시장을 하나 이상 선택하세요.")
        else:
            prog = st.progress(0.0, text="시작…")

            def cb(i, total, ticker):
                prog.progress(i / total, text=f"{i}/{total}  {ticker}")

            with st.spinner("시세 수집 + 기본 필터 적용 중…"):
                cands = engine.build_candidates(
                    markets, base_params=base_params, years=int(years),
                    limit=(int(limit) or None), progress_cb=cb,
                    include_types=include_types,
                )
            prog.empty()
            st.session_state["candidates"] = cands
            st.session_state["scan_meta"] = {"src": "라이브", "n": len(cands)}
else:
    meta = snapshot.snapshot_meta(SNAP_URL or None)
    if meta.get("tickers"):
        st.caption(f"스냅샷: {meta['tickers']}종목 · 최종 {meta.get('last_date','?')} · "
                   f"{'+'.join(meta.get('markets', []))}")
    if st.button("📥 최신 스냅샷 불러오기", type="primary") or (
        st.session_state.get("candidates") is None and snap_available
    ):
        with st.spinner("스냅샷 로드 중…"):
            cands = snapshot.load_candidates(SNAP_URL or None)
        st.session_state["candidates"] = cands
        st.session_state["scan_meta"] = {"src": "스냅샷", "n": len(cands)}

cands = st.session_state.get("candidates")
if not cands:
    if live_mode:
        st.info("좌측에서 시장·기준을 정하고 **라이브 스캔**을 누르세요.")
    else:
        st.info("매일 자동 스캔된 **스냅샷**을 불러오세요. 보조지표·가중치는 즉시 반영됩니다.")
else:
    meta = st.session_state.get("scan_meta", {})
    st.success(f"후보 {meta.get('n', len(cands))}종목 ({meta.get('src','?')}) · 보조지표를 켜면 즉시 좁혀집니다.")

    # ---- display filters: pick market & security type from the loaded set ----
    st.sidebar.header("표시 필터 (시장·유형)")
    present_markets = sorted({c.market for c in cands})
    present_types = [t for t in SECURITY_TYPES if any(c.security_type == t for c in cands)]
    sel_markets = st.sidebar.multiselect("시장", present_markets, default=present_markets, key="disp.markets")
    _l2t = {v: k for k, v in TYPE_LABELS.items()}
    sel_type_labels = st.sidebar.multiselect(
        "종목 유형", [TYPE_LABELS[t] for t in present_types],
        default=[TYPE_LABELS[t] for t in present_types], key="disp.types",
    )
    sel_types = {_l2t[lbl] for lbl in sel_type_labels}
    shown = [c for c in cands
             if c.market in set(sel_markets) and c.security_type in sel_types]

    rows = engine.apply_filters(shown, base_params=base_params, selected=selected, weights=weights)
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
