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

# 작업 분류용 프롬프트
classification_prompt = PromptTemplate.from_template("""
다음 질문을 읽고, 어떤 종류의 정보가 필요한지 작업 유형을 분류하세요.:

- 회계기준서만 필요한 질문: "accounting"
- 사업보고서 내용만 필요한 질문: "business"
- 재무제표 내용만 필요한 질문: "finance"
- 회계 기준서는 기본이고, 사업보고서,재무제표까지도 모두 필요한 질문: "hybrid"
- 회계 관련이 아닌 다른 질문일때: "else"

형식: 작업유형: <type>

질문: 재고자산은 어떻게 관리해?
작업유형: accounting

질문: 매출 총이익률이 뭐야?
작업유형: accounting

질문: 삼성전자의 2023년 사업보고서의 핵심 내용을 요약해줘
작업유형: business

질문: 삼성전자는 2023년에 무슨 사업을 했어?
작업유형: business

질문: 삼성전자 2024년 사업보고서에는 뭐가 핵심이야?
작업유형: business

질문: 카카오는 요즘 사업 상황이 어때?
작업유형: hybrid

질문: LG화학의 2024년 재무제표 수치를 알려줘
작업유형: finance

질문: 카카오의 재무제표를 분석해줘
작업유형: finance

질문: 카카오의 2023년 재무제표를 보고 앞으로의 전망을 알려줘
작업유형: hybrid

질문: 네이버 재무 상태를 보면 앞으로 전망이 어때 ?
작업유형: hybrid

질문: 요즘 재밌는 영화 뭐가 있나?
작업유형: else

질문: {question}
작업유형:
""")

# 회계 질문 답변 프롬프트
accounting_prompt = PromptTemplate.from_template(
    """다음 회계 기준서 내용만을 바탕으로 질문에 답변해주고, 다른 내용으로 추론하거나 답변하지 마세요.

회계 기준서:
{context}

질문:
{question}
"""
)

# 일반 질문 답변 프롬프트
simple_prompt = PromptTemplate.from_template("""
사용자의 질문에 대해서 아래와 같이 답변해주세요.
답변: 해당 내용은 제가 알지 못하는 분야입니다.
질문: {question}
""")

# 회사명과 연도를 추출하는 프롬프트
extract_prompt = PromptTemplate.from_template("""
사용자의 질문에서 회사 이름과 연도를 추출해 주세요.
사용자 질문에 따로 연도 관련 내용이 없으면 2023, 2024로 해주세요.
형식은 반드시 다음과 같이 해주세요:
회사: <회사명>
연도: <연도(4자리 숫자)>

[예시]
회사: 삼성전자  
연도: 2022, 2023, 2024

질문: {question}
""")

# 사업보고서 질문 답변 프롬프트
business_prompt = PromptTemplate.from_template("""
다음은 사업보고서에서 추출된 정성적 설명입니다.  
재무 수치는 일부 포함되어 있으나, 정성적 설명 위주로 활용해주세요.

📌 반드시 지켜야 할 규칙:
- 금액, 비율, 연도, 수치 등 숫자 관련 설명을 너무 길지 않게 적고, 사업 및 재무 상태에 대한 정성적인 해석 위주로 진행해주세요.
- 재무 데이터는 API를 통해만 제공되며, 현재는 참고용 문서만 있습니다.
- 정확한 수치가 필요한 경우, "정확한 수치는 재무제표 API를 통해 확인해야 합니다"라고만 말하세요.

<사업보고서 발췌 내용>
{context}

<질문>
{question}

<답변>
""")

# 하이브리드 작업 질문 답변 프름프트
hybrid_prompt = PromptTemplate.from_template("""
다음은 사용자의 질문에 답변하기 위한 참고 자료입니다.
- 📘 회계 기준서: 실제 회계기준서 내용을 기반으로 하며, 해당 회계 기준 기반으로만 추론이 가능하고 다른 기준은 절대 추론에 적용하지 마세요.
- 📄 사업보고서: 실제 기업의 사업보고서에서 발췌된 내용입니다. 연도별 구분을 명확히 하여 분석하고, 사업 상황 및 기업 전망 분석 시 활용하세요.
- 📊 재무제표: 아래 데이터는 실제 API를 통해 가져온 수치이며, 이 데이터에 기반해서만 분석하세요. 연도별로 구분하여 서술하고, 없는 연도에 대해 예측하거나 임의로 생성하지 마세요.

다음 정보를 바탕으로, 질문에 대해 실제 문서 기반 분석으로 내용을 두서있게 정리해주고, 결론 부분은 상세히 이해하기 쉽게 작성해주세요.
📘 회계 기준서:
{acct}

📄 사업보고서:
{biz}

📊 재무제표:
{fin}

⛔ 주의:
- 실제 문서에 있는 내용만 사용해야 하며, 임의로 수치를 조합하거나 예상치를 추론하지 마세요.
- 연도별로 수치 데이터를 너무 길게 작성하지 말고, 핵심 변화 내용 위주로 서술해주세요.
- 없거나 모호한 내용은 "관련 자료에서는 해당 정보를 찾을 수 없습니다"라고 명확히 답변하세요.
- 1억 이상의 숫자는 ~억원으로 표시해주세요. (ex: 820억원)

질문: {question}
""")

# 제무재표 질문 답변 프롬프트
financial_prompt = PromptTemplate.from_template("""
다음은 실제 API로부터 얻은 기업의 연도별 재무제표 데이터입니다.
각 연도의 데이터를 구분하여 분석하세요. 추측이나 임의 해석 없이 아래 수치에 기반하여 설명만 하세요.

{financial_data}

⛔ 주의사항:
- 반드시 각 연도별로 나눠서 해석하고, "2022년에는 ~", "2023년에는 ~" 와 같은 형식으로 작성하세요.
- 없는 데이터는 해석하지 마세요.
- 이 데이터 외에 임의로 지어내거나 일반화하지 마세요.
- 1억 이상의 숫자는 ~억원으로 표시해주세요. (ex: 820억원)

질문: {question}
""")

@st.cache_resource
def create_chain():
    simple_llm = ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0)
    classification_chain = classification_prompt | simple_llm | StrOutputParser()
    account_chain = accounting_prompt | simple_llm | StrOutputParser()
    simple_chain = simple_prompt | simple_llm | StrOutputParser()
    extract_chain = extract_prompt | simple_llm | StrOutputParser()
    business_chain = business_prompt | simple_llm | StrOutputParser()
    hybrid_chain = hybrid_prompt | simple_llm | StrOutputParser()
    financial_chain = financial_prompt | simple_llm | StrOutputParser()

    return simple_chain, classification_chain, account_chain, extract_chain, business_chain, hybrid_chain, financial_chain





