from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd
from dotenv import load_dotenv
import os
from tqdm import tqdm
from pinecone_embedding import init_pinecone_vector_store
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 사용 예시
LANGSMITH_TRACING = os.getenv('LANGSMITH_TRACING')
LANGSMITH_ENDPOINT = os.getenv('LANGSMITH_ENDPOINT')
LANGSMITH_API_KEY = os.getenv('LANGSMITH_API_KEY')
LANGSMITH_PROJECT = os.getenv('LANGSMITH_PROJECT')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
DART_API_KEY = os.getenv('DART_API_KEY')

PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'dart')
PINECONE_INDEX_REGION = os.getenv('PINECONE_INDEX_REGION', 'us-east-1')
PINECONE_INDEX_CLOUD = os.getenv('PINECONE_INDEX_CLOUD', 'aws')
PINECONE_INDEX_METRIC = os.getenv('PINECONE_INDEX_METRIC', 'cosine')
PINECONE_INDEX_DIMENSION = int(os.getenv('PINECONE_INDEX_DIMENSION', '1536'))

OPENAI_LLM_MODEL = os.getenv('OPENAI_LLM_MODEL', 'gpt-4o-mini')
OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')







def embed_and_upload_documents(
    csv_path,
    vector_store,
    chunk_size=1000,
    chunk_overlap=100,
    batch_size=100
):
    # 환경 변수 로드
    load_dotenv()
    
    # CSV 파일 읽기
    df = pd.read_csv(csv_path)

    # 텍스트 분할기 생성
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    # Document 리스트 생성
    documents = []
    for idx, row in df.iterrows():
        chunks = text_splitter.split_text(row['텍스트 미리보기'])
        for chunk in chunks:
            doc = Document(
                page_content=chunk,
                metadata={
                    '년도': row['년도'],
                    '회사명': row['회사명']
                }
            )
            documents.append(doc)

    # 문서 일괄 업로드
    for i in tqdm(range(0, len(documents), batch_size)):
        batch = documents[i:i+batch_size]
        vector_store.add_documents(batch)



# 벡터스토어 객체 생성 (임베딩 포함)
vector_store = init_pinecone_vector_store(
    index_name=PINECONE_INDEX_NAME,
    dimension=PINECONE_INDEX_DIMENSION,
    metric=PINECONE_INDEX_METRIC,
    region=PINECONE_INDEX_REGION,
    cloud=PINECONE_INDEX_CLOUD,
    embedding_model=OPENAI_EMBEDDING_MODEL
)

# 문서 임베딩 및 업로드
embed_and_upload_documents(
    csv_path="documents.csv",
    vector_store=vector_store,
    chunk_size=1000,
    chunk_overlap=100,
    batch_size=100
)
