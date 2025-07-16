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

# 설정
PINECONE_INDEX_NAME = "samsung-rag"
PINECONE_DIMENSION = 1536
PINECONE_REGION = "us-east-1"
PINECONE_CLOUD = "aws"
EMBEDDING_MODEL = "text-embedding-3-small"

# 시스템 프롬프트
SYSTEM_PROMPT = """
너는 기업의 공시문서(예: 분기보고서, 사업보고서, 감사보고서 등)를 기반으로 정확하고 근거 있는 답변을 제공하는 AI 어시스턴트이자
기업의 현황과 흐름을 알려주는 전문 컨설턴트야.

지켜야 할 원칙:
- 반드시 제공된 문서 내용만 바탕으로 답변해야 해. 추측하지 마.
- 숫자나 수치는 문서에서 직접 인용하고, 단위를 포함해줘.
- 문서에 근거가 없으면 "해당 정보는 문서에서 찾을 수 없습니다."라고 답변해.
- 가능한 경우, 문서의 출처(ex. 페이지 번호 or 문단 내용)를 함께 포함해.
- 모르는 내용은 절대로 대답하지마
- 초급 중급에 나눠서 각각 초등학생수준 일반인 수준으로 설명을 해줘

🧾 예시:
"2025년 1분기 삼성전자의 매출총이익은 약 20조 원이며, 이는 2024년 동기 대비 8% 증가한 수치입니다. (출처: 3페이지)"

목표는 **정확성, 투명성, 신뢰도**를 갖춘 답변이야.
"""


@st.cache_resource
def initialize_pinecone():
    """Pinecone 초기화"""
    return Pinecone(api_key=os.environ["PINECONE_API_KEY"])


@st.cache_resource
def setup_vector_store():
    """벡터 스토어 설정"""
    pc = initialize_pinecone()
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    index = pc.Index(PINECONE_INDEX_NAME)
    return PineconeVectorStore(index=index, embedding=embeddings)


@st.cache_resource
def setup_qa_chain():
    """QA 체인 설정"""
    vector_store = setup_vector_store()

    # 프롬프트 구성
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", "{question}"),
        ("system", "관련 문서:\n{context}")
    ])

    # LLM 구성
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.environ["OPENAI_API_KEY"]
    )

    # QA 체인 생성
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}
    )

    return qa_chain, vector_store


def get_pinecone_stats():
    """Pinecone 데이터베이스 통계 정보 가져오기"""
    try:
        pc = initialize_pinecone()
        index = pc.Index(PINECONE_INDEX_NAME)
        stats = index.describe_index_stats()
        return stats
    except Exception as e:
        st.error(f"Pinecone 연결 오류: {str(e)}")
        return None


def main():
    st.title("🏢 시총50기업 공시문서 RAG 시스템")
    st.markdown("---")

    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 시스템 정보")

        # Pinecone 데이터베이스 상태
        st.subheader("📊 데이터베이스 상태")

        try:
            stats = get_pinecone_stats()
            if stats:
                st.success("✅ Pinecone 연결 성공")
                st.write(f"**인덱스명**: {PINECONE_INDEX_NAME}")
                st.write(f"**총 벡터 수**: {stats.total_vector_count:,}")
                st.write(f"**차원**: {stats.dimension}")

                # 네임스페이스 정보
                if hasattr(stats, 'namespaces') and stats.namespaces:
                    st.write("**네임스페이스**:")
                    for namespace, info in stats.namespaces.items():
                        if namespace == "":
                            namespace = "기본"
                        st.write(f"  - {namespace}: {info.vector_count:,}개")
            else:
                st.error("❌ Pinecone 연결 실패")

        except Exception as e:
            st.error(f"❌ 데이터베이스 상태 확인 실패: {str(e)}")

        st.markdown("---")

        # 시스템 설정 정보
        st.subheader("🔧 시스템 설정")
        st.write(f"**임베딩 모델**: {EMBEDDING_MODEL}")
        st.write(f"**검색 문서 수**: 3개")
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
        "2024년 주요 재무지표는?",
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
                # 시스템 상태 확인
                with st.spinner("시스템 연결 확인 중..."):
                    stats = get_pinecone_stats()
                    if not stats or stats.total_vector_count == 0:
                        st.error("❌ 데이터베이스에 데이터가 없습니다. 관리자에게 문의하세요.")
                        return

                with st.spinner("답변을 생성중입니다..."):
                    qa_chain, vector_store = setup_qa_chain()

                    # 검색 결과 먼저 표시
                    st.subheader("📋 관련 문서")
                    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
                    results = retriever.invoke(question)

                    if not results:
                        st.warning("관련 문서를 찾을 수 없습니다. 다른 질문을 시도해보세요.")
                        return

                    for i, result in enumerate(results, 1):
                        with st.expander(f"📄 문서 {i} (유사도 점수 기준)"):
                            st.write(result.page_content)

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