# 실행 방법:
#   streamlit run app.py
#   (프로젝트 루트 C:\stock_trading_project\kr_market 에서 실행)

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import streamlit as st

from engine.Collectors import analyze_chart, get_top_gainers
from engine.config import SignalConfig

st.title("급등 종목 검증 대시보드")

# ── 사이드바 ──────────────────────────────────────────────
with st.sidebar:
    st.header("설정")
    market = st.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])
    top_n = st.slider("출력 개수", min_value=5, max_value=50, value=20)
    collect_btn = st.button("데이터 수집", width="stretch")

config = SignalConfig()

for key in ("raw", "stats", "chart_results"):
    if key not in st.session_state:
        st.session_state[key] = None

# ── 데이터 수집 ───────────────────────────────────────────
if collect_btn:
    with st.spinner(f"{market} 데이터 수집 중..."):
        try:
            raw, stats = get_top_gainers(market, config)
        except Exception as e:
            st.error(f"데이터 수집 실패: {e}")
            st.stop()
    st.session_state.raw = raw
    st.session_state.stats = stats
    st.session_state.chart_results = None  # 시장 변경 시 차트 결과 초기화

# ── 데이터 없음 ───────────────────────────────────────────
if st.session_state.raw is None:
    st.info("사이드바에서 시장과 출력 개수를 선택한 뒤 [데이터 수집] 버튼을 누르세요.")
    st.stop()

raw = st.session_state.raw
stats = st.session_state.stats

if not raw:
    st.error("수집된 데이터가 없습니다.")
    st.stop()

st.caption(
    f"필터 전 {stats['before']}개  →  필터 통과 {stats['after']}개  "
    f"({stats['before'] - stats['after']}개 제외)"
)

df = (
    pd.DataFrame(raw)
    .sort_values("change_rate", ascending=False)
    .head(top_n)
    .reset_index(drop=True)
)
df.index += 1

# ── 주요 통계 ─────────────────────────────────────────────
top_row = df.iloc[0]
total_amount_eok = df["amount"].sum() / 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("수집 종목 수", f"{len(df)}개")
c2.metric("평균 등락률", f"{df['change_rate'].mean():.2f}%")
c3.metric("최고 등락률 종목", top_row["name"], f"{top_row['change_rate']:.2f}%")
c4.metric("총 거래대금", f"{total_amount_eok:,.0f}억원")

st.divider()

# ── 급등 종목 표 ──────────────────────────────────────────
st.subheader("급등 종목")
display_df = df.rename(columns={
    "name": "종목명",
    "code": "종목코드",
    "price": "현재가(원)",
    "change_rate": "등락률(%)",
    "volume": "거래량",
    "amount": "거래대금(백만원)",
})
st.dataframe(
    display_df,
    width="stretch",
    height=600,
    column_config={
        "현재가(원)": st.column_config.NumberColumn(format="%d"),
        "등락률(%)": st.column_config.NumberColumn(format="%.2f%%"),
        "거래량": st.column_config.NumberColumn(format="%d"),
        "거래대금(백만원)": st.column_config.NumberColumn(format="%d"),
    },
)

st.divider()

# ── 차트 분석 ─────────────────────────────────────────────
st.subheader("차트 분석 (정배열 / 52주 고저가)")

ma_keys = [f"ma{p}" for p in config.ma_periods]
ma_labels = [f"MA{p}" for p in config.ma_periods]

if st.button("차트 분석 실행", help=f"종목별 {config.annual_days}일 데이터를 수집합니다. 종목 수에 따라 시간이 걸릴 수 있습니다."):
    stocks = list(zip(df["code"], df["name"]))
    results = []
    progress = st.progress(0, text="차트 데이터 수집 중...")
    for i, (code, name) in enumerate(stocks):
        try:
            analysis = analyze_chart(code, config)
        except Exception:
            analysis = {
                "code": code, "is_golden": None,
                "w52_high": None, "w52_low": None, "pct_from_high": None,
                **{k: None for k in ma_keys},
            }
        analysis["name"] = name
        results.append(analysis)
        progress.progress((i + 1) / len(stocks), text=f"{name} 분석 중... ({i + 1}/{len(stocks)})")
    progress.empty()
    st.session_state.chart_results = results

if st.session_state.chart_results:
    base_keys = ["name", "code", "is_golden", "w52_high", "w52_low", "pct_from_high"]
    base_labels = ["종목명", "코드", "정배열", "연간고가", "연간저가", "고가대비(%)"]

    chart_df = pd.DataFrame(st.session_state.chart_results)[base_keys + ma_keys].copy()
    chart_df.columns = base_labels + ma_labels
    chart_df.index = range(1, len(chart_df) + 1)

    ma_col_config = {label: st.column_config.NumberColumn(format="%.0f") for label in ma_labels}
    st.dataframe(
        chart_df,
        width="stretch",
        column_config={
            "정배열": st.column_config.CheckboxColumn(),
            "연간고가": st.column_config.NumberColumn(format="%d"),
            "연간저가": st.column_config.NumberColumn(format="%d"),
            "고가대비(%)": st.column_config.NumberColumn(format="%.1f%%"),
            **ma_col_config,
        },
    )
