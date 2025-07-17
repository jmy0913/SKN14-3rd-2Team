from typing import List, Callable, Union
import os

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.documents import Document

from src.llm import LLM
from src.services.document_service import DocumentService
from src.rag.document_loader import DocumentLoader

class Orchestrator:
    """메인 오케스트레이터 - 모든 구성 요소를 조정합니다."""
    
    def __init__(self):
        # 새로운 모듈화된 서비스 사용
        self.document_service = DocumentService()
        # 하위 호환성을 위해 기존 인터페이스 유지
        self.vector_store = self.document_service.vector_store

    def query_llm(self, query: str) -> str:
        """LLM에 직접 쿼리를 보냅니다."""
        llm = LLM()
        prompt: List[Union[HumanMessage, SystemMessage, AIMessage, ToolMessage]] = [HumanMessage(query)] 
        response: str = llm.invoke(prompt)
        return response

    def query_llm_with_tools(self, query: str) -> str:
        """도구를 사용하여 LLM에 쿼리를 보냅니다. (현재 사용 가능한 도구 없음)"""
        # 현재 재무 데이터 RAG 시스템에는 별도 도구가 필요하지 않음
        return self.query_llm(query)
    
    def upload_docs_to_rag(self, path: str) -> List[str]:
        """파일에서 문서를 로드하고 RAG에 업로드합니다."""
        self.vector_store.get_index_ready()
        document_loader = DocumentLoader()
        documents: List[Document] = document_loader.get_document_chunks(path)
        uploaded_ids: List[str] = self.vector_store.add_documents_to_index(documents)
        return uploaded_ids
    
    def query_rag(self, query: str) -> str:
        """RAG 시스템을 사용하여 쿼리에 응답합니다."""
        try:
            self.vector_store.get_index_ready()
            
            # 새로운 서비스를 통해 문서 검색
            documents = self.document_service.search_documents(query, k=5)
            
            if not documents:
                return "관련 정보를 찾을 수 없습니다."
            
            # 검색된 문서 내용 추출
            retrieved_content = [doc.page_content for doc in documents]
            print(f'retrieved_content : {retrieved_content}')
            
            # LLM에 컨텍스트와 함께 쿼리
            llm = LLM()
            prompt = []
            prompt.append(
                SystemMessage(
                    "Use the following retrieved contents to inform your response: " + str(retrieved_content)
                )
            )
            prompt.append(
                HumanMessage(query)
            )
            response: str = llm.invoke(prompt)
            return response
            
        except Exception as e:
            print(f"[ERROR] RAG 쿼리 처리 중 오류: {e}")
            return f"죄송합니다. 쿼리 처리 중 오류가 발생했습니다: {str(e)}"
    
    def delete_all_vectors(self) -> None:
        """모든 벡터를 삭제합니다."""
        if not self.vector_store.check_index_exists():
            raise Exception("Vectors cannot be deleted as index doesn't exist.")
        return self.vector_store.delete_all_vectors()
    
    def get_vector_store_stats(self) -> dict:
        """벡터 스토어 통계를 가져옵니다."""
        return self.document_service.get_vector_store_stats()