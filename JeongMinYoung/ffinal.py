import streamlit as st
import sys
import os
import json
import requests
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
from typing import List, Dict
import pandas as pd
from pykrx import stock
import yfinance as yf
import markdown

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# RAG 시스템 import (두 번째 파일의 RAG 시스템 사용)
from utils1.main import run_flexible_rag1
from utils1.main import run_flexible_rag2
from utils1.main import run_flexible_rag3


# 이미지를 base64로 인코딩하는 함수
def get_image_base64(image_path):
    """이미지 파일을 base64로 인코딩합니다."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return encoded_string
    except Exception as e:
        st.error(f"이미지 로드 오류: {e}")
        return ""


# 환경변수 로드
load_dotenv()
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

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

# 통합 CSS (첫 번째 파일의 UI 스타일 유지)
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
        margin: 0;
    }
    .block-container {
        overflow: hidden;
        padding: 1rem;
        padding-left: 4rem;
        padding-right: 4rem;
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
        display: flex;
        flex-direction: column;
        overflow-y: auto;
    }

    /* 컬럼 간격 개별 조정 */
    .stColumn {
        padding: 0;
    }

    /* 첫 번째 컬럼 (대화 관리) - 패딩 제거 */
    .stColumn:nth-child(1) {
        padding: 0 !important;
    }

    /* 두 번째 컬럼 (채팅) */
    .stColumn:nth-child(2) {
        padding-left: 8px;
        padding-right: 8px;
    }

    /* 세 번째 컬럼 (뉴스) */
    .stColumn:nth-child(3) {
        padding-left: 8px;
    }

    /* 특정 컬럼 클래스 패딩 제거 */
    .stColumn.st-emotion-cache-1t02cvl.eertqu01 {
        padding-top: 0 !important;
    }

    /* stVerticalBlock gap 제거 */
    .stVerticalBlock.st-emotion-cache-gsx7k2.eertqu03 {
        gap: 0 !important;
    }

    /* 뉴스 컨테이너 하단 여백 추가 */
    .st-emotion-cache-dim9q8.eertqu02 {
        margin-bottom: 15px !important;
    }

    /* Streamlit 컨테이너 높이 조정 */
    .st-emotion-cache-z4kicb {
        flex-direction: row;
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
        padding: 1rem;
        background-color: white;
        max-height: calc(100vh - 300px);
        scroll-behavior: smooth;
    }

    /* 채팅 메시지 컨테이너 */
    .chat-messages {
        display: flex;
        flex-direction: column;
        min-height: 100%;
    }

    /* 마지막 메시지에 여백 추가 */
    .chat-messages::after {
        content: '';
        height: 20px;
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

    /* 뉴스 패널 스타일 - 네이버 뉴스 스타일 */
    .news-card {
        background: white;
        padding: 12px 0;
        margin: 0;
        border-bottom: 1px solid #f1f3f4;
        transition: background-color 0.2s ease;
    }
    .news-card:hover {
        background-color: #f8f9fa;
    }
    .news-card:last-child {
        border-bottom: none;
    }
    .news-title {
        font-size: 13px;
        font-weight: 400;
        color: #202124;
        margin-bottom: 4px;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-decoration: none;
    }
    .news-title a {
        color: inherit;
        text-decoration: none;
    }
    .news-title:hover {
        text-decoration: underline;
    }
    .news-description {
        color: #5f6368;
        font-size: 12px;
        margin-bottom: 6px;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .news-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 11px;
        color: #5f6368;
        margin-bottom: 8px;
    }
    .news-source {
        color: #1a73e8;
        font-weight: 500;
    }
    .news-time {
        color: #5f6368;
    }
    .news-category {
        background: #e8f0fe;
        color: #1a73e8;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 500;
    }
    .search-section {
        background: white;
        padding: 12px;
        border-bottom: 1px solid #f1f3f4;
        margin-bottom: 8px;
    }
    .news-header {
        background: transparent;
        color: #333333;
        padding: 8px;
        border-radius: 8px;
        margin-bottom: 8px;
        text-align: center;
    }
    .no-news {
        text-align: center;
        color: #999;
        font-style: italic;
        padding: 60px 20px;
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border-radius: 16px;
        border: 2px dashed #e0e0e0;
    }
    .no-news p:first-child {
        font-size: 24px;
        margin-bottom: 8px;
    }
    .no-news p:last-child {
        font-size: 14px;
        color: #666;
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


# 주식 관련 함수들 (두 번째 파일에서 가져옴)
@st.cache_data
def get_krx_tickers():
    try:
        kospi = stock.get_market_ticker_list(market="KOSPI")
        kosdaq = stock.get_market_ticker_list(market="KOSDAQ")
        tickers = kospi + kosdaq

        name_code_map = {}
        for ticker in tickers:
            name = stock.get_market_ticker_name(ticker)
            name_code_map[name] = ticker

        return name_code_map
    except Exception as e:
        st.error(f"주식 데이터 로드 오류: {e}")
        return {}


def get_stock_data(company_name):
    """주식 데이터를 가져오는 함수"""
    try:
        name_to_code = get_krx_tickers()

        if not name_to_code:
            return {
                "success": False,
                "error": "주식 데이터베이스 연결에 실패했습니다."
            }

        if company_name in name_to_code:
            code = name_to_code[company_name]

            # 날짜 설정 (더 넉넉하게)
            today = datetime.today()
            two_months_ago = today - timedelta(days=60)

            # 먼저 pykrx로 시도
            try:
                stock_data = stock.get_market_ohlcv_by_date(
                    two_months_ago.strftime("%Y%m%d"),
                    today.strftime("%Y%m%d"),
                    code
                )

                if not stock_data.empty:
                    # 컬럼명을 영어로 변환
                    stock_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                    return {
                        "success": True,
                        "code": code,
                        "data": stock_data,
                        "source": "pykrx"
                    }
            except Exception as e:
                pass  # yfinance로 fallback

            # yfinance로 fallback
            try:
                # KOSPI는 .KS, KOSDAQ은 .KQ
                if code in stock.get_market_ticker_list(market="KOSPI"):
                    yahoo_code = f"{code}.KS"
                else:
                    yahoo_code = f"{code}.KQ"

                stock_data = yf.download(
                    yahoo_code,
                    start=two_months_ago.strftime("%Y-%m-%d"),
                    end=today.strftime("%Y-%m-%d"),
                    progress=False
                )

                if not stock_data.empty:
                    return {
                        "success": True,
                        "code": code,
                        "data": stock_data,
                        "source": "yfinance"
                    }
                else:
                    return {
                        "success": False,
                        "error": "해당 종목의 주가 데이터를 찾을 수 없습니다."
                    }

            except Exception as e:
                return {
                    "success": False,
                    "error": f"주가 데이터 조회 실패: {str(e)}"
                }
        else:
            # 유사한 기업명 찾기
            similar_names = [name for name in name_to_code.keys() if company_name in name]
            if similar_names:
                suggestions = ", ".join(similar_names[:3])
                return {
                    "success": False,
                    "error": f"정확한 기업명을 입력해주세요. 비슷한 기업: {suggestions}"
                }
            else:
                return {
                    "success": False,
                    "error": "해당 기업명은 상장기업이 아닙니다. 정확한 기업명을 입력해주세요."
                }
    except Exception as e:
        return {
            "success": False,
            "error": f"시스템 오류: {str(e)}"
        }


def guess_category(title: str, description: str) -> str:
    text = (title + " " + description).lower()

    if any(word in text for word in ["경제", "금융", "투자", "기업"]):
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


# RAG 응답 생성 함수 (두 번째 파일의 레벨별 RAG 시스템 사용)
def generate_response_stream(user_input: str):
    """
    RAG 시스템을 사용하여 사용자 입력에 대한 응답을 스트림으로 생성합니다.
    선택된 레벨에 따라 다른 RAG 함수를 호출합니다.
    """
    try:
        # 선택된 레벨에 따라 해당하는 RAG 함수 호출
        if st.session_state.selected_level == "초급":
            response = run_flexible_rag1(user_input)
        elif st.session_state.selected_level == "중급":
            response = run_flexible_rag2(user_input)
        elif st.session_state.selected_level == "고급":
            response = run_flexible_rag3(user_input)
        else:
            # 기본값은 초급
            response = run_flexible_rag1(user_input)

        # 응답을 단어 단위로 분할하여 스트리밍
        words = response.split()
        for word in words:
            yield word + " "
            import time
            time.sleep(0.1)  # 단어 간 딜레이 (0.1초)

    except Exception as e:
        # RAG 시스템 오류 시 fallback 응답
        st.error(f"RAG 시스템 오류: {str(e)}")
        fallback_response = generate_fallback_response(user_input)
        # fallback 응답을 단어 단위로 스트리밍
        words = fallback_response.split()
        for word in words:
            yield word + " "
            import time
            time.sleep(0.1)  # 단어 간 딜레이


def generate_fallback_response(user_input: str) -> str:
    """
    RAG 시스템 오류 시 사용할 fallback 응답을 생성합니다.
    """
    user_input_lower = user_input.lower()

    if "재무" in user_input_lower or "매출" in user_input_lower or "실적" in user_input_lower:
        return "죄송합니다. 현재 RAG 시스템에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
    elif "안녕" in user_input_lower or "hello" in user_input_lower:
        return "안녕하세요! 재무 데이터에 대해 궁금한 점이 있으시면 언제든지 물어보세요."
    else:
        return "죄송합니다. 현재 시스템에 문제가 발생하여 정확한 답변을 드릴 수 없습니다. 잠시 후 다시 시도해주세요."


# Initialize session state (두 번째 파일의 세션 상태 추가)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "search_query" not in st.session_state:
    st.session_state.search_query = "경제"
if "last_header_date" not in st.session_state:
    st.session_state.last_header_date = None
if "first_message_sent" not in st.session_state:
    st.session_state.first_message_sent = False
if "awaiting_response" not in st.session_state:
    st.session_state.awaiting_response = False
if "user_input_content" not in st.session_state:
    st.session_state.user_input_content = ""
if "selected_level" not in st.session_state:
    st.session_state.selected_level = "초급"
if "info_mode" not in st.session_state:
    st.session_state.info_mode = "뉴스"


# 대화 관리 함수들
def generate_conversation_id():
    return f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def create_new_conversation():
    conv_id = generate_conversation_id()
    now = datetime.now()
    st.session_state.conversations[conv_id] = {
        "id": conv_id,
        "title": f"{now.strftime('%Y/%m/%d')}\n{now.strftime('%p %I:%M').replace('AM', '오전').replace('PM', '오후')}",
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "messages": []
    }
    st.session_state.current_conversation_id = conv_id
    st.session_state.messages = []
    st.session_state.first_message_sent = False
    st.session_state.awaiting_response = False
    st.session_state.user_input_content = ""
    return conv_id


def save_conversation(conv_id):
    if conv_id and conv_id in st.session_state.conversations:
        st.session_state.conversations[conv_id]["messages"] = st.session_state.messages.copy()
        st.session_state.conversations[conv_id]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_conversation(conv_id):
    if conv_id in st.session_state.conversations:
        st.session_state.current_conversation_id = conv_id
        st.session_state.messages = st.session_state.conversations[conv_id]["messages"].copy()


def delete_conversation(conv_id):
    """대화를 삭제하는 함수"""
    if conv_id in st.session_state.conversations:
        del st.session_state.conversations[conv_id]

        # 삭제된 대화가 현재 활성 대화인 경우
        if st.session_state.current_conversation_id == conv_id:
            # 다른 대화가 있으면 첫 번째 대화로 전환, 없으면 초기화
            if st.session_state.conversations:
                first_conv_id = list(st.session_state.conversations.keys())[0]
                load_conversation(first_conv_id)
            else:
                st.session_state.current_conversation_id = None
                st.session_state.messages = []
                st.session_state.first_message_sent = False


# 툴바에 로고 추가 (첫 번째 파일 UI 유지)
try:
    logo_b64 = get_image_base64("icon/robot-icon.png")
    st.markdown(f"""
    <style>
    /* 기존 툴바 내용 숨기기 */
    .stAppToolbar {{
        background-color: white !important;
        border-bottom: 1px solid #e0e0e0 !important;
        padding: 8px 20px !important;
    }}

    /* Deploy 버튼과 메뉴 숨기기 */
    .stAppDeployButton,
    .stMainMenu {{
        display: none !important;
    }}

    /* 툴바 왼쪽에 로봇 아이콘 추가 (대화목록만큼 들여쓰기) */
    .stAppToolbar::before {{
        content: '';
        position: absolute;
        left: 52px;
        top: 50%;
        transform: translateY(-50%);
        width: 28px;
        height: 28px;
        background-image: url("data:image/png;base64,{logo_b64}");
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
    }}

    /* 툴바 왼쪽에 JemBot 텍스트 추가 */
    .stAppToolbar::after {{
        content: 'JemBot';
        position: absolute;
        left: 88px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 1.2rem;
        font-weight: 700;
        color: #333333;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}

    /* 툴바 높이 조정 */
    .stAppToolbar .st-emotion-cache-1j22a0y {{
        min-height: 48px !important;
    }}
    </style>
    """, unsafe_allow_html=True)
except Exception as e:
    # 이미지 로드 실패 시 이모지로 대체
    st.markdown("""
    <style>
    /* 기존 툴바 내용 숨기기 */
    .stAppToolbar {
        background-color: white !important;
        border-bottom: 1px solid #e0e0e0 !important;
        padding: 8px 20px !important;
    }

    /* Deploy 버튼과 메뉴 숨기기 */
    .stAppDeployButton,
    .stMainMenu {
        display: none !important;
    }

    /* 툴바 왼쪽에 로봇 이모지 추가 (대화목록만큼 들여쓰기) */
    .stAppToolbar::before {
        content: '🤖';
        position: absolute;
        left: 52px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 24px;
    }

    /* 툴바 왼쪽에 JemBot 텍스트 추가 */
    .stAppToolbar::after {
        content: 'JemBot';
        position: absolute;
        left: 88px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 1.2rem;
        font-weight: 700;
        color: #333333;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* 툴바 높이 조정 */
    .stAppToolbar .st-emotion-cache-1j22a0y {
        min-height: 48px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더 영역 (첫 번째 파일의 UI 구조 유지하되 주식 기능 추가)
col_space, col_chat_title, col_news_title = st.columns([15, 65, 20])

with col_space:
    # 대화목록 제목과 + 버튼을 로고 부분에 배치
    col_title, col_plus = st.columns([3, 1])

    with col_title:
        st.markdown("""
        <div style="margin-bottom: 0.5rem;">
            <h3 style="margin: 0; color: #333333; font-weight: 600; font-size: 1.1rem;">대화 목록</h3>
        </div>
        """, unsafe_allow_html=True)

    with col_plus:
        # + 버튼 CSS 스타일 (첫 번째 파일 스타일 유지)
        st.markdown("""
        <style>
        button[key="new_chat_plus_header"] {
            background-color: rgba(0, 51, 153, 0.2) !important;
            color: rgb(0, 51, 153) !important;
            border: 0px solid rgb(255, 75, 75) !important;
            border-radius: 50% !important;
            width: 32px !important;
            height: 32px !important;
            font-size: 18px !important;
            font-weight: bold !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 auto !important;
            padding: 0 !important;
            transition: all 0.2s ease !important;
            position: relative !important;
            z-index: 999 !important;
            line-height: 1 !important;
        }
        button[key="new_chat_plus_header"]:hover {
            background-color: rgba(0, 51, 153, 0.8) !important;
            color: white !important;
            transform: scale(1.1) !important;
            border: 0px solid rgb(255, 75, 75) !important;
        }
        button[key="new_chat_plus_header"]:active {
            background-color: rgb(0, 51, 153) !important;
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # 새 대화 생성 + 버튼
        if st.button("➕", key="new_chat_plus_header", help="새 채팅 시작", use_container_width=True):
            create_new_conversation()
            st.rerun()

with col_chat_title:
    # 레벨 선택 박스 CSS
    st.markdown("""
    <style>
    .level-selector-container {
        text-align: center;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    # 레벨 선택 박스 (컴팩트 버전)
    col_space1, col_btn, col_space2 = st.columns([1, 2, 1])

    with col_btn:
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("초급", key="level_beginner",
                         type="primary" if st.session_state.selected_level == "초급" else "secondary",
                         use_container_width=True):
                st.session_state.selected_level = "초급"
                st.rerun()

        with col2:
            if st.button("중급", key="level_intermediate",
                         type="primary" if st.session_state.selected_level == "중급" else "secondary",
                         use_container_width=True):
                st.session_state.selected_level = "중급"
                st.rerun()

        with col3:
            if st.button("고급", key="level_advanced",
                         type="primary" if st.session_state.selected_level == "고급" else "secondary",
                         use_container_width=True):
                st.session_state.selected_level = "고급"
                st.rerun()

    # 레벨 선택 버튼 스타일 커스터마이징 (첫 번째 파일 스타일 유지)
    st.markdown("""
    <style>
    /* 모든 레벨 버튼과 하위 요소들 - 더 강력한 선택자 */
    button[key="level_beginner"],
    button[key="level_intermediate"], 
    button[key="level_advanced"],
    button[data-testid="stBaseButton-primary"][key="level_beginner"],
    button[data-testid="stBaseButton-secondary"][key="level_beginner"],
    button[data-testid="stBaseButton-primary"][key="level_intermediate"],
    button[data-testid="stBaseButton-secondary"][key="level_intermediate"],
    button[data-testid="stBaseButton-primary"][key="level_advanced"],
    button[data-testid="stBaseButton-secondary"][key="level_advanced"],
    button[key="level_beginner"] *,
    button[key="level_intermediate"] *,
    button[key="level_advanced"] *,
    .st-emotion-cache-18wcnp {
        border-radius: 20px !important;
        border: 0px solid rgb(255, 75, 75) !important;
        box-shadow: none !important;
    }

    /* 버튼 기본 스타일 - 더 강력한 선택자 */
    button[key="level_beginner"], 
    button[key="level_intermediate"], 
    button[key="level_advanced"],
    button[data-testid="stBaseButton-primary"][key="level_beginner"],
    button[data-testid="stBaseButton-secondary"][key="level_beginner"],
    button[data-testid="stBaseButton-primary"][key="level_intermediate"],
    button[data-testid="stBaseButton-secondary"][key="level_intermediate"],
    button[data-testid="stBaseButton-primary"][key="level_advanced"],
    button[data-testid="stBaseButton-secondary"][key="level_advanced"],
    .st-emotion-cache-18wcnp,
    button.st-emotion-cache-1z0ldxb.e1e4lema2[key="level_intermediate"],
    button.st-emotion-cache-1z0ldxb.e1e4lema2[key="level_advanced"],
    .st-emotion-cache-1z0ldxb.e1e4lema2[key="level_intermediate"],
    .st-emotion-cache-1z0ldxb.e1e4lema2[key="level_advanced"] {
        font-weight: 500 !important;
        font-size: 12px !important;
        padding: 4px 12px !important;
        margin-bottom: 5px !important;
        transition: all 0.2s ease !important;
        height: 32px !important;
        background-color: rgba(0, 51, 153, 0.2) !important;
        color: rgb(0, 51, 153) !important;
        border: 0px solid rgb(255, 75, 75) !important;
        border-radius: 20px !important;
    }

    /* 활성 상태 스타일 변경 */
    button[key="level_beginner"][kind="primary"],
    button[key="level_intermediate"][kind="primary"],
    button[key="level_advanced"][kind="primary"],
    button[data-testid="stBaseButton-primary"][key="level_beginner"],
    button[data-testid="stBaseButton-primary"][key="level_intermediate"],
    button[data-testid="stBaseButton-primary"][key="level_advanced"],
    .st-emotion-cache-18wcnp:active,
    .st-emotion-cache-18wcnp.active,
    .st-emotion-cache-1z0ldxb.e1e4lema2[key="level_intermediate"]:active,
    .st-emotion-cache-1z0ldxb.e1e4lema2[key="level_advanced"]:active {
        background-color: rgb(0, 51, 153) !important;
        color: white !important;
    }

    /* 호버 효과 */
    button[key="level_beginner"]:hover,
    button[key="level_intermediate"]:hover,
    button[key="level_advanced"]:hover,
    button[data-testid="stBaseButton-primary"][key="level_beginner"]:hover,
    button[data-testid="stBaseButton-secondary"][key="level_beginner"]:hover,
    button[data-testid="stBaseButton-primary"][key="level_intermediate"]:hover,
    button[data-testid="stBaseButton-secondary"][key="level_intermediate"]:hover,
    button[data-testid="stBaseButton-primary"][key="level_advanced"]:hover,
    button[data-testid="stBaseButton-secondary"][key="level_advanced"]:hover,
    .st-emotion-cache-18wcnp:hover,
    .st-emotion-cache-1z0ldxb.e1e4lema2[key="level_intermediate"]:hover,
    .st-emotion-cache-1z0ldxb.e1e4lema2[key="level_advanced"]:hover {
        transform: scale(1.05) !important;
        background-color: rgba(0, 51, 153, 0.8) !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

with col_news_title:
    # 뉴스/주식 모드 선택 부분 추가
    col_mode1, col_mode2 = st.columns(2)

    with col_mode1:
        if st.button("📰 뉴스", key="mode_news",
                     type="primary" if st.session_state.info_mode == "뉴스" else "secondary",
                     use_container_width=True):
            st.session_state.info_mode = "뉴스"
            st.rerun()

    with col_mode2:
        if st.button("📈 주식", key="mode_stock",
                     type="primary" if st.session_state.info_mode == "주식" else "secondary",
                     use_container_width=True):
            st.session_state.info_mode = "주식"
            st.rerun()

    # 모드 버튼 스타일
    st.markdown("""
    <style>
    button[key="mode_news"], button[key="mode_stock"] {
        font-size: 11px !important;
        padding: 2px 6px !important;
        height: 28px !important;
        border-radius: 14px !important;
        border: none !important;
        margin-bottom: 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 메인 레이아웃 (대화 관리 + 채팅 + 뉴스/주식)
col_conv, col_chat, col_news = st.columns([15, 65, 20])

# 왼쪽: 대화 관리 영역 (첫 번째 파일 UI 유지)
with col_conv:
    # 구분선 (채팅창/뉴스창과 높이 맞춤)
    st.markdown("""
    <div style="border-bottom: 1px solid #e0e0e0; margin-bottom: 20px; padding-bottom: 20px;"></div>
    """, unsafe_allow_html=True)

    # 버튼 색상 고정 CSS
    st.markdown("""
    <style>
    /* 대화 버튼 - 흰색 배경 고정 */
    button[key^="conv_"],
    button[data-testid="stBaseButton-secondary"][key^="conv_"] {
        background: white !important;
        background-color: white !important;
        border: 1px solid #f1f3f4 !important;
        border-radius: 8px !important;
        padding: 12px !important;
        text-align: left !important;
        margin-bottom: 10px !important;
        color: #333 !important;
        font-size: 11px !important;
        white-space: pre-line !important;
        line-height: 1.4 !important;
    }

    button[key^="conv_"]:hover,
    button[data-testid="stBaseButton-secondary"][key^="conv_"]:hover {
        background: #f8f9fa !important;
        background-color: #f8f9fa !important;
        border-color: #e1e5e9 !important;
    }

    /* 휴지통 버튼 - 투명 배경 고정 */
    button[key^="delete_"],
    button[data-testid="stBaseButton-secondary"][key^="delete_"] {
        background: transparent !important;
        background-color: transparent !important;
        border: 1px solid #ddd !important;
        border-radius: 4px !important;
        width: 24px !important;
        height: 24px !important;
        padding: 4px !important;
        font-size: 12px !important;
        color: #666 !important;
    }

    button[key^="delete_"]:hover,
    button[data-testid="stBaseButton-secondary"][key^="delete_"]:hover {
        background: #ffebee !important;
        background-color: #ffebee !important;
        border-color: #dc3545 !important;
        color: #dc3545 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.session_state.conversations:
        for conv_id, conv_data in st.session_state.conversations.items():
            is_active = conv_id == st.session_state.current_conversation_id

            # 대화 버튼과 삭제 버튼을 나란히 배치
            col_conv_btn, col_delete_btn = st.columns([5, 1])

            with col_conv_btn:
                # 원래대로 텍스트만 사용
                if st.button(
                        conv_data['title'],
                        key=f"conv_{conv_id}",
                        help="대화 로드",
                        use_container_width=True
                ):
                    load_conversation(conv_id)
                    st.rerun()

            with col_delete_btn:
                # 휴지통 버튼
                if st.button("🗑️", key=f"delete_{conv_id}", help="대화 삭제"):
                    delete_conversation(conv_id)
                    st.rerun()

            # 활성 대화 스타일 동적 적용
            if is_active:
                st.markdown(f"""
                <style>
                button[key="conv_{conv_id}"] {{
                    background: #e8f0fe !important;
                    border-color: #1a73e8 !important;
                    color: #1a73e8 !important;
                }}
                </style>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; color: #9aa0a6; font-size: 13px; padding: 20px;">
            저장된 대화가 없습니다
        </div>
        """, unsafe_allow_html=True)

# 중앙: 채팅 영역
with col_chat:
    # 채팅 메시지 표시
    chat_container = st.container(height=450)

    with chat_container:
        # 채팅 메시지 컨테이너 시작
        st.markdown('<div class="chat-messages">', unsafe_allow_html=True)

        # JemBotMessage 표시 (첫 번째 메시지가 보내졌을 때만 표시)
        if st.session_state.first_message_sent:
            current_date = datetime.now().strftime('%Y-%m-%d')

            # 날짜가 바뀌었을 때 헤더 날짜 업데이트
            if st.session_state.last_header_date != current_date:
                st.session_state.last_header_date = current_date

            # 항상 헤더 표시 (같은 날에도 계속 표시)
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 15px; color: #666;">
                <div style="font-size: 14px; font-weight: 500;">JemBotMessage</div>
                <div style="font-size: 12px; margin-top: 2px;">Today {datetime.now().strftime('%H:%M')}</div>
            </div>
            """, unsafe_allow_html=True)

        # 웰컴 메시지는 첫 번째 메시지가 보내지지 않았을 때만 표시
        if not st.session_state.first_message_sent:
            st.markdown("""
            <div class="welcome-message">
                안녕하세요! RAG 시스템을 통해 재무 데이터에 대해 질문해보세요.<br>
                <small style="color: #888;">예: "삼성전자 2023년 재무제표 알려줘"</small>
            </div>
            """, unsafe_allow_html=True)

        # 채팅 메시지 표시 (레벨 정보 포함)
        for msg in st.session_state.messages:
            role_class = "user" if msg["role"] == "user" else "assistant"
            time_str = datetime.now().strftime("%H:%M")

            if msg["role"] == "user":
                st.markdown(f"""
                <div style="text-align: right; margin-bottom: 10px;">
                    <div style="display: inline-block; background: #007AFF; padding: 10px 15px; border-radius: 30px; color: white; max-width: 70%;">{msg["content"]}</div>
                    <span style="color: #888888; font-size: 0.75rem; margin-left: 4px; vertical-align: bottom;">{time_str}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                # AI 응답에 레벨 표시 추가
                level_colors = {
                    "초급": "#4CAF50",
                    "중급": "#2196F3",
                    "고급": "#FF9800"
                }
                msg_level = msg.get("level", st.session_state.selected_level)
                level_color = level_colors.get(msg_level, "#4CAF50")

                st.markdown(f"""
                <div style="text-align: left; margin-bottom: 3px;">
                    <span style="background-color: {level_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 500;">{msg_level}</span>
                </div>
                """, unsafe_allow_html=True)

                # 채팅 메시지 with 마크다운 렌더링
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])

                # 시간 표시
                st.markdown(f"""
                <div style="text-align: left;">
                    <span style="color: #888888; font-size: 0.75rem; margin-left: 4px;">{time_str}</span>
                </div>
                """, unsafe_allow_html=True)

        # 채팅 메시지 컨테이너 끝
        st.markdown('</div>', unsafe_allow_html=True)

        # 자동 스크롤 JavaScript
        if st.session_state.messages:
            st.markdown("""
            <script>
            // 페이지 로드 후 스크롤을 맨 아래로
            window.addEventListener('load', function() {
                const chatContainer = document.querySelector('.chat-container') || document.querySelector('[data-testid="stVerticalBlock"]');
                if (chatContainer) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            });

            // DOM 변경 감지하여 스크롤 자동 조정
            const observer = new MutationObserver(function() {
                const chatContainer = document.querySelector('.chat-container') || document.querySelector('[data-testid="stVerticalBlock"]');
                if (chatContainer) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            </script>
            """, unsafe_allow_html=True)

    # 입력 영역
    user_input = st.chat_input("재무 데이터 RAG에게 물어보기")

    if user_input:
        # 새 대화가 없으면 자동 생성
        if not st.session_state.current_conversation_id:
            create_new_conversation()

        # Add user message to chat history first (레벨 정보 포함)
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "level": st.session_state.selected_level
        })

        # 첫 번째 메시지 플래그 설정
        if len(st.session_state.messages) == 1:
            st.session_state.first_message_sent = True

        # 응답 대기 상태 설정
        st.session_state.awaiting_response = True
        st.session_state.user_input_content = user_input

        # 즉시 UI 업데이트를 위해 rerun
        st.rerun()

    # 응답 대기 중인 경우 챗봇 응답 생성
    if st.session_state.awaiting_response:

        # Generate response using RAG system (streaming)
        try:
            # 로딩 메시지를 채팅창 안에 글자 단위로 스트리밍
            loading_text = "RAG 시스템에서 답변을 생성하는 중... ⏳"

            with chat_container:
                loading_placeholder = st.empty()

                for i in range(len(loading_text)):
                    current_text = loading_text[:i + 1]
                    loading_placeholder.markdown(f"""
                    <div style="text-align: left; margin-bottom: 10px;">
                        <div style="display: inline-block; background: #f1f3f4; padding: 10px 15px; border-radius: 30px; color: #666; max-width: 70%;">{current_text}</div>
                        <span style="color: #888888; font-size: 0.75rem; margin-left: 4px; vertical-align: bottom;">{datetime.now().strftime('%H:%M')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    import time

                    time.sleep(0.05)  # 글자 간 딜레이

            # 스트림 응답을 받기 위한 placeholder (채팅창 안에서)
            with chat_container:
                response_placeholder = st.empty()
                full_response = ""

                # 스트림 방식으로 응답 생성
                for chunk in generate_response_stream(st.session_state.user_input_content):
                    full_response += chunk
                    # 로딩 메시지 제거하고 실시간으로 응답 업데이트
                    loading_placeholder.empty()

                    # 레벨 표시와 함께 응답 업데이트
                    level_colors = {
                        "초급": "#4CAF50",
                        "중급": "#2196F3",
                        "고급": "#FF9800"
                    }
                    current_level = st.session_state.selected_level
                    level_color = level_colors.get(current_level, "#4CAF50")


                    html_content = markdown.markdown(full_response)

                    response_placeholder.markdown(f"""
                    <div style="text-align: left; margin-bottom: 10px;">
                        <div style="margin-bottom: 3px;">
                            <span style="background-color: {level_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 500;">{current_level}</span>
                        </div>
                        <div style="display: inline-block; background: #f1f3f4; padding: 10px 15px; border-radius: 30px; color: #000; max-width: 70%;">{html_content}</div>
                        <span style="color: #888888; font-size: 0.75rem; margin-left: 4px; vertical-align: bottom;">{datetime.now().strftime('%H:%M')}</span>
                    </div>
                    """, unsafe_allow_html=True)

            # 스트림 완료 후 placeholder 제거
            response_placeholder.empty()
            loading_placeholder.empty()
            bot_reply = full_response

        except Exception as e:
            bot_reply = f"죄송합니다. RAG 시스템에서 오류가 발생했습니다: {str(e)}"
            st.error("RAG 시스템 연결에 문제가 있습니다. 시스템 관리자에게 문의하세요.")

        # Add bot reply to chat history (레벨 정보 포함)
        st.session_state.messages.append({
            "role": "assistant",
            "content": bot_reply,
            "level": st.session_state.selected_level
        })

        # 응답 완료 후 플래그 리셋
        st.session_state.awaiting_response = False
        st.session_state.user_input_content = ""

        # 자동 저장
        if st.session_state.current_conversation_id:
            save_conversation(st.session_state.current_conversation_id)

        # 답변 완료 후 페이지 새로고침
        st.rerun()

# 오른쪽: 뉴스/주식 패널
with col_news:
    if st.session_state.info_mode == "뉴스":
        # 뉴스 표시 (첫 번째 파일 UI 유지)
        if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
            with st.container(height=450):
                with st.spinner("뉴스를 불러오는 중..."):
                    news_data = get_naver_news(st.session_state.search_query)

                    if news_data and news_data.get('items'):
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

                            # 뉴스 카드 - 네이버 스타일
                            st.markdown(f"""
                            <div class="news-card">
                                <div class="news-meta">
                                    <span class="news-category" style="background-color: {category_color}20; color: {category_color};">
                                        {category}
                                    </span>
                                    <span class="news-time">{time_diff}</span>
                                </div>
                                <div class="news-title">
                                    <a href="{link}" target="_blank">
                                        {title}
                                    </a>
                                </div>
                                <div class="news-description">
                                    {description[:100]}{'...' if len(description) > 100 else ''}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="no-news">
                            <p>📭</p>
                            <p>검색된 뉴스가 없습니다</p>
                            <p>다른 키워드로 검색해보세요</p>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ 네이버 API 키가 설정되지 않았습니다.")

        # 검색창을 아래로 이동 (채팅 입력창과 같은 레벨)
        news_search = st.chat_input("검색어를 입력하세요")

        if news_search:
            st.session_state.search_query = news_search
            st.rerun()

    else:  # 주식 모드 (두 번째 파일의 주식 기능 적용)
        # 검색창 위치 (위아래 여백 추가)
        st.markdown('<div style="margin: 12px 0;">', unsafe_allow_html=True)
        stock_search = st.text_input("", placeholder="기업명을 입력하세요 (예: 삼성전자)", key="stock_input",
                                     label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        # 입력창 스타일링
        st.markdown("""
        <style>
        input[key="stock_input"] {
            border-radius: 20px !important;
            border: 2px solid #e1e5e9 !important;
            padding: 10px 15px !important;
            font-size: 14px !important;
            background: white !important;
            transition: all 0.3s ease !important;
        }
        input[key="stock_input"]:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # 주식 검색 결과 표시 (상단 여백 추가)
        if stock_search:
            company_name = stock_search.strip()

            if company_name:
                st.markdown('<div style="margin-top: 16px;">', unsafe_allow_html=True)
                with st.spinner("🔍 주식 정보를 분석하는 중..."):
                    stock_result = get_stock_data(company_name)

                if stock_result["success"]:
                    # 성공 헤더 (여백 조정)
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 14px; border-radius: 10px; margin: 12px 0; text-align: center;">
                        <div style="color: white; font-weight: bold; font-size: 14px;">🎯 {company_name}</div>
                        <div style="color: rgba(255,255,255,0.9); font-size: 12px;">종목코드: {stock_result['code']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    stock_data = stock_result["data"]
                    if not stock_data.empty and len(stock_data) > 0:
                        try:
                            # 최근 주가 정보 (안전하게 처리)
                            latest_price = float(stock_data["Close"].iloc[-1])
                            prev_price = float(stock_data["Close"].iloc[-2]) if len(
                                stock_data) > 1 else latest_price
                            price_change = latest_price - prev_price
                            change_percent = (price_change / prev_price) * 100 if prev_price != 0 else 0

                            # 주가 카드 디자인
                            if price_change > 0:
                                color = "#e53e3e"
                                bg_color = "#fed7d7"
                                arrow = "📈"
                                trend = "상승"
                            elif price_change < 0:
                                color = "#3182ce"
                                bg_color = "#bee3f8"
                                arrow = "📉"
                                trend = "하락"
                            else:
                                color = "#718096"
                                bg_color = "#edf2f7"
                                arrow = "📊"
                                trend = "보합"

                            # 메인 주가 카드 (여백 조정)
                            st.markdown(f"""
                            <div style="background: {bg_color}; padding: 16px; margin: 12px 0; border-radius: 12px; border-left: 4px solid {color};">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="font-size: 20px; font-weight: bold; color: #2d3748; margin-bottom: 4px;">
                                            {latest_price:,.0f}원
                                        </div>
                                        <div style="color: {color}; font-size: 13px; font-weight: 600;">
                                            {price_change:+,.0f}원 ({change_percent:+.2f}%)
                                        </div>
                                    </div>
                                    <div style="text-align: center;">
                                        <div style="font-size: 24px; margin-bottom: 4px;">{arrow}</div>
                                        <div style="font-size: 11px; color: {color}; font-weight: bold;">{trend}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # 최근 거래 현황 (안전하게 처리) - 여백 추가
                            if len(stock_data) >= 3:
                                st.markdown('<div style="margin: 16px 0 8px 0;"><strong>📋 최근 거래 현황</strong></div>',
                                            unsafe_allow_html=True)
                                display_data = stock_data[["Close", "Volume"]].tail(3).copy()
                                display_data.columns = ["종가(원)", "거래량"]
                                display_data.index = display_data.index.strftime('%m/%d')

                                # 거래량을 읽기 쉽게 포맷
                                display_data["거래량"] = display_data["거래량"].apply(lambda x: f"{int(x):,}")
                                display_data["종가(원)"] = display_data["종가(원)"].apply(lambda x: f"{int(x):,}")

                                st.dataframe(display_data, use_container_width=True, height=110)

                            # 당일 고가/저가 정보 (안전하게) - 여백 추가
                            try:
                                st.markdown('<div style="margin-top: 16px;">', unsafe_allow_html=True)
                                col1, col2 = st.columns(2)
                                with col1:
                                    high_price = float(stock_data["High"].iloc[-1])
                                    st.markdown(f"""
                                    <div style="background: #f7fafc; padding: 10px; border-radius: 8px; text-align: center;">
                                        <div style="font-size: 11px; color: #718096;">당일 최고가</div>
                                        <div style="font-size: 14px; font-weight: bold; color: #e53e3e;">{high_price:,.0f}원</div>
                                    </div>
                                    """, unsafe_allow_html=True)

                                with col2:
                                    low_price = float(stock_data["Low"].iloc[-1])
                                    st.markdown(f"""
                                    <div style="background: #f7fafc; padding: 10px; border-radius: 8px; text-align: center;">
                                        <div style="font-size: 11px; color: #718096;">당일 최저가</div>
                                        <div style="font-size: 14px; font-weight: bold; color: #3182ce;">{low_price:,.0f}원</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                            except:
                                st.info("📊 고가/저가 정보를 표시할 수 없습니다.")

                            # 데이터 소스 표시 (여백 추가)
                            data_source = stock_result.get("source", "unknown")
                            source_text = "KRX (한국거래소)" if data_source == "pykrx" else "Yahoo Finance"
                            st.markdown(
                                f'<div style="margin-top: 12px;"><small>📡 데이터 제공: {source_text}</small></div>',
                                unsafe_allow_html=True)

                        except Exception as e:
                            st.error(f"주가 데이터 처리 중 오류: {str(e)}")

                    else:
                        st.markdown("""
                        <div style="background: #fed7d7; padding: 16px; border-radius: 10px; text-align: center; margin: 12px 0;">
                            <div style="font-size: 18px; margin-bottom: 8px;">⚠️</div>
                            <div style="color: #e53e3e; font-weight: bold;">주가 데이터가 없습니다</div>
                            <div style="color: #9b2c2c; font-size: 12px; margin-top: 4px;">거래 정지 종목이거나 최신 데이터가 없을 수 있습니다</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: #fed7d7; padding: 16px; border-radius: 10px; text-align: center; margin: 12px 0;">
                        <div style="font-size: 18px; margin-bottom: 8px;">❌</div>
                        <div style="color: #e53e3e; font-weight: bold;">검색 결과 없음</div>
                        <div style="color: #9b2c2c; font-size: 12px; margin-top: 4px;">{stock_result['error']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            # 초기 화면 (여백 조정)
            st.markdown("""
            <div style="text-align: center; color: #a0aec0; padding: 32px 20px; background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%); border-radius: 12px; margin-top: 20px;">
                <div style="font-size: 32px; margin-bottom: 12px;">📊</div>
                <div style="font-size: 16px; font-weight: bold; color: #4a5568; margin-bottom: 8px;">실시간 주식 정보</div>
                <div style="font-size: 13px; color: #718096; line-height: 1.4;">
                    상장기업 이름을 입력하여<br>
                    최신 주가와 차트를 확인하세요
                </div>
                <div style="background: white; padding: 8px 12px; border-radius: 16px; display: inline-block; margin-top: 12px;">
                    <span style="font-size: 11px; color: #9b2c2c;">💡 예시: 삼성전자, LG화학, 카카오</span>
                </div>
            </div>
            """, unsafe_allow_html=True)