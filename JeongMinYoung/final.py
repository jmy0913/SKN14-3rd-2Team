import streamlit as st
from datetime import datetime
import time
from utils1.main import run_flexible_rag
import requests
import os
from dotenv import load_dotenv
import re
from typing import List

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

# 채팅 히스토리 초기화
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# RAG 시스템 응답을 스트리밍으로 반환
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

# 뉴스 API 호출
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

# 관련 주식 찾기
def get_related_stocks(query: str) -> List[str]:
    query_lower = query.lower()
    related_stocks = []

    for keyword, stocks in STOCK_KEYWORDS.items():
        if keyword in query_lower:
            related_stocks.extend(stocks)

    # 중복 제거하고 상위 5개만 반환
    return list(set(related_stocks))[:5]

# 메인 화면
def main():
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>🏢 재무재표 RAG 시스템</h1>
        <p>자연어로 재무 정보를 검색하고 분석하세요</p>
    </div>
    """, unsafe_allow_html=True)

    # 검색 입력
    st.subheader("💬 자연어 검색")

    # 검색 인터페이스
    search_query = st.text_input(
        "궁금한 것을 자연어로 물어보세요",
        value=st.session_state.get('search_query', ''),
        placeholder="예: 삼성전자 2023년 재무제표 알려줘"
    )

    # 검색 실행
    if st.button("🔍 검색") or search_query:
        if search_query:
            if 'search_query' not in st.session_state or st.session_state.search_query != search_query:
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

                # 검색 쿼리 초기화
                st.session_state.search_query = search_query
            else:
                st.warning("이미 분석된 검색어입니다. 새로고침 후 다시 시도하세요.")

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

    # 뉴스 패널
    st.markdown("""
    <div class="news-header">
        <h3 style="margin: 0; font-size: 18px;">📰 실시간 뉴스</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.9;">최신 뉴스와 관련 주식 정보</p>
    </div>
    """, unsafe_allow_html=True)

    # 뉴스 검색
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
                title = re.sub('<.*?>', '', item.get('title', ''))
                description = re.sub('<.*?>', '', item.get('description', ''))
                pub_date = item.get('pubDate', '')
                link = item.get('link', '')

                # 뉴스 카드
                st.markdown(f"""
                <div class="news-card" style="border-left-color: #2196F3;">
                    <div class="news-meta">
                        <span class="category-badge" style="background: #2196F3; color: white;">
                            경제
                        </span>
                        <span>{pub_date}</span>
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
