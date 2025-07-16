import os
import json
import requests
import re
from dotenv import load_dotenv


# LangChain core
from langchain_core.tools import tool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence, RunnableLambda, RunnableParallel

# LangChain OpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.schema import AttributeInfo

# LangChain Community
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# LangChain chains
from langchain.chains import LLMChain
import streamlit as st
# Python built-in
from difflib import get_close_matches

# Pinecone import
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore

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
            'k': 4,
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
            'k': 10,
        }
    )

    # 메터데이터 정보
    '''
    metadata_field_info = [
        AttributeInfo(
            name='year',
            type='list[string]',
            description='사업보고서 연도(예시:2024)'),
        AttributeInfo(
            name='corp_name',
            type='string',
            description='사업보고서를 조회할 기업명 (예시: 삼성전자, NAVER, LG화학 등 명확한 회사명)'
        ),
        AttributeInfo(
            name='page_content',
            type='string',
            description='문서 본문 내용'),
        AttributeInfo(
            name="content_type",
            description="문서의 내용 분류 (예시: key_matters, research_development, esg_information,"
                        "other_important_matters, major_contract)- 예시에서만 뽑아주세요.",
            type="string",
        ),
        AttributeInfo(
            name="section",
            description="사업보고서의 섹션 (예시: 주요사항, 연구개발 활동, ESG(환경·사회·지배구조) 정보,"
                        "기타 중요사항, 주요사항, 재무지표, 주요 계약 및 거래) - 예시에서만 뽑아주세요.",
            type="string"),

    ]
    '''

    metadata_field_info = [
        AttributeInfo(
            name='year',
            type='list[string]',
            description='사업보고서 연도(예시:2024)'),
        AttributeInfo(
            name='corp_name',
            type='string',
            description='사업보고서를 조회할 기업명 (예시: 삼성전자, NAVER, LG화학 등 명확한 회사명)'
        ),
        AttributeInfo(
            name='page_content',
            type='string',
            description='문서 본문 내용'),

    ]

    '''
    metadata_field_info = [
        AttributeInfo(
            name="corp_name",
            description="회사 이름 (예: NAVER, 삼성전자, LG에너지솔루션 등)",
            type="string",
        ),
        AttributeInfo(
            name='year',
            type='string',
            description='사업보고서 조회할 연도(예시:2024)')
        ,
        AttributeInfo(
            name="section",
            description="사업보고서의 섹션 (예시: 주요사항, 연구개발 활동, ESG(환경·사회·지배구조) 정보,"
                        "기타 중요사항, 주요사항, 재무지표, 주요 계약 및 거래) - 예시에서만 뽑아주세요.",
            type="string",
        ),
        AttributeInfo(
            name="content_type",
            description="문서의 내용 분류 (예시: key_matters, research_development, esg_information,"
                        "other_important_matters, major_contract,  등)- 예시에서만 뽑아주세요.",
            type="string",
        )
    ]
    '''

    # SelfQueryRetriever 객체생성

    self_query_retriever = SelfQueryRetriever.from_llm(
        llm=ChatOpenAI(model='gpt-4o-mini', temperature=0),
        vectorstore=vector_db3,
        document_contents='page_content',  # 문서 내용을 가리키는 메타데이터 필드명
        metadata_field_info=metadata_field_info,
        search_kwargs={"k": 10}
    )



    return accounting_retriever, business_retriever, business_retriever2, self_query_retriever


