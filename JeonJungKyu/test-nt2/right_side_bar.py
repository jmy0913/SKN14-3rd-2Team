import streamlit as st
import requests
from dotenv import load_dotenv
import os
from datetime import datetime
import re
import json
from typing import List, Dict

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


# 네이버 뉴스 API 호출 함수
def get_naver_news(query, display=10):
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


# 페이지 구성
st.set_page_config(
    page_title="뉴스 패널",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 커스텀 CSS
st.markdown("""
<style>
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
        font-size: 14px;
        font-weight: 600;
        color: #1f77b4;
        margin-bottom: 8px;
        line-height: 1.3;
    }
    .news-description {
        color: #666;
        font-size: 12px;
        margin-bottom: 8px;
        line-height: 1.4;
    }
    .news-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
        color: #999;
        margin-bottom: 10px;
    }
    .category-badge {
        background: #f0f0f0;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 10px;
        font-weight: 500;
    }
    .stock-section {
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid #eee;
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
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .main-content {
        background: #ffffff;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .news-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    .refresh-btn {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 20px;
        cursor: pointer;
        font-size: 12px;
        transition: all 0.3s ease;
    }
    .no-news {
        text-align: center;
        color: #999;
        font-style: italic;
        padding: 40px 20px;
    }
</style>
""", unsafe_allow_html=True)

# 컬럼 구성 (왼쪽: 65%, 오른쪽: 35%)
col_main, col_news = st.columns([70, 30])


# 오른쪽: 뉴스 사이드 영역
with col_news:
    st.markdown("""
    <div class="news-header">
        <h2 style="margin: 0; font-size: 20px;">📰 실시간 뉴스</h2>
        <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">최신 뉴스와 관련 주식 정보</p>
    </div>
    """, unsafe_allow_html=True)

    # 검색 섹션
    with st.container():
        st.markdown('<div class="search-section">', unsafe_allow_html=True)

        # 예시 키워드 버튼
        st.markdown("**🔥 인기 키워드**")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("삼성전자 뉴스", key="ai_btn"):
                st.session_state.search_query = "삼성전자 뉴스"
        with col2:
            if st.button("삼성전자 주식", key="stock_btn"):
                st.session_state.search_query = "삼성전자 주식"
        with col3:
            if st.button("SK하이닉스", key="ev_btn"):
                st.session_state.search_query = "SK하이닉스"

        # 검색 입력
        search_query = st.text_input(
            "검색 키워드",
            value=st.session_state.get('search_query', '삼성전자'),
            placeholder="키워드를 입력하세요..."
        )

        col_refresh, col_count = st.columns([1, 1])
        with col_refresh:
            if st.button("🔄 새로고침", key="refresh_btn"):
                st.rerun()


        st.markdown('</div>', unsafe_allow_html=True)

    # 뉴스 표시
    if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
        with st.spinner("뉴스를 불러오는 중..."):
            news_data = get_naver_news(search_query)
            related_stocks = get_related_stocks(search_query)

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
                        {description[:120]}{'...' if len(description) > 120 else ''}
                    </div>
                    <div style="text-align: right;">
                        <a href="{link}" target="_blank" style="font-size: 11px; color: #ff6b6b; text-decoration: none;">
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

