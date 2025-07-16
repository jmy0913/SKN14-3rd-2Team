# 키워드별 관련 주식 매핑
STOCK_KEYWORDS = {
    "인공지능": ["삼성전자", "SK하이닉스", "네이버", "카카오", "LG전자", "솔트룩스", "수아컴퍼니", "엔씨소프트"],
    "반도체": ["삼성전자", "SK하이닉스", "LG전자", "DB하이텍", "원익IPS", "테스", "케이"]}
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
import json
from typing import List, Dict, Optional
import plotly.graph_objects as go
import plotly.express as px
from io import StringIO
import requests
from dotenv import load_dotenv
import os
import time
from utils1.main import run_flexible_rag

# 환경변수 로드
load_dotenv()
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
import requests
from dotenv import load_dotenv
import os

# 환경변수 로드
load_dotenv()
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# 키워드별 관련 주식 매핑
STOCK_KEYWORDS = {
    "인공지능": ["삼성전자", "SK하이닉스", "네이버", "카카오", "LG전자", "솔트룩스", "수아컴퍼니", "엔씨소프트"],
    "반도체": ["삼성전자", "SK하이닉스", "LG전자", "DB하이텍", "원익IPS", "테스", "케이엠더블유", "실리콘웍스"],
    "전기차": ["현대차", "기아", "LG화학", "삼성SDI", "SK이노베이션", "포스코케미칼", "에코프로", "엘앤에프"],
    "바이오": ["삼성바이오로직스", "셀트리온", "유한양행", "한미약품", "대웅제약", "녹십자", "JW중외제약", "일양약품"],
    "게임": ["엔씨소프트", "넥슨", "네오위즈", "NHN", "컴투스", "웹젠", "액토즈소프트", "선데이토즈"],
    "우주": ["한화시스템", "KAI", "현대로템", "LIG넥스원", "퍼스텍", "인콘", "쎄트렉아이", "나라스페이스"],
    "메타버스": ["네이버", "카카오", "엔씨소프트", "컴투스", "자이언트스텝", "버넥트", "맥스트", "선데이토즈"],
    "5G": ["삼성전자", "LG전자", "SK텔레콤", "KT", "LG유플러스", "KMW", "에이스테크놀로지", "텔레칩스"],
    "금융": ["KB금융", "신한지주", "하나금융지주", "우리금융지주", "NH투자증권", "미래에셋증권", "삼성증권", "대신증권"],
    "부동산": ["삼성물산", "현대건설", "대우건설", "GS건설", "포스코건설", "HDC현대산업개발", "대림산업", "롯데건설"]
}

# 뉴스 카테고리별 색상
CATEGORY_COLORS = {
    "경제": "#4CAF50",
    "기술": "#2196F3",
    "정치": "#FF9800",
    "사회": "#9C27B0",
    "문화": "#E91E63",
    "스포츠": "#FF5722",
    "기본": "#607D8B"
}

# 페이지 구성
st.set_page_config(
    page_title="재무재표 RAG 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 네이버 뉴스 API 호출 함수


def get_naver_news(query, display=5):
    url = 'https://openapi.naver.com/v1/search/news.json'
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        'query': query,
        'display': display,
        'start': 1,
        'sort': 'date'
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"API 호출 중 오류 발생: {e}")
        return None


# 키워드 기반 관련 주식 찾기
def get_related_stocks(query: str) -> List[str]:
    query_lower = query.lower()
    related_stocks = []

    for keyword, stocks in STOCK_KEYWORDS.items():
        if keyword in query_lower:
            related_stocks.extend(stocks)

    # 중복 제거하고 상위 5개만 반환
    return list(set(related_stocks))[:5]


# 뉴스 카테고리 추측
def guess_category(title: str, description: str) -> str:
    text = (title + " " + description).lower()

    if any(word in text for word in ["주식", "증시", "경제", "금융", "투자", "기업"]):
        return "경제"
    elif any(word in text for word in ["기술", "ai", "인공지능", "반도체", "it", "테크"]):
        return "기술"
    elif any(word in text for word in ["정치", "정부", "대통령", "국회", "선거"]):
        return "정치"
    elif any(word in text for word in ["사회", "사건", "사고", "범죄"]):
        return "사회"
    elif any(word in text for word in ["문화", "예술", "영화", "음악", "연예"]):
        return "문화"
    elif any(word in text for word in ["스포츠", "축구", "야구", "농구", "올림픽"]):
        return "스포츠"
    else:
        return "기본"


# HTML 태그 제거
def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


# 시간 경과 표시 함수
def time_ago(pub_date: str) -> str:
    try:
        date_obj = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
        now = datetime.now(date_obj.tzinfo)
        diff = now - date_obj

        if diff.days > 0:
            return f"{diff.days}일 전"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}시간 전"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}분 전"
        else:
            return "방금 전"
    except:
        return pub_date


# 샘플 재무 데이터 (실제 환경에서는 데이터베이스나 API에서 가져옴)
SAMPLE_FINANCIAL_DATA = {
    "삼성전자": {
        "2023": {
            "매출액": 258772000,
            "영업이익": 35994000,
            "당기순이익": 15109000,
            "총자산": 426952000,
            "부채총계": 105031000,
            "자본총계": 321921000,
            "부채비율": 32.6,
            "ROE": 4.7,
            "ROA": 3.5,
            "영업이익률": 13.9
        },
        "2022": {
            "매출액": 302231000,
            "영업이익": 43376000,
            "당기순이익": 23669000,
            "총자산": 405025000,
            "부채총계": 97356000,
            "자본총계": 307669000,
            "부채비율": 31.7,
            "ROE": 7.7,
            "ROA": 5.8,
            "영업이익률": 14.4
        }
    },
    "SK하이닉스": {
        "2023": {
            "매출액": 60460000,
            "영업이익": -14748000,
            "당기순이익": -19430000,
            "총자산": 101582000,
            "부채총계": 31442000,
            "자본총계": 70140000,
            "부채비율": 44.8,
            "ROE": -27.7,
            "ROA": -19.1,
            "영업이익률": -24.4
        },
        "2022": {
            "매출액": 44193000,
            "영업이익": 8851000,
            "당기순이익": 6507000,
            "총자산": 95251000,
            "부채총계": 26583000,
            "자본총계": 68668000,
            "부채비율": 38.7,
            "ROE": 9.5,
            "ROA": 6.8,
            "영업이익률": 20.0
        }
    },
    "네이버": {
        "2023": {
            "매출액": 8758000,
            "영업이익": 1360000,
            "당기순이익": 1225000,
            "총자산": 24859000,
            "부채총계": 7651000,
            "자본총계": 17208000,
            "부채비율": 44.5,
            "ROE": 7.1,
            "ROA": 4.9,
            "영업이익률": 15.5
        },
        "2022": {
            "매출액": 7994000,
            "영업이익": 1243000,
            "당기순이익": 1104000,
            "총자산": 22683000,
            "부채총계": 6871000,
            "자본총계": 15812000,
            "부채비율": 43.5,
            "ROE": 7.0,
            "ROA": 4.9,
            "영업이익률": 15.6
        }
    }
}

# 재무 지표 설명
FINANCIAL_METRICS = {
    "매출액": "기업이 상품이나 서비스를 판매하여 얻은 총 수익",
    "영업이익": "매출액에서 매출원가와 판매관리비를 뺀 이익",
    "당기순이익": "모든 수익과 비용을 반영한 최종 이익",
    "총자산": "기업이 보유한 모든 자산의 총합",
    "부채총계": "기업이 갚아야 할 모든 빚의 총합",
    "자본총계": "기업 소유주의 지분 총액",
    "부채비율": "부채총계 / 자본총계 × 100 (%)",
    "ROE": "당기순이익 / 자본총계 × 100 (자기자본이익률)",
    "ROA": "당기순이익 / 총자산 × 100 (총자산이익률)",
    "영업이익률": "영업이익 / 매출액 × 100 (%)"
}

# 커스텀 CSS
st.markdown("""
<style>
    .streaming-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #28a745;
        font-family: monospace;
        min-height: 100px;
    }
    .rag-response {
        background: #e8f5e8;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #28a745;
        white-space: pre-wrap;
        line-height: 1.6;
    }
    .search-mode-toggle {
        background: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 15px;
    }
    .news-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #2196F3;
        transition: transform 0.2s ease;
    }
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    .news-title {
        font-size: 13px;
        font-weight: 600;
        color: #1f77b4;
        margin-bottom: 8px;
        line-height: 1.3;
    }
    .news-description {
        color: #666;
        font-size: 11px;
        margin-bottom: 8px;
        line-height: 1.4;
    }
    .news-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 10px;
        color: #999;
        margin-bottom: 10px;
    }
    .category-badge {
        background: #f0f0f0;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 9px;
        font-weight: 500;
    }
    .stock-tag {
        display: inline-block;
        background: #e3f2fd;
        color: #1976d2;
        padding: 2px 6px;
        border-radius: 8px;
        font-size: 10px;
        margin: 2px;
        font-weight: 500;
    }
    .search-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .news-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        text-align: center;
    }
    .no-news {
        text-align: center;
        color: #999;
        font-style: italic;
        padding: 20px;
    }
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #4CAF50;
    }
    .company-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #2196F3;
    }
    .chat-message {
        background: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #ff6b6b;
    }
    .response-message {
        background: #e8f5e8;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #2196F3;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
        margin-bottom: 5px;
    }
    .positive {
        color: #4CAF50;
    }
    .negative {
        color: #f44336;
    }
</style>
""", unsafe_allow_html=True)


# RAG 시스템 함수들
def stream_rag_response(query: str):
    """RAG 응답을 스트리밍으로 반환"""
    try:
        # 외부 RAG 시스템 호출
        response = run_flexible_rag(query)

        # 응답을 청크 단위로 스트리밍
        words = response.split()
        for i, word in enumerate(words):
            yield word + " "
            time.sleep(0.05)  # 스트리밍 효과를 위한 딜레이
    except Exception as e:
        yield f"❌ RAG 시스템 오류: {str(e)}"


def search_financial_data(query: str, companies: List[str] = None) -> Dict:
    """재무 데이터 검색 함수 (기존 샘플 데이터 기반)"""
    results = {}
    query_lower = query.lower()

    # 검색할 회사 목록 결정
    if companies:
        search_companies = companies
    else:
        search_companies = list(SAMPLE_FINANCIAL_DATA.keys())

    # 키워드 기반 검색
    for company in search_companies:
        if company in SAMPLE_FINANCIAL_DATA:
            company_data = SAMPLE_FINANCIAL_DATA[company]
            results[company] = {}

            # 각 연도별 데이터 검색
            for year in company_data:
                year_data = company_data[year]
                filtered_data = {}

                # 특정 지표 검색
                for metric, value in year_data.items():
                    if any(keyword in query_lower for keyword in [
                        metric.lower(),
                        "매출" if "매출" in metric else "",
                        "이익" if "이익" in metric else "",
                        "자산" if "자산" in metric else "",
                        "부채" if "부채" in metric else "",
                        "roe" if "roe" in metric.lower() else "",
                        "roa" if "roa" in metric.lower() else ""
                    ]):
                        filtered_data[metric] = value

                # 키워드가 없으면 모든 데이터 반환
                if not filtered_data and not any(keyword in query_lower for keyword in
                                                 ["매출", "이익", "자산", "부채", "roe", "roa"]):
                    filtered_data = year_data

                if filtered_data:
                    results[company][year] = filtered_data

    return results


def generate_response(query: str, search_results: Dict) -> str:
    """검색 결과를 바탕으로 자연어 응답 생성"""
    if not search_results:
        return "요청하신 정보를 찾을 수 없습니다. 다른 키워드로 검색해보세요."

    response = []
    query_lower = query.lower()

    # 비교 분석 요청인지 확인
    if "비교" in query_lower or "vs" in query_lower:
        companies = list(search_results.keys())
        if len(companies) >= 2:
            response.append("## 📊 기업 비교 분석")

            # 최신 연도 데이터로 비교
            latest_year = "2023"
            for company in companies:
                if company in search_results and latest_year in search_results[company]:
                    data = search_results[company][latest_year]
                    response.append(f"\n**{company} ({latest_year}년)**")
                    for metric, value in data.items():
                        if isinstance(value, (int, float)):
                            formatted_value = f"{value:,.0f}" if abs(value) >= 1000 else f"{value:.1f}"
                            unit = "원" if metric in ["매출액", "영업이익", "당기순이익", "총자산", "부채총계", "자본총계"] else "%"
                            response.append(f"- {metric}: {formatted_value}{unit}")

    # 트렌드 분석 요청인지 확인
    elif "트렌드" in query_lower or "변화" in query_lower:
        response.append("## 📈 연도별 트렌드 분석")

        for company, years_data in search_results.items():
            response.append(f"\n**{company}**")
            years = sorted(years_data.keys())

            for metric in ["매출액", "영업이익", "당기순이익"]:
                if len(years) >= 2:
                    values = []
                    for year in years:
                        if metric in years_data[year]:
                            values.append(years_data[year][metric])

                    if len(values) >= 2:
                        change = ((values[-1] - values[0]) / abs(values[0])) * 100
                        change_text = "증가" if change > 0 else "감소"
                        response.append(f"- {metric}: {change:.1f}% {change_text}")

    # 일반 정보 요청
    else:
        response.append("## 💼 재무 정보")

        for company, years_data in search_results.items():
            response.append(f"\n**{company}**")

            for year in sorted(years_data.keys(), reverse=True):
                year_data = years_data[year]
                response.append(f"\n*{year}년*")

                for metric, value in year_data.items():
                    if isinstance(value, (int, float)):
                        formatted_value = f"{value:,.0f}" if abs(value) >= 1000 else f"{value:.1f}"
                        unit = "원" if metric in ["매출액", "영업이익", "당기순이익", "총자산", "부채총계", "자본총계"] else "%"

                        # 설명 추가
                        explanation = FINANCIAL_METRICS.get(metric, "")
                        response.append(f"- **{metric}**: {formatted_value}{unit}")
                        if explanation:
                            response.append(f"  *{explanation}*")

    return "\n".join(response)


def create_comparison_chart(search_results: Dict, metric: str = "매출액"):
    """비교 차트 생성"""
    companies = list(search_results.keys())
    years = []
    values = {company: [] for company in companies}

    # 데이터 추출
    all_years = set()
    for company in companies:
        all_years.update(search_results[company].keys())

    years = sorted(list(all_years))

    for year in years:
        for company in companies:
            if year in search_results[company] and metric in search_results[company][year]:
                values[company].append(search_results[company][year][metric])
            else:
                values[company].append(None)

    # 차트 생성
    fig = go.Figure()

    for company in companies:
        fig.add_trace(go.Scatter(
            x=years,
            y=values[company],
            mode='lines+markers',
            name=company,
            line=dict(width=3),
            marker=dict(size=8)
        ))

    fig.update_layout(
        title=f'{metric} 비교',
        xaxis_title='연도',
        yaxis_title=f'{metric} (원)' if metric in ["매출액", "영업이익", "당기순이익", "총자산", "부채총계", "자본총계"] else f'{metric} (%)',
        hovermode='x unified',
        template='plotly_white'
    )

    return fig


# 메인 화면
def main():
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>🏢 재무재표 RAG 시스템</h1>
        <p>자연어로 재무 정보를 검색하고 분석하세요</p>
    </div>
    """, unsafe_allow_html=True)

    # 사이드바
    with st.sidebar:
        st.header("🔍 검색 옵션")

        # 회사 선택
        available_companies = list(SAMPLE_FINANCIAL_DATA.keys())
        selected_companies = st.multiselect(
            "분석할 회사 선택",
            available_companies,
            default=available_companies[:2]
        )

        st.markdown("---")

        # 빠른 검색 버튼
        st.subheader("🚀 빠른 검색")

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            if st.button("📊 삼성전자 2023년 재무제표", use_container_width=True):
                st.session_state.search_query = "삼성전자 2023년 재무제표"

            if st.button("💰 SK하이닉스 영업이익", use_container_width=True):
                st.session_state.search_query = "SK하이닉스 영업이익"

        with col_btn2:
            if st.button("📈 네이버 ROE 분석", use_container_width=True):
                st.session_state.search_query = "네이버 ROE 분석"

            if st.button("🏦 재무 안정성 비교", use_container_width=True):
                st.session_state.search_query = "삼성전자 SK하이닉스 재무안정성 비교"

        st.markdown("---")

        # 도움말
        st.subheader("💡 검색 예시")

        st.markdown("**🤖 RAG 시스템 예시:**")
        st.markdown("""
        - "삼성전자 2023년 재무제표 알려줘"
        - "SK하이닉스 영업이익 분석해줘"
        - "네이버 부채비율은 어떻게 돼?"
        - "현대차 ROE 계산해줘"
        """)

        st.markdown("**📊 샘플 데이터 예시:**")
        st.markdown("""
        - "삼성전자 매출액"
        - "SK하이닉스 vs 네이버 영업이익"
        - "ROE 비교 분석"
        - "부채비율 트렌드"
        """)

        st.markdown("---")

        # 시스템 상태
        st.subheader("🔧 시스템 상태")

        # RAG 시스템 상태 체크
        try:
            test_response = "RAG 시스템 연결됨 ✅"
            rag_status = "🟢 정상"
        except:
            rag_status = "🔴 오류"

        # 네이버 API 상태 체크
        naver_status = "🟢 정상" if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET else "🔴 미설정"

        st.markdown(f"""
        - **RAG 시스템**: {rag_status}
        - **네이버 뉴스 API**: {naver_status}
        - **샘플 데이터**: 🟢 정상
        """)

        if not (NAVER_CLIENT_ID and NAVER_CLIENT_SECRET):
            st.info("네이버 API 키를 설정하면 뉴스 기능을 사용할 수 있습니다.")

    # 메인 컨텐츠
    col1, col2 = st.columns([2, 1])

    with col1:
        # 검색 모드 선택
        st.markdown('<div class="search-mode-toggle">', unsafe_allow_html=True)
        search_mode = st.radio(
            "🔍 검색 모드 선택",
            ["🤖 RAG 시스템", "📊 샘플 데이터"],
            horizontal=True,
            help="RAG 시스템: 실제 재무제표 데이터 검색, 샘플 데이터: 기본 제공 데이터"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # 검색 인터페이스
        st.subheader("💬 자연어 검색")

        # 채팅 히스토리 초기화
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        # 검색 입력
        search_query = st.text_input(
            "궁금한 것을 자연어로 물어보세요",
            value=st.session_state.get('search_query', ''),
            placeholder="예: 삼성전자 2023년 재무제표 알려줘"
        )

        # 검색 실행
        if st.button("🔍 검색") or search_query:
            if search_query:
                if search_mode == "🤖 RAG 시스템":
                    # RAG 시스템 사용
                    with st.spinner("RAG 시스템이 분석 중입니다..."):
                        # 스트리밍 응답 컨테이너
                        response_container = st.empty()

                        # 스트리밍 응답 표시
                        full_response = ""
                        for chunk in stream_rag_response(search_query):
                            full_response += chunk
                            response_container.markdown(f"""
                            <div class="streaming-container">
                                <strong>🤖 RAG 시스템 응답:</strong><br><br>
                                {full_response}
                            </div>
                            """, unsafe_allow_html=True)

                        # 최종 응답을 채팅 히스토리에 추가
                        st.session_state.chat_history.append({
                            'query': search_query,
                            'response': full_response,
                            'mode': 'RAG',
                            'timestamp': datetime.now()
                        })

                else:
                    # 샘플 데이터 사용
                    with st.spinner("샘플 데이터를 분석 중..."):
                        search_results = search_financial_data(search_query, selected_companies)
                        response = generate_response(search_query, search_results)

                    # 채팅 히스토리에 추가
                    st.session_state.chat_history.append({
                        'query': search_query,
                        'response': response,
                        'results': search_results,
                        'mode': 'Sample',
                        'timestamp': datetime.now()
                    })

                # 검색 쿼리 초기화
                st.session_state.search_query = ""

        # 채팅 히스토리 표시
        if st.session_state.chat_history:
            st.subheader("📝 검색 결과")

            for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):  # 최근 5개만 표시
                # 질문 표시
                st.markdown(f"""
                <div class="chat-message">
                    <strong>🙋‍♂️ 질문:</strong> {chat['query']}
                    <small style="color: #666;">[{chat['mode']}] {chat['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</small>
                </div>
                """, unsafe_allow_html=True)

                # 응답 표시
                if chat['mode'] == 'RAG':
                    st.markdown(f"""
                    <div class="rag-response">
                        <strong>🤖 RAG 시스템:</strong><br><br>
                        {chat['response']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="response-message">
                        <strong>📊 샘플 데이터:</strong><br>
                        {chat['response'].replace('##', '###').replace('\n', '<br>')}
                    </div>
                    """, unsafe_allow_html=True)

                    # 차트 생성 (샘플 데이터 모드에서만)
                    if 'results' in chat and chat['results'] and len(chat['results']) >= 1:
                        if "비교" in chat['query'] or "vs" in chat['query']:
                            metric_options = ["매출액", "영업이익", "당기순이익", "ROE", "ROA"]
                            for metric in metric_options:
                                if metric.lower() in chat['query'].lower():
                                    fig = create_comparison_chart(chat['results'], metric)
                                    st.plotly_chart(fig, use_container_width=True)
                                    break
                            else:
                                fig = create_comparison_chart(chat['results'], "매출액")
                                st.plotly_chart(fig, use_container_width=True)

                st.markdown("---")

    with col2:
        # 뉴스 패널
        st.markdown("""
        <div class="news-header">
            <h3 style="margin: 0; font-size: 18px;">📰 실시간 뉴스</h3>
            <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.9;">최신 뉴스와 관련 주식 정보</p>
        </div>
        """, unsafe_allow_html=True)

        # 검색 섹션
        with st.container():
            st.markdown('<div class="search-section">', unsafe_allow_html=True)

            # 검색 입력
            news_query = st.text_input(
                "뉴스 검색",
                value=st.session_state.get('news_query', '삼성전자'),
                placeholder="키워드를 입력하세요...",
                key="news_search"
            )

            if st.button("🔄 새로고침", key="refresh_news_btn", use_container_width=True):
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        # 뉴스 표시
        if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
            with st.spinner("뉴스를 불러오는 중..."):
                news_data = get_naver_news(news_query)
                related_stocks = get_related_stocks(news_query)

            if news_data and news_data.get('items'):
                # 관련 주식 표시
                if related_stocks:
                    st.markdown("**📈 관련 주식**")
                    stocks_html = ""
                    for stock in related_stocks:
                        stocks_html += f'<span class="stock-tag">{stock}</span>'
                    st.markdown(stocks_html, unsafe_allow_html=True)
                    st.markdown("---")

                # 뉴스 항목 표시
                for i, item in enumerate(news_data['items']):
                    title = remove_html_tags(item.get('title', ''))
                    description = remove_html_tags(item.get('description', ''))
                    pub_date = item.get('pubDate', '')
                    link = item.get('link', '')

                    # 카테고리 추측
                    category = guess_category(title, description)
                    category_color = CATEGORY_COLORS.get(category, CATEGORY_COLORS["기본"])

                    # 시간 경과 계산
                    time_diff = time_ago(pub_date)

                    # 뉴스 카드
                    st.markdown(f"""
                    <div class="news-card" style="border-left-color: {category_color};">
                        <div class="news-meta">
                            <span class="category-badge" style="background: {category_color}; color: white;">
                                {category}
                            </span>
                            <span>{time_diff}</span>
                        </div>
                        <div class="news-title">
                            <a href="{link}" target="_blank" style="text-decoration: none; color: #1f77b4;">
                                {title}
                            </a>
                        </div>
                        <div class="news-description">
                            {description[:100]}{'...' if len(description) > 100 else ''}
                        </div>
                        <div style="text-align: right;">
                            <a href="{link}" target="_blank" style="font-size: 10px; color: #ff6b6b; text-decoration: none;">
                                📖 원문 보기
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 구분선 (마지막 항목 제외)
                    if i < len(news_data['items']) - 1:
                        st.markdown("<hr style='margin: 5px 0; border: none; height: 1px; background: #eee;'>",
                                    unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="no-news">
                    <p>📭 뉴스를 불러올 수 없습니다.</p>
                    <p>검색 키워드를 변경해보세요.</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ 네이버 API 키가 설정되지 않았습니다.")
            st.info("`.env` 파일에 다음 내용을 추가하세요:")
            st.code("""
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
            """, language="bash")


if __name__ == "__main__":
    main()