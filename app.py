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

from screener import engine  # noqa: E402
from screener.filters.base import base_filters, get, optional_filters  # noqa: E402
from screener.models import Param  # noqa: E402

st.set_page_config(page_title="폭락주 스크리너", layout="wide")


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

st.sidebar.header("유니버스")
markets = st.sidebar.multiselect("시장", ["KR", "US"], default=["KR", "US"])
limit = st.sidebar.number_input("스캔 종목 수 제한 (0=전체)", 0, 10000, 200, step=50,
                                help="처음엔 작게 두고 동작 확인 후 늘리세요. 전체 스캔은 오래 걸립니다.")
years = base_params.get("years", 5)

# ---- Sidebar: optional filters ----
st.sidebar.header("보조지표 필터")
selected: dict[str, dict] = {}
for flt in optional_filters():
    on = st.sidebar.checkbox(flt.label, value=False, key=f"on.{flt.key}", help=flt.description)
    if on:
        with st.sidebar.expander(f"⚙️ {flt.label} 설정", expanded=True):
            params = {p.key: render_param(p, flt.key) for p in flt.params}
        selected[flt.key] = params

news_ready = bool(os.getenv("NEWSAPI_KEY", "").strip())
if any(get(k).needs_news for k in selected) and not news_ready:
    st.sidebar.warning("뉴스 필터가 켜졌지만 NEWSAPI_KEY가 없습니다 (.env 설정 필요) — 결과가 비게 됩니다.")

# ---- Main ----
st.title("📉 5년 고가 대비 폭락주 스크리너")
st.caption("기본: 종가 기준 N년 최고가 대비 하락률 ≥ 임계. 보조지표는 사이드바에서 켜고 값 조정.")

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔄 스캔 (시세 수집·기본 필터)", type="primary"):
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
                )
            prog.empty()
            st.session_state["candidates"] = cands
            st.session_state["scan_meta"] = {"markets": markets, "n": len(cands)}

cands = st.session_state.get("candidates")
if cands is None:
    st.info("좌측에서 시장·기준을 정하고 **스캔**을 누르세요. 스캔 결과(후보군)는 캐시되어, 보조지표는 즉시 다시 필터링됩니다.")
else:
    meta = st.session_state.get("scan_meta", {})
    st.success(f"기본 필터 통과 후보: {meta.get('n', len(cands))}종목  ·  보조지표를 켜면 즉시 좁혀집니다.")
    rows = engine.apply_filters(cands, base_params=base_params, selected=selected)
    st.subheader(f"결과: {len(rows)}종목")
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.download_button(
            "결과 CSV 다운로드",
            data=_to_csv(rows),
            file_name="screener_results.csv",
            mime="text/csv",
        )
    else:
        st.warning("조건을 만족하는 종목이 없습니다. 임계값을 완화해 보세요.")
