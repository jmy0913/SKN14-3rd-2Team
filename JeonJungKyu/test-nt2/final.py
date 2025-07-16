import streamlit as st
import sys
import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import re
from typing import List, Dict

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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

# Page configuration
st.set_page_config(
    page_title="재무 데이터 RAG 챗봇",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 통합 CSS (기존 + 뉴스 패널 스타일)
st.markdown("""
<style>
    /* 전체 레이아웃 */
    .main {
        height: 100vh;
        overflow: hidden;
        background-color: #f8f9fa;
    }
    .stApp {
        height: 100vh;
        overflow: hidden;
    }
    .block-container {
        height: 100vh;
        overflow: hidden;
        padding: 0;
        max-width: none;
    }

    /* 사이드바 스타일 */
    .sidebar {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
        padding: 1rem;
        height: 100vh;
        overflow-y: auto;
    }

    /* 메인 컨텐츠 영역 */
    .main-content {
        background-color: white;
        height: 100vh;
        display: flex;
        flex-direction: column;
        overflow-y: auto;
    }

    /* 상단 바 */
    .top-bar {
        padding: 1rem 2rem;
        border-bottom: 1px solid #e9ecef;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: white;
    }

    /* 채팅 컨테이너 */
    .chat-container {
        flex: 1;
        overflow-y: auto;
        padding: 2rem;
        background-color: white;
        max-height: calc(100vh - 200px);
    }

    /* 메시지 스타일 */
    .message {
        margin-bottom: 1rem;
        border-radius: 18px;
        max-width: 70%;
        word-wrap: break-word;
        position: relative;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .message.user {
        background: #007AFF;
        color: white;
        margin-left: auto;
        text-align: left;
        border-bottom-right-radius: 4px;
    }
    .message.assistant {
        background: #f1f3f4;
        color: #000;
        margin-right: auto;
        border-bottom-left-radius: 4px;
    }
    .message-time {
        font-size: 0.7rem;
        opacity: 0.6;
        margin-top: 0.25rem;
    }

    /* 대화 아이템 */
    .conversation-item {
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border-radius: 8px;
        background-color: transparent;
        cursor: pointer;
        transition: background-color 0.2s;
        border: none;
        text-align: left;
        width: 100%;
    }
    .conversation-item:hover {
        background-color: #e9ecef;
    }
    .conversation-item.active {
        background-color: #e8f0fe;
        color: #1a73e8;
    }

    /* 버튼 스타일 */
    .gemini-button {
        background-color: transparent;
        border: 1px solid #dadce0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        color: #5f6368;
        cursor: pointer;
        transition: all 0.2s;
        width: 100%;
        text-align: left;
        margin-bottom: 0.5rem;
    }
    .gemini-button:hover {
        background-color: #f8f9fa;
        border-color: #dadce0;
    }

    /* 입력 필드 */
    .chat-input {
        border: 1px solid #dadce0;
        border-radius: 24px;
        padding: 0.75rem 1rem;
        background-color: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* 웰컴 메시지 */
    .welcome-message {
        text-align: center;
        color: #5f6368;
        font-size: 1.1rem;
        margin-top: 2rem;
    }

    /* 뉴스 패널 스타일 */
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
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .news-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: center;
    }
    .no-news {
        text-align: center;
        color: #999;
        font-style: italic;
        padding: 40px 20px;
    }
</style>
""", unsafe_allow_html=True)


# 뉴스 관련 함수들
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


def get_related_stocks(query: str) -> List[str]:
    query_lower = query.lower()
    related_stocks = []

    for keyword, stocks in STOCK_KEYWORDS.items():
        if keyword in query_lower:
            related_stocks.extend(stocks)

    return list(set(related_stocks))[:5]


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


def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


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


# 간단한 RAG 응답 생성 함수 (오케스트레이터 대체)
def generate_response(user_input: str) -> str:
    """
    사용자 입력에 대한 간단한 응답을 생성합니다.
    실제 RAG 시스템 구현 시 이 함수를 대체하세요.
    """
    # 간단한 키워드 기반 응답
    user_input_lower = user_input.lower()

    if "삼성전자" in user_input_lower:
        return "삼성전자는 대한민국의 대표적인 반도체 및 전자제품 제조업체입니다. 메모리 반도체 분야에서 세계 1위를 차지하고 있으며, 스마트폰, 디스플레이 패널 등 다양한 전자제품을 생산하고 있습니다."

    elif "sk하이닉스" in user_input_lower:
        return "SK하이닉스는 메모리 반도체 전문 기업으로, DRAM과 NAND Flash 메모리 분야에서 세계적인 경쟁력을 보유하고 있습니다. 특히 모바일 DRAM과 서버용 메모리 시장에서 강세를 보이고 있습니다."

    elif "주식" in user_input_lower or "투자" in user_input_lower:
        return "주식 투자는 기업의 성장성과 재무 건전성을 종합적으로 분석한 후 결정하는 것이 중요합니다. 분산 투자를 통해 리스크를 관리하고, 장기적인 관점에서 접근하는 것을 권장합니다."

    elif "재무" in user_input_lower or "매출" in user_input_lower or "실적" in user_input_lower:
        return "기업의 재무 분석을 위해서는 매출액, 영업이익, 부채비율, ROE(자기자본이익률) 등의 지표를 종합적으로 살펴보는 것이 중요합니다. 또한 동종 업계 대비 성과도 비교해보시기 바랍니다."

    elif "안녕" in user_input_lower or "hello" in user_input_lower:
        return "안녕하세요! 한국 기업의 재무 정보에 대해 궁금한 점이 있으시면 언제든지 물어보세요. 삼성전자, SK하이닉스, LG전자 등 주요 기업들의 정보를 제공해드릴 수 있습니다."

    else:
        return f"'{user_input}'에 대한 질문을 받았습니다. 더 구체적인 정보를 원하시면 기업명이나 재무 관련 키워드를 포함해서 질문해주세요. 예를 들어, '삼성전자 재무 현황' 또는 'SK하이닉스 주가 전망' 등으로 질문하실 수 있습니다."


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "search_query" not in st.session_state:
    st.session_state.search_query = "삼성전자"


# 대화 관리 함수들
def generate_conversation_id():
    return f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def create_new_conversation():
    conv_id = generate_conversation_id()
    st.session_state.conversations[conv_id] = {
        "id": conv_id,
        "title": f"대화 {len(st.session_state.conversations) + 1}",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": []
    }
    st.session_state.current_conversation_id = conv_id
    st.session_state.messages = []
    return conv_id


def save_conversation(conv_id):
    if conv_id and conv_id in st.session_state.conversations:
        st.session_state.conversations[conv_id]["messages"] = st.session_state.messages.copy()
        st.session_state.conversations[conv_id]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_conversation(conv_id):
    if conv_id in st.session_state.conversations:
        st.session_state.current_conversation_id = conv_id
        st.session_state.messages = st.session_state.conversations[conv_id]["messages"].copy()


# 사이드바 (대화 관리)
with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0;">
        <h3 style="margin-bottom: 1rem; color: #5f6368;">재무 데이터 RAG</h3>
    </div>
    """, unsafe_allow_html=True)

    # 새 대화 생성 버튼
    if st.button("✏️ 새 채팅", use_container_width=True, key="new_chat"):
        create_new_conversation()
        st.rerun()

    st.markdown("---")

    # 저장된 대화 목록
    st.markdown("**최근**")

    if st.session_state.conversations:
        for conv_id, conv_data in st.session_state.conversations.items():
            is_active = conv_id == st.session_state.current_conversation_id

            if st.button(f"💬 {conv_data['title']}", key=f"conv_{conv_id}", help="대화 로드"):
                load_conversation(conv_id)
                st.rerun()
    else:
        st.markdown("저장된 대화가 없습니다.", help="새 대화를 시작해보세요")

    st.markdown("---")

    # 하단 정보
    st.markdown("""
    <div style="position: fixed; bottom: 1rem; left: 1rem; font-size: 0.8rem; color: #5f6368;">
        <div>대한민국 서울특별시</div>
        <div style="color: #1a73e8;">IP 주소 기반 • 위치 업데이트</div>
    </div>
    """, unsafe_allow_html=True)

# 메인 레이아웃 (채팅 + 뉴스)
col_chat, col_news = st.columns([70, 30])

# 왼쪽: 채팅 영역
with col_chat:
    # 상단 바
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown("### 재무 데이터 RAG 챗봇")
    with col2:
        st.markdown("")
    with col3:
        if st.button("업그레이드", key="upgrade"):
            st.info("업그레이드 기능 준비 중")

    st.markdown("---")

    # 채팅 메시지 표시
    with st.container(height=500):
        if not st.session_state.messages:
            # 웰컴 메시지
            st.markdown("""
            <div class="welcome-message">
                안녕하세요! 한국 기업의 재무 정보에 대해 질문해보세요.
            </div>
            """, unsafe_allow_html=True)
        else:
            # 채팅 메시지 표시
            for msg in st.session_state.messages:
                role_class = "user" if msg["role"] == "user" else "assistant"
                time_str = datetime.now().strftime("%H:%M")

                if msg["role"] == "user":
                    st.markdown(f"""
                    <div style="display: flex; justify-content: flex-end; margin-bottom: 10px; align-items: flex-end;">
                        <div class="message-time" style="color: #888888; font-size: 0.75rem; margin-right: 8px; margin-bottom: 5px;">{time_str}</div>
                        <div class="message {role_class}" style="max-width: 80%;">
                            <div style="background: #007AFF; padding: 10px 15px; border-radius: 30px; display: inline-block; color: white;">{msg["content"]}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="display: flex; justify-content: flex-start; margin-bottom: 10px; align-items: flex-end;">
                        <div class="message {role_class}" style="max-width: 80%;">
                            <div style="background: #f1f3f4; padding: 10px 15px; border-radius: 30px; display: inline-block; color: #000;">{msg["content"]}</div>
                        </div>
                        <div class="message-time" style="color: #888888; font-size: 0.75rem; margin-left: 8px; margin-bottom: 5px;">{time_str}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # 입력 영역
    user_input = st.chat_input("재무 데이터 RAG에게 물어보기")

    if user_input:
        # 새 대화가 없으면 자동 생성
        if not st.session_state.current_conversation_id:
            create_new_conversation()

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Generate response
        with st.spinner("답변 생성 중..."):
            try:
                bot_reply = generate_response(user_input)
            except Exception as e:
                bot_reply = f"죄송합니다. 오류가 발생했습니다: {str(e)}"

        # Add bot reply to chat history
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

        # 자동 저장
        if st.session_state.current_conversation_id:
            save_conversation(st.session_state.current_conversation_id)

        st.rerun()

# 오른쪽: 뉴스 패널
with col_news:
    st.markdown("""
    <div class="news-header">
        <h2 style="margin: 0; font-size: 20px;">📰 실시간 뉴스</h2>
        <p style="margin: 0px 0 0 0; font-size: 14px; opacity: 0.9;"></p>
    </div>
    """, unsafe_allow_html=True)

    # 검색 섹션
    with st.container():
        st.markdown('<div class="search-section">', unsafe_allow_html=True)

        # 검색 입력
        search_query = st.text_input(
            "검색 키워드",
            value=st.session_state.search_query,
            placeholder="키워드를 입력하세요...",
            label_visibility="collapsed"
        )

        if st.button("🔄 새로고침", key="refresh_btn", use_container_width=True):
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # 뉴스 표시
    if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
        with st.container(height=600):
            with st.spinner("뉴스를 불러오는 중..."):
                news_data = get_naver_news(search_query)
                related_stocks = get_related_stocks(search_query)

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