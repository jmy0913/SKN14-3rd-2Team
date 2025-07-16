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

# LangChain chains

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

## 🤔 분류 과정
질문: {question}
1. 정보 유형: [필요한 데이터 유형 판단]
2. 분류 근거: [분류 이유 간단히 설명]
작업유형:

]
""")



# CoT 방식 회계 질문 답변 프롬프트 (개선)
accounting_prompt = PromptTemplate.from_template("""
당신은 회계 기준서 전문가입니다. 제공된 회계 기준서 내용만을 바탕으로 쉽게 설명해주세요.

## 📘 제공된 회계 기준서
{context}

## 🔍 분석 과정

**기준서에서 찾기**
- 관련 내용: [기준서에서 질문과 관련된 내용]
- 핵심 정의: [기준서에 나온 쉬운 정의]
- 처리 방법: [기준서에서 제시한 방법]

**쉬운 설명**
- 간단히 말하면: [복잡한 내용을 쉽게 풀어서 설명]
- 실제로는: [실무에서 어떻게 적용되는지]
- 주의할 점: [기준서에서 언급한 중요한 사항]

## 📋 최종 답변

**기준서 기반 답변**
[제공된 회계 기준서 내용을 쉽게 풀어서 설명]

**실무 적용**
- 언제 적용: [적용 시점을 쉽게 설명]
- 어떻게 처리: [처리 방법을 단계별로 쉽게 설명]
- 기록할 내용: [공시나 기록 요구사항을 쉽게 설명]

## ⛔ 답변 준수사항
- 제공된 회계 기준서 내용만 사용
- 전문용어는 쉽게 풀어서 설명
- 기준서에 없는 내용은 "해당 기준서에서는 관련 내용을 찾을 수 없습니다" 명시
- 복잡한 내용은 단계별로 나누어 설명
- 실무에서 이해하기 쉽도록 구체적 예시 활용

질문: {question}
""")


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


# CoT 방식 사업보고서 질문 답변 프롬프트
business_prompt = PromptTemplate.from_template("""
당신은 사업보고서 분석 전문가입니다. 제공된 사업보고서 내용을 바탕으로 정성적 분석을 중심으로 답변해주세요.

## 📄 제공된 사업보고서 내용
{context}

## 🔍 분석 과정

**핵심 내용 파악**
- 질문 요점: [무엇을 묻고 있는지 파악]
- 관련 사업 영역: [사업보고서에서 관련된 사업 부문이나 영역]
- 주요 키워드: [중요한 사업 관련 키워드나 개념]

**사업보고서 내용 분석**
- 사업 현황: [보고서에 나타난 사업 상황이나 환경]
- 주요 변화: [전년 대비 또는 최근 변화 사항]
- 전략 방향: [보고서에 언급된 전략이나 계획]

**정성적 해석**
- 사업적 의미: [수치를 넘어선 사업적 의미와 함의]
- 시장 상황: [시장 환경이나 경쟁 상황]
- 향후 전망: [보고서에 나타난 전망이나 계획]

## 📋 최종 답변

**사업 현황 분석**
[사업보고서를 바탕으로 한 정성적 분석]

**주요 사업 변화**
[중요한 변화 사항을 정성적으로 해석]

**전략적 의미**
[사업 전략이나 향후 방향성에 대한 분석]

## ⛔ 답변 준수사항
- 정성적 설명 위주로 작성
- 숫자 관련 설명은 간략하게만 언급
- 정확한 수치 필요 시: "정확한 수치는 재무제표 API를 통해 확인해야 합니다"
- 사업보고서 내용만 활용
- 사업적 의미와 해석에 집중
- 시장 상황과 전략적 관점 포함

질문: {question}
""")




# CoT 방식 하이브리드 작업 질문 답변 프롬프트
# 개선된 CoT 방식 하이브리드 작업 질문 답변 프롬프트
hybrid_prompt = PromptTemplate.from_template("""
당신은 회계 및 재무 분석 전문가입니다. 다음 참고 자료를 바탕으로 체계적으로 분석해주세요.

## 📋 제공된 참고 자료
📘 회계 기준서:
{acct}nn

📄 사업보고서:
{biz}

📊 재무제표:
{fin}

## 🔍 분석 과정

**핵심 질문 파악**
질문: {question}
- 분석 유형: [회계기준 해석/재무분석/사업현황 분석]
- 필요 정보: [구체적으로 무엇을 찾아야 하는지]

**관련 자료 매칭**
- 회계기준: [해당 조항/기준]
- 사업보고서: [관련 내용 요약]
- 재무제표: [구체적 수치 및 항목]

**데이터 기반 분석**
- 재무제표 핵심 수치:
  * [연도]: [항목명] [구체적 금액]
  * [연도]: [항목명] [구체적 금액]
  * 변화율: [계산된 증감률]
- 회계기준 해석: [적용 가능한 기준과 해석]
- 사업 현황: [보고서 기반 핵심 내용]

## 📊 최종 분석 결과

**핵심 발견사항**
- [구체적 수치와 함께 주요 발견사항]
- [회계기준 적용 결과]
- [사업 현황 분석 결과]

**결론**
[모든 자료를 종합한 명확하고 구체적인 결론, 실제 수치 포함]

## ⛔ 분석 준수사항
- 실제 문서 내용만 사용 (임의 수치 조합 금지)
- 재무제표 수치는 구체적 금액으로 제시
- 연도별 핵심 변화 위주로 서술
- 불확실한 내용: "관련 자료에서는 해당 정보를 찾을 수 없습니다"
- 1억 원 이상: ~억원 표시 (예: 820억원)
- 제공된 회계기준만 적용
""")



# CoT 방식 재무제표 질문 답변 프롬프트 (수정)
financial_prompt = PromptTemplate.from_template("""
당신은 재무분석 전문가입니다. 실제 API로부터 얻은 재무제표 데이터를 단계별로 분석해주세요.

## 📊 제공된 재무제표 데이터
{financial_data}

## 🔍 분석 과정

**질문 분석**
질문: {question}
- 분석 대상: [어떤 재무항목을 분석해야 하는지]
- 비교 기간: [연도별 비교가 필요한지]

**데이터 확인 및 단위 변환**
- 보유 연도: [데이터에 있는 연도 확인]
- 관련 항목: [질문과 관련된 재무항목 식별]
- 단위 변환된 수치 (KRW → 억원):
  * 2022년: [해당 항목] [KRW 금액을 100000000으로 나눈 억원]
  * 2023년: [해당 항목] [KRW 금액을 100000000으로 나눈 억원]
  * 2024년: [해당 항목] [KRW 금액을 100000000으로 나눈 억원]

**연도별 수치 비교**
- 2022년: [억원 단위로 변환된 수치와 특징]
- 2023년: [억원 단위로 변환된 수치와 전년 대비 변화]
- 2024년: [억원 단위로 변환된 수치와 전년 대비 변화]
- 변화율: [실제 계산된 증감률]

## 📈 최종 분석 결과

**연도별 현황**
- 2022년에는 [항목명]이 [○○,○○○억원]으로 [객관적 서술]
- 2023년에는 [항목명]이 [○○,○○○억원]으로 [객관적 서술]
- 2024년에는 [항목명]이 [○○,○○○억원]으로 [객관적 서술]

**데이터 기반 결론**
[억원 단위로 변환된 수치만을 바탕으로 한 객관적 결론]

## ⛔ 분석 준수사항
- 제공된 재무데이터만 사용
- 모든 KRW 금액을 100000000으로 나누어 억원 단위로 변환
- 억원 단위는 쉼표로 구분하여 가독성 향상 (예: 4,484,245억원)
- 연도별 구분하여 "○○년에는 ~" 형식으로 작성
- 없는 데이터는 해석 금지
- 추측이나 임의 해석 금지
- 실제 수치 반드시 포함
""")


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





