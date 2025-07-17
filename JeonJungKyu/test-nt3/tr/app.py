import streamlit as st
import pandas as pd
from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
from utils.corp_search import run_flexible_rag

# 환경변수 로드
load_dotenv()

EMBEDDING_MODEL = 'BAAI/bge-m3'


st.title("🏢 기업 재무제표, 사업보고서 RAG 시스템")
st.markdown("---")

    # 사이드바 설정
with st.sidebar:
    st.header("⚙️ 시스템 정보")

        # 시스템 설정 정보
    st.subheader("🔧 시스템 설정")
    st.write(f"**임베딩 모델**: {EMBEDDING_MODEL}")
    st.write(f"**LLM 모델**: gpt-4o-mini")

        # 새로고침 버튼
    if st.button("🔄 상태 새로고침"):
        st.cache_resource.clear()
        st.rerun()

    # 메인 컨텐츠
st.header("💬 질문하기")

    # 예시 질문들
example_questions = [
        "삼성전자 매출총이익은?",
        "현대 포스코의 GM Battery Raw Materials Corporation과 어떤 약정이 있나요?",
        "2024년 카카오의 주요 재무지표는?",
        "최근 투자 현황은 어떻게 되나요?"
    ]

st.subheader("🔍 예시 질문")
cols = st.columns(2)
for i, question in enumerate(example_questions):
    with cols[i % 2]:
        if st.button(question, key=f"example_{i}"):
            st.session_state.question = question

    # 질문 입력
question = st.text_input(
        "질문을 입력하세요:",
        value=st.session_state.get('question', ''),
        placeholder="예: 삼성전자의 2024년 매출은 얼마인가요?"
    )

if st.button("🔍 검색", type="primary"):
    if question:
        try:
            with st.spinner("답변을 생성중입니다..."):

                    # QA 결과
                st.subheader("🤖 AI 답변")
                answer = run_flexible_rag(question)

                    # 답변을 더 보기 좋게 표시
                st.markdown("---")
                st.write(answer)

        except Exception as e:
            st.write(e)


