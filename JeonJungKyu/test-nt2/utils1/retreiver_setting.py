from dotenv import load_dotenv

from transformers import BertTokenizer

from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.schema import AttributeInfo

# LangChain Community
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


from langchain.embeddings import OpenAIEmbeddings  # OpenAIEmbeddings 임포트 추가
from langchain_openai import ChatOpenAI

# Pinecone import
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore

from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize
import string
import os

# Load environment variables
load_dotenv()


# 설정
PINECONE_INDEX_NAME = "3rd-project"
PINECONE_DIMENSION = 1536
PINECONE_REGION = "us-east-1"
PINECONE_CLOUD = "aws"
EMBEDDING_MODEL = "text-embedding-3-small"

def faiss_retriever_loading():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    faiss_path1 = os.path.join(current_dir, "faiss_index3")
    faiss_path2 = os.path.join(current_dir, "faiss_index_bge_m3")
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

    vector_db1 = FAISS.load_local(
        faiss_path1,
        embeddings,
        allow_dangerous_deserialization=True
    )

    accounting_retriever = vector_db1.as_retriever(
        search_type='similarity',
        search_kwargs={
            'k': 6
        })

    # 사업보고서 벡터 db
    vector_db2 = FAISS.load_local(
        faiss_path2,
        embeddings,
        allow_dangerous_deserialization=True
    )


    business_retriever = vector_db2.as_retriever(
        search_type='similarity',
        search_kwargs={
            'k': 5,
        })


    # 사업보고서 벡터 db - pinecone
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    index = pc.Index(PINECONE_INDEX_NAME)
    vector_db3 = PineconeVectorStore(index=index, embedding=embeddings)

    business_retriever2 = vector_db3.as_retriever(
        search_type='similarity',
        search_kwargs={
            'k': 7,
        }
    )



    metadata_field_info = [
        AttributeInfo(
            name='year',
            type='list[string]',
            description='사업보고서 연도(예시:2024)'),
        AttributeInfo(
            name='page_content',
            type='string',
            description='문서 본문 내용')]


    # SelfQueryRetriever 객체생성

    self_query_retriever = SelfQueryRetriever.from_llm(
        llm=ChatOpenAI(model='gpt-4o-mini', temperature=0),
        vectorstore=vector_db3,
        document_contents='page_content',  # 문서 내용을 가리키는 메타데이터 필드명
        metadata_field_info=metadata_field_info,
        search_kwargs={"k": 7}
    )

    return accounting_retriever, business_retriever, business_retriever2, self_query_retriever

# 한국어 형태소 분석기
def preprocess(text):
    tokenizer = BertTokenizer.from_pretrained('kykim/bert-kor-base')
    # BERT tokenizer를 사용하여 텍스트 토큰화
    tokens = tokenizer.tokenize(text)  # BERT tokenizer로 단어 분리
    return tokens

def calculate_bm25(query, documents):
    # 문서에서 텍스트만 추출
    doc_tokens = [preprocess(doc.page_content) for doc in documents]  # 문서 전처리
    bm25 = BM25Okapi(doc_tokens)  # BM25 모델 초기화
    query_tokens = preprocess(query)  # 쿼리 전처리
    return bm25.get_scores(query_tokens)  # BM25 점수 계산

