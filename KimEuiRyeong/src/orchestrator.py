from typing import List, Callable, Union
import os

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.documents import Document

from src.llm import LLM
from src.tools.get_weather import get_us_state_weather_alerts
from src.rag.vector_store import VectorStore
from src.rag.document_loader import DocumentLoader

# ADD by EUIRYEONG
from src.rag.document_saver import DocumentSaver

# ADD by EUIRYEONG
from src.config import VECTOR_STORE_INDEX_NAME, RAG_DOCUMENTS_FOLDER_NAME

class Orchestrator:
    def __init__(self):
        self.vector_store = VectorStore(VECTOR_STORE_INDEX_NAME)

    def query_llm(self, query: str) -> str:
        llm = LLM()
        prompt: List[HumanMessage] = [HumanMessage(query)] 
        response: str = llm.invoke(prompt)
        return response

    def query_llm_with_tools(self, query: str) -> str:
        tools: List[Callable] = [get_us_state_weather_alerts]
        llm = LLM(tools=tools)
        prompt: List[Union[HumanMessage, SystemMessage, AIMessage, ToolMessage]] = [HumanMessage(query)]
        response: str = llm.invoke_with_tools(prompt)
        return response
    
    def upload_docs_to_rag(self, path: str) -> List[str]:
        self.vector_store.get_index_ready()
        document_loader = DocumentLoader()
        documents: List[Document] = document_loader.get_document_chunks(path)
        uploaded_ids: List[str] = self.vector_store.add_documents_to_index(documents)
        return uploaded_ids
    
    def query_rag(self, query: str) -> str:
        self.vector_store.get_index_ready()
        retrieved_content: List[str] = self.vector_store.similarity_search(query)
        llm = LLM()
        prompt: List[SystemMessage, HumanMessage] = []
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
    
    def delete_all_vectors(self) -> None:
        if not self.vector_store.check_index_exists():
            raise Exception("Vectors cannot be deleted as index doesn't exist.")
        return self.vector_store.delete_all_vectors()
    
    # ADD by EUIRYEONG
    def save_financial_reports(self):
        document_saver = DocumentSaver()
        filtered_dict = document_saver.filter_corp_codes_by_name()
        saved_documents = document_saver.save_financial_reports_document(filtered_dict)
        return saved_documents
