import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional
import warnings

warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="재무분석 RAG 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# 사이드바 네비게이션
def sidebar_navigation():
    st.sidebar.title("📊 재무분석 대시보드")

    pages = {
        "📈 주식 분석": "stock_analysis",
    }

    selected_page = st.sidebar.selectbox("페이지 선택", list(pages.keys()))
    return pages[selected_page]


# 주식 데이터 가져오기
@st.cache_data
def get_stock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """주식 데이터 가져오기"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        return data
    except Exception as e:
        st.error(f"데이터 가져오기 오류: {e}")
        return pd.DataFrame()


# 주식 정보 가져오기
@st.cache_data
def get_stock_info(symbol: str) -> Dict:
    """주식 기본 정보 가져오기"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return info
    except Exception as e:
        st.error(f"정보 가져오기 오류: {e}")
        return {}


# 한국 주식 심볼 변환
def get_korean_stock_symbol(stock_code: str) -> str:
    """한국 주식 코드를 yfinance 심볼로 변환"""
    return f"{stock_code}.KS"


# 기술적 지표 계산
def calculate_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """기술적 지표 계산"""
    # 이동평균선
    data['MA5'] = data['Close'].rolling(window=5).mean()
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['MA60'] = data['Close'].rolling(window=60).mean()

    # RSI 계산
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # 볼린저 밴드
    data['BB_Middle'] = data['Close'].rolling(window=20).mean()
    bb_std = data['Close'].rolling(window=20).std()
    data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
    data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)

    # MACD
    exp1 = data['Close'].ewm(span=12).mean()
    exp2 = data['Close'].ewm(span=26).mean()
    data['MACD'] = exp1 - exp2
    data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
    data['MACD_Histogram'] = data['MACD'] - data['MACD_Signal']

    return data


# 한국 주요 주식 목록
KOREAN_STOCKS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "051910": "LG화학",
    "005380": "현대차",
    "006400": "삼성SDI",
    "035720": "카카오",
    "012330": "현대모비스",
    "028260": "삼성물산",
    "066570": "LG전자",
    "323410": "카카오뱅크",
    "207940": "삼성바이오로직스",
    "068270": "셀트리온",
    "003550": "LG",
    "017670": "SK텔레콤"
}


# 주식 분석 페이지
def stock_analysis_page():
    # 헤더 섹션
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; text-align: center; margin: 0;">📈 주식 분석 대시보드</h1>
        <p style="color: white; text-align: center; margin: 0.5rem 0 0 0; opacity: 0.9;">
            실시간 주식 데이터 분석 및 기술적 지표 제공
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 주식 검색 섹션
    with st.container():
        st.markdown("### 🔍 주식 검색")

        # 탭으로 검색 방식 구분
        tab1, tab2 = st.tabs(["💼 인기 종목", "🔤 직접 입력"])

        with tab1:
            col1, col2 = st.columns([2, 1])
            with col1:
                selected_stock = st.selectbox(
                    "인기 종목 선택",
                    options=list(KOREAN_STOCKS.keys()),
                    format_func=lambda x: f"{x} - {KOREAN_STOCKS[x]}",
                    key="popular_stock"
                )
            with col2:
                st.write("")  # 공간 조정
                st.write("")
                if st.button("📊 분석하기", type="primary", key="analyze_popular"):
                    st.session_state.selected_stock = selected_stock
                    st.session_state.selected_period = "1y"

        with tab2:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                stock_input = st.text_input(
                    "주식 코드 입력",
                    placeholder="예: 005930 (삼성전자)",
                    key="manual_stock"
                )
            with col2:
                period = st.selectbox(
                    "기간 선택",
                    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                    index=3,
                    key="period_select"
                )
            with col3:
                st.write("")  # 공간 조정
                st.write("")
                if st.button("📊 분석하기", type="primary", key="analyze_manual"):
                    if stock_input:
                        st.session_state.selected_stock = stock_input
                        st.session_state.selected_period = period
                    else:
                        st.error("주식 코드를 입력해주세요.")

    # 주식 데이터 분석 결과
    if hasattr(st.session_state, 'selected_stock'):
        symbol = get_korean_stock_symbol(st.session_state.selected_stock)
        period = getattr(st.session_state, 'selected_period', '1y')

        # 로딩 표시
        with st.spinner('데이터를 불러오는 중...'):
            data = get_stock_data(symbol, period)
            stock_info = get_stock_info(symbol)

        if not data.empty:
            # 회사 정보 표시
            company_name = KOREAN_STOCKS.get(st.session_state.selected_stock, "알 수 없음")
            st.markdown(f"## 📊 {company_name} ({st.session_state.selected_stock}) 분석")

            # 기본 정보 카드
            current_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2]
            change = current_price - prev_price
            change_pct = (change / prev_price) * 100

            # 메트릭 카드를 더 시각적으로
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                delta_color = "normal" if change >= 0 else "inverse"
                st.metric("💰 현재가", f"{current_price:,.0f}원",
                          f"{change:+.0f}원 ({change_pct:+.2f}%)",
                          delta_color=delta_color)

            with col2:
                st.metric("📈 최고가", f"{data['High'].max():,.0f}원")

            with col3:
                st.metric("📉 최저가", f"{data['Low'].min():,.0f}원")

            with col4:
                avg_volume = data['Volume'].mean()
                current_volume = data['Volume'].iloc[-1]
                volume_change = ((current_volume - avg_volume) / avg_volume) * 100
                st.metric("📊 거래량", f"{current_volume:,.0f}",
                          f"{volume_change:+.1f}% vs 평균")

            # 기술적 지표 계산
            data = calculate_technical_indicators(data)

            # 차트 섹션
            st.markdown("### 📈 차트 분석")

            # 차트 타입 선택
            chart_type = st.selectbox(
                "차트 유형 선택",
                ["캔들스틱", "라인", "볼린저 밴드", "이동평균선"],
                key="chart_type"
            )

            # 차트 생성
            if chart_type == "캔들스틱":
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='주가',
                    increasing_line_color='#ff6b6b',
                    decreasing_line_color='#4ecdc4'
                ))
                fig.update_layout(
                    title=f"{company_name} 캔들스틱 차트",
                    xaxis_title="날짜",
                    yaxis_title="주가 (원)",
                    height=600,
                    template="plotly_white"
                )

            elif chart_type == "라인":
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['Close'],
                    mode='lines',
                    name='종가',
                    line=dict(color='#667eea', width=2)
                ))
                fig.update_layout(
                    title=f"{company_name} 주가 추이",
                    xaxis_title="날짜",
                    yaxis_title="주가 (원)",
                    height=600,
                    template="plotly_white"
                )

            elif chart_type == "볼린저 밴드":
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['BB_Upper'],
                    mode='lines', name='상한선',
                    line=dict(color='red', dash='dash')
                ))
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['BB_Lower'],
                    mode='lines', name='하한선',
                    line=dict(color='red', dash='dash'),
                    fill='tonexty', fillcolor='rgba(255,0,0,0.1)'
                ))
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['BB_Middle'],
                    mode='lines', name='중간선',
                    line=dict(color='blue')
                ))
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['Close'],
                    mode='lines', name='종가',
                    line=dict(color='black', width=2)
                ))
                fig.update_layout(
                    title=f"{company_name} 볼린저 밴드",
                    xaxis_title="날짜",
                    yaxis_title="주가 (원)",
                    height=600,
                    template="plotly_white"
                )

            elif chart_type == "이동평균선":
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['Close'],
                    name='종가', line=dict(color='black', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['MA5'],
                    name='MA5', line=dict(color='red')
                ))
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['MA20'],
                    name='MA20', line=dict(color='blue')
                ))
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['MA60'],
                    name='MA60', line=dict(color='green')
                ))
                fig.update_layout(
                    title=f"{company_name} 이동평균선",
                    xaxis_title="날짜",
                    yaxis_title="주가 (원)",
                    height=600,
                    template="plotly_white"
                )

            st.plotly_chart(fig, use_container_width=True)

            # 기술적 지표 대시보드
            st.markdown("### 🔍 기술적 지표")

            col1, col2 = st.columns(2)

            with col1:
                # RSI 차트
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(
                    x=data.index, y=data['RSI'],
                    mode='lines', name='RSI',
                    line=dict(color='purple')
                ))
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red",
                                  annotation_text="과매수 (70)")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="blue",
                                  annotation_text="과매도 (30)")
                fig_rsi.update_layout(
                    title="RSI (상대강도지수)",
                    yaxis_title="RSI",
                    height=300,
                    template="plotly_white"
                )
                st.plotly_chart(fig_rsi, use_container_width=True)

            with col2:
                # MACD 차트
                fig_macd = go.Figure()
                fig_macd.add_trace(go.Scatter(
                    x=data.index, y=data['MACD'],
                    mode='lines', name='MACD',
                    line=dict(color='blue')
                ))
                fig_macd.add_trace(go.Scatter(
                    x=data.index, y=data['MACD_Signal'],
                    mode='lines', name='Signal',
                    line=dict(color='red')
                ))
                fig_macd.add_trace(go.Bar(
                    x=data.index, y=data['MACD_Histogram'],
                    name='Histogram',
                    marker_color='green'
                ))
                fig_macd.update_layout(
                    title="MACD",
                    yaxis_title="MACD",
                    height=300,
                    template="plotly_white"
                )
                st.plotly_chart(fig_macd, use_container_width=True)

            # 거래량 차트
            st.markdown("### 📊 거래량 분석")
            fig_volume = go.Figure()
            fig_volume.add_trace(go.Bar(
                x=data.index, y=data['Volume'],
                name='거래량',
                marker_color='lightblue'
            ))
            fig_volume.update_layout(
                title="거래량 추이",
                xaxis_title="날짜",
                yaxis_title="거래량",
                height=300,
                template="plotly_white"
            )
            st.plotly_chart(fig_volume, use_container_width=True)

            # 투자 의견 (간단한 시그널)
            st.markdown("### 💡 투자 참고사항")

            # 현재 RSI 값
            current_rsi = data['RSI'].iloc[-1]
            current_ma5 = data['MA5'].iloc[-1]
            current_ma20 = data['MA20'].iloc[-1]

            col1, col2, col3 = st.columns(3)

            with col1:
                if current_rsi > 70:
                    st.warning("⚠️ RSI 과매수 구간 (70 이상)")
                elif current_rsi < 30:
                    st.success("✅ RSI 과매도 구간 (30 이하)")
                else:
                    st.info("ℹ️ RSI 중립 구간")

            with col2:
                if current_ma5 > current_ma20:
                    st.success("✅ 단기 상승 추세 (MA5 > MA20)")
                else:
                    st.warning("⚠️ 단기 하락 추세 (MA5 < MA20)")

            with col3:
                if change_pct > 0:
                    st.success(f"✅ 전일 대비 상승 ({change_pct:.2f}%)")
                else:
                    st.error(f"❌ 전일 대비 하락 ({change_pct:.2f}%)")

            # 주의사항
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 5px; margin-top: 1rem;">
                <h4>⚠️ 투자 주의사항</h4>
                <ul>
                    <li>위 분석은 참고용이며, 투자 결정은 본인의 판단에 따라 신중히 하시기 바랍니다.</li>
                    <li>과거 데이터를 기반으로 한 분석이므로 미래 수익을 보장하지 않습니다.</li>
                    <li>투자에는 원금 손실의 위험이 있습니다.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.error("❌ 주식 데이터를 불러올 수 없습니다. 주식 코드를 확인해주세요.")

    else:
        # 초기 화면
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background-color: #f8f9fa; border-radius: 10px;">
            <h3>🚀 주식 분석을 시작해보세요!</h3>
            <p>위의 검색 섹션에서 분석하고 싶은 주식을 선택하거나 직접 입력해주세요.</p>
        </div>
        """, unsafe_allow_html=True)


# 메인 함수
def main():
    # 페이지 선택
    current_page = sidebar_navigation()

    # 페이지 라우팅
    if current_page == "stock_analysis":
        stock_analysis_page()


if __name__ == "__main__":
    main()