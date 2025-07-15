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

# 환경변수 로드
load_dotenv()

EMBEDDING_MODEL = 'BAAI/bge-m3'


def main():
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
                    qa_chain, vector_store = setup_qa_chain()

                    # QA 결과
                    st.subheader("🤖 AI 답변")
                    answer = qa_chain.run(question)

                    # 답변을 더 보기 좋게 표시
                    st.markdown("---")
                    st.write(answer)

                    # 신뢰도 안내
                    st.info("💡 이 답변은 위의 관련 문서를 기반으로 생성되었습니다.")

            except Exception as e:
                st.error(f"❌ 오류가 발생했습니다: {str(e)}")
                st.write("**가능한 원인:**")
                st.write("- 환경변수 설정 오류")
                st.write("- API 키 만료 또는 할당량 초과")
                st.write("- 네트워크 연결 문제")
                st.write("- Pinecone 인덱스 접근 문제")
        else:
            st.warning("❗ 질문을 입력해주세요.")

    # 하단 정보
    st.markdown("---")

    # 시스템 정보
    col1, col2 = st.columns(2)

    with col1:
        st.info("💡 **시스템 특징**\n"
                "- 공시문서 기반 정확한 정보 제공\n"
                "- 문서에 없는 내용은 답변하지 않음\n"
                "- 실시간 벡터 검색으로 관련 문서 찾기")

    with col2:
        st.success("✅ **데이터베이스 준비 완료**\n"
                   "- 삼성전자 통합 사업보고서 (2022-2024)\n"
                   "- 벡터 임베딩 완료\n"
                   "- 즉시 검색 가능")

    # 사용 팁
    with st.expander("📝 사용 팁"):
        st.write("""
        **효과적인 질문 방법:**
        1. 구체적인 수치나 데이터를 요청하세요
        2. 특정 연도나 기간을 명시하세요
        3. 회사명이나 사업 부문을 정확히 기재하세요

        **예시:**
        - ✅ "2024년 삼성전자 매출액은 얼마인가요?"
        - ✅ "반도체 사업부의 영업이익 추이는?"
        - ❌ "삼성이 어떤 회사인가요?" (너무 일반적)
        """)

    # 저작권 정보
    st.caption("📋 본 시스템은 공개된 사업보고서 데이터를 기반으로 하며, 투자 판단의 참고용으로만 사용하시기 바랍니다.")


if __name__ == "__main__":
    main()