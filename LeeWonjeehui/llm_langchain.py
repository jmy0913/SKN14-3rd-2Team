from dotenv import load_dotenv
import os
from typing import Any, List
from pydantic import Field
from langchain.schema import BaseRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from dart_api import fetch_financial_docs_from_dart  # (company, year) 인자 등 실제 구현에 맞춰 조정

def run_hybrid_qa():
    load_dotenv()
    embeddings = OpenAIEmbeddings(model=os.environ["OPENAI_EMBEDDING_MODEL"])
    vector_store = PineconeVectorStore(
        index_name="financial",
        embedding=embeddings
    )

    # -- Pydantic 필드 명시 & arbitrary_types_allowed 처리 --
    class CombinedRetriever(BaseRetriever):
        vector_retriever: Any = Field(exclude=True)
        dart_api_func: Any = Field(exclude=True)
        
        class Config:
            arbitrary_types_allowed = True

        def _get_relevant_documents(self, query: str, *, run_manager=None) -> List:
            vector_docs = self.vector_retriever.get_relevant_documents(query)
            dart_docs = []
            # 예시 조건: 실서비스에서는 쿼리 파싱(회사, 연도 등 추출)로 대체 필요
            if any(kw in query for kw in ['재무제표', '자산', '원재료']):
                dart_docs = self.dart_api_func("삼성전자", 2023)  # 쿼리에서 추출하도록 수정 가능
            return vector_docs + dart_docs

        async def _aget_relevant_documents(self, query: str, *, run_manager=None) -> List:
            return self._get_relevant_documents(query)
    # -------------------------------------------------------

    system_prompt = """
    너는 사업보고서를 바탕으로 사용자에게 정확하고 신뢰도 높은 답변을 제공하는 AI 어시스턴트야.
    반드시 제공된 문서 내용만 바탕으로 답변해야 해. 추측하지 마.
    숫자나 수치는 문서에서 직접 인용하고, 단위를 포함해줘.
    문서에 근거가 없으면 "해당 정보는 문서에서 찾을 수 없습니다."라고 답변해.
    가능한 경우, 문서의 출처(ex. 페이지 번호 혹은 문단 요약)를 함께 포함해.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{question}"),
        ("system", "관련 문서:\n{context}")
    ])

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.environ["OPENAI_API_KEY"]
    )

    combined_retriever = CombinedRetriever(
        vector_retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
        dart_api_func=fetch_financial_docs_from_dart
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=combined_retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}
    )

    # Q&A 실행 예시
    question = "삼성전자 2023년 자산 및 주요 원재료 현황 알려줘."
    result = qa_chain.run(question)
    print(result)

if __name__ == "__main__":
    run_hybrid_qa()
