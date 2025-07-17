import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv() # load all the environment variable.

OPENAI_KEY=os.environ.get("OPENAI_KEY")
MODEL_NAME=os.environ.get("MODEL_NAME")
PINECONE_KEY=os.environ.get("PINECONE_KEY")
EMBEDDING_MODEL_NAME=os.environ.get("EMBEDDING_MODEL_NAME")
VECTOR_STORE_INDEX_NAME=os.environ.get("VECTOR_STORE_INDEX_NAME")
CHUNK_SIZE=int(os.environ.get("CHUNK_SIZE"))
CHUNK_OVERLAP=int(os.environ.get("CHUNK_OVERLAP"))

# ADD by EUIRYEONG
RAG_DOCUMENTS_FOLDER_NAME=os.environ.get("RAG_DOCUMENTS_FOLDER_NAME")
FINANCIAL_REPORTS_FOLDER_NAME=os.environ.get("FINANCIAL_REPORTS_FOLDER_NAME")
DART_API_KEY=os.environ.get("DART_API_KEY")

# 대량 처리 설정을 별도 모듈로 분리
from .bulk_config import (
    get_target_companies_from_env,
    get_target_years_from_env,
    get_bulk_processing_settings
)

def load_config():
    """환경 설정을 로드하는 함수"""
    return {
        "openai_key": OPENAI_KEY,
        "model_name": MODEL_NAME,
        "pinecone_key": PINECONE_KEY,
        "embedding_model_name": EMBEDDING_MODEL_NAME,
        "vector_store_index_name": VECTOR_STORE_INDEX_NAME,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "rag_documents_folder_name": RAG_DOCUMENTS_FOLDER_NAME,
        "financial_reports_folder_name": FINANCIAL_REPORTS_FOLDER_NAME,
        "dart_api_key": DART_API_KEY
    }
