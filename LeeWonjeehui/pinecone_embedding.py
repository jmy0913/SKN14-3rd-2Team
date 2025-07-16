import os
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


# 필요한 라이브러리 임포트
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import os




def init_pinecone_vector_store(
    index_name,
    dimension,
    metric,
    region,
    cloud,
    embedding_model
):
    pc = Pinecone()
    print(pc.list_indexes().names())
    print(pc.list_indexes())
    try:
        if index_name not in pc.list_indexes():
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(
                    region=region,
                    cloud=cloud
                )
            )
            print(f'{index_name} index 생성완료!')
        else:
            print(f'{index_name} index가 이미 존재합니다.')
    except Exception as e:
        # 409 에러가 발생하면 이미 존재하는 것이므로 무시
        if "ALREADY_EXISTS" in str(e):
            print(f'{index_name} index가 이미 존재합니다. (409 Conflict)')
        else:
            raise e

    embeddings = OpenAIEmbeddings(model=embedding_model)
    vector_store = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings
    )
    return vector_store

vector_store = init_pinecone_vector_store(
    index_name=PINECONE_INDEX_NAME,
    dimension=PINECONE_INDEX_DIMENSION,
    metric=PINECONE_INDEX_METRIC,
    region=PINECONE_INDEX_REGION,
    cloud=PINECONE_INDEX_CLOUD,
    embedding_model=OPENAI_EMBEDDING_MODEL
)
