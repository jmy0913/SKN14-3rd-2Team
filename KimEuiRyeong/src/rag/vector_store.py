from typing import List
from uuid import uuid4

from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from src.config import PINECONE_KEY, OPENAI_KEY, EMBEDDING_MODEL_NAME

class VectorStore:
    def __init__(self, index_name: str):
        self.pc = Pinecone(api_key=PINECONE_KEY)
        self.index_name: str = index_name

    def create_index(self) -> None:
        # This uses the pinecone library
        index = self.pc.create_index(
            name=self.index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        print(f'Created index: {index}')

    def check_index_exists(self) -> bool:
        # This uses the pinecone library
        if not self.pc.has_index(self.index_name):
            return False
        return True
    
    def get_index_ready(self) -> None:
        if not self.check_index_exists():
            self.create_index()
    
    def get_index(self) -> PineconeVectorStore:
        # This uses the Langchain-pinecone library
        embedding_model = OpenAIEmbeddings(
            model=EMBEDDING_MODEL_NAME,
            api_key=OPENAI_KEY
        )
        index = self.pc.Index(self.index_name)
        vs_index = PineconeVectorStore(index=index, embedding=embedding_model)
        return vs_index

    def add_documents_to_index(self, documents: List[Document]) -> List[str]:
        vs_index: PineconeVectorStore = self.get_index()
        uuids = [str(uuid4()) for _ in range(len(documents))]
        list_of_ids: List[str] = vs_index.add_documents(documents=documents, ids=uuids)
        return list_of_ids
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """유사도 검색을 수행합니다."""
        vs_index: PineconeVectorStore = self.get_index()
        results = vs_index.similarity_search(query, k=k)
        return results
    
    def get_index_stats(self) -> dict:
        """인덱스 통계를 가져옵니다."""
        try:
            index = self.pc.Index(self.index_name)
            stats = index.describe_index_stats()
            return stats
        except Exception as e:
            return {"error": str(e)}
    
    def delete_all_vectors(self) -> None:
        """인덱스의 모든 벡터를 삭제합니다."""
        try:
            index = self.pc.Index(self.index_name)
            index.delete(delete_all=True)
            print(f"[SUCCESS] 인덱스 '{self.index_name}'의 모든 벡터 삭제 완료")
        except Exception as e:
            print(f"[ERROR] 벡터 삭제 실패: {e}")
        
