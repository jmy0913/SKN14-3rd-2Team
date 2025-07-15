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
from langchain_openai import ChatOpenAI

# LangChain Community
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# LangChain chains
from langchain.chains import LLMChain
import streamlit as st
# Python built-in
from difflib import get_close_matches

# Load environment variables
load_dotenv()


@st.cache_resource
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

    business_retriever = vector_db1.as_retriever(
        search_type='similarity',
        search_kwargs={
            'k': 5,
        })

    return accounting_retriever, business_retriever


