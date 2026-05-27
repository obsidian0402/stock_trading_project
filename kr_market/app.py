# 실행 방법:
#   streamlit run app.py
#   (프로젝트 루트 C:\stock_trading_project\kr_market 에서 실행)

import os
import sys

# app.py 위치(프로젝트 루트)를 sys.path에 추가해 engine 패키지를 찾을 수 있게 함
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import streamlit as st

from engine.Collectors import get_top_gainers
from engine.config import SignalConfig

st.title("급등 종목 검증 대시보드")

# ── 사이드바 ──────────────────────────────────────────────
with st.sidebar:
    st.header("설정")
    market = st.selectbox("시장 선택", ["KOSPI", "KOSDAQ"])
    top_n = st.slider("출력 개수", min_value=5, max_value=50, value=20)
    collect_btn = st.button("데이터 수집", width="stretch")

config = SignalConfig()

# ── 메인 영역 ─────────────────────────────────────────────
if collect_btn:
    with st.spinner(f"{market} 데이터 수집 중..."):
        try:
            raw, stats = get_top_gainers(market, config)
        except Exception as e:
            st.error(f"데이터 수집 실패: {e}")
            st.stop()

    st.caption(
        f"필터 전 {stats['before']}개  →  필터 통과 {stats['after']}개  "
        f"({stats['before'] - stats['after']}개 제외)"
    )

    if not raw:
        st.error("수집된 데이터가 없습니다.")
        st.stop()

    df = (
        pd.DataFrame(raw)
        .sort_values("change_rate", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    df.index += 1  # 순위를 1부터 표시

    # ── 주요 통계 ─────────────────────────────────────────
    top_row = df.iloc[0]
    total_amount_eok = df["amount"].sum() / 100  # 백만원 → 억원

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("수집 종목 수", f"{len(df)}개")
    c2.metric("평균 등락률", f"{df['change_rate'].mean():.2f}%")
    c3.metric(
        "최고 등락률 종목",
        top_row["name"],
        f"{top_row['change_rate']:.2f}%",
    )
    c4.metric("총 거래대금", f"{total_amount_eok:,.0f}억원")

    st.divider()

    # ── 표 출력 ───────────────────────────────────────────
    display_df = df.rename(
        columns={
            "name": "종목명",
            "code": "종목코드",
            "price": "현재가(원)",
            "change_rate": "등락률(%)",
            "volume": "거래량",
            "amount": "거래대금(백만원)",
        }
    )

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
else:
    st.info("사이드바에서 시장과 출력 개수를 선택한 뒤 [데이터 수집] 버튼을 누르세요.")
