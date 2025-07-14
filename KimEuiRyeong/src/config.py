import os
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
