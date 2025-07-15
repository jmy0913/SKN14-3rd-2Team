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

# Python built-in
from difflib import get_close_matches

# Load environment variables
load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
faiss_path1 = os.path.join(current_dir, "faiss_index3")
faiss_path2 = os.path.join(current_dir, "faiss_index_bge_m3")

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

# 회계기준서 벡터 db
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

# llm 설정
simple_llm = ChatOpenAI(
    model = 'gpt-4o-mini',
    temperature=0
)

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


classification_chain = classification_prompt | simple_llm | StrOutputParser()

# 회계 질문 답변 프롬프트
accounting_prompt = PromptTemplate.from_template(
    """다음 회계 기준서 내용만을 바탕으로 질문에 답변해주고, 다른 내용으로 추론하거나 답변하지 마세요.

회계 기준서:
{context}

질문:
{question}
"""
)


account_chain = accounting_prompt | simple_llm | StrOutputParser()

# 일반 질문 답변 프롬프트
simple_prompt = PromptTemplate.from_template("""
사용자의 질문에 대해서 아래와 같이 답변해주세요.
답변: 해당 내용은 제가 알지 못하는 분야입니다.
질문: {question}
""")

simple_chain = simple_prompt | simple_llm | StrOutputParser()


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

# 추출 LLM 체인
extract_chain = extract_prompt | simple_llm | StrOutputParser()


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


business_chain = business_prompt | simple_llm | StrOutputParser()

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


hybrid_chain = (
    hybrid_prompt |
    simple_llm |
    StrOutputParser()
)

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

financial_chain = (
    financial_prompt
    | simple_llm
    | StrOutputParser()
)


# 입력된 회사명을 corp_list에 있는 회사명 중 가장 유사한 회사명으로 정규화
def normalize_company_name(user_input: str, corp_list: list[dict]) -> str:
    # 입력 정규화
    user_input_norm = user_input.strip().lower().replace("(주)", "").replace("주식회사", "").replace(" ", "")

    # corp_name과 corp_eng_name 둘 다 비교 대상으로 만듦
    all_names = []
    mapping = {}

    for corp in corp_list:
        kor = corp["corp_name"]
        eng = corp["corp_eng_name"]

        kor_norm = kor.lower().replace("(주)", "").replace("주식회사", "").replace(" ", "")
        eng_norm = eng.lower().replace("(주)", "").replace("co.,ltd.", "").replace(",", "").replace(" ", "")

        # 각 이름을 매핑 테이블에 저장
        all_names.extend([kor_norm, eng_norm])
        mapping[kor_norm] = kor
        mapping[eng_norm] = kor  # 반환은 항상 kor 기준

    # 유사한 이름 찾기
    matches = get_close_matches(user_input_norm, all_names, n=1, cutoff=0.6)
    if matches:
        matched = matches[0]
        return mapping[matched]

    return None


# 회사명으로 회사코드 가져오는 함수
@tool
def find_corporation_code(company_name: str) -> str:
    """
    사용자가 입력한 기업명을 기반으로 DART 기업코드를 반환합니다.
    유사한 기업명도 자동 정규화하여 검색합니다.
    """
    company_name = company_name.strip("'\"")

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'corp_list.json')

        with open(file_path, encoding='utf-8') as f:
            corp_list = json.load(f)

    except Exception as e:
        return f"[ERROR] corp_list.json 로드 실패: {str(e)}"

    # Step 1: 정규화된 이름 찾기
    normalized_name = normalize_company_name(company_name, corp_list)
    if not normalized_name:
        return f"[ERROR] '{company_name}'에 유사한 기업명을 찾을 수 없습니다."

    # Step 2: 기업 코드 반환
    for corp in corp_list:
        if corp["corp_name"] == normalized_name:
            return corp["corp_code"]

    return f"[ERROR] '{normalized_name}'에 해당하는 기업 코드를 찾을 수 없습니다."


# extract chain이 준 응답에서 회사명과 연도 추출하는 함수
def parse_extracted_text(text: str) -> dict:
    company_match = re.search(r"회사\s*:\s*(.+)", text)
    year_match = re.search(r"연도\s*:\s*(\d{4}(?:,\s*\d{4})*)", text)  # 여러 연도 대응 가능

    company = company_match.group(1).strip() if company_match else None
    year_str = year_match.group(1) if year_match else "2024"
    years = [y.strip() for y in year_str.split(",")]

    return {
        "company": company,
        "year_list": years
    }


# 제무재표 api로 받아오는 함수
def get_financial_state(
    corp_code: str,
    bsns_year: str,
    reprt_code: str,
    fs_div: str
) -> list[str]:
    """
    단일 기업의 단일 회계연도에 대한 재무제표 항목을 조회하는 도구입니다.

    Parameters:
    - corp_code: DART에서 제공하는 기업 고유 코드 (예: "00126380" for 삼성전자)
    - bsns_year: 사업 연도 (예: "2023")
    - reprt_code: 보고서 코드 (예: "11011" = 사업보고서)
        * 1분기: 11013, 반기: 11012, 3분기: 11014, 사업보고서: 11011
    - fs_div: 재무제표 구분 ("CFS" = 연결, "OFS" = 별도)

    Returns:
    - 각 항목별로 "계정명 : 당기 금액, 전기 금액, 통화" 형식의 문자열 리스트

    💡 이 함수는 하나의 연도만 조회합니다.
       따라서 여러 연도(예: 2022, 2023, 2024)의 정보를 원할 경우,
       이 Tool을 연도별로 여러 번 호출해야 합니다.
    """

    DART_API_KEY = os.getenv("DART_API_KEY")

    url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code,
        "fs_div": fs_div,
    }


    response = requests.get(url, params=params)
    data = response.json()

    data_list = []

    if data["status"] == "000":
        for item in data["list"]:
            name = item["account_nm"]
            curr = item["thstrm_amount"]
            prev = item.get("frmtrm_amount", "-")
            currency = item.get("currency", "KRW")
            data_list.append(f"{name} : {curr} (당기), {prev} (전기), 통화: {currency}")
        return data_list
    else:
        return [f"[API 오류] {data.get('message', '정의되지 않은 오류')}"]


# 회계 질문 답변 분기 함수
def handle_accounting(question: str) -> str:
    print("📥 accounting 처리 시작")
    docs = accounting_retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    return account_chain.invoke({"context": context, "question": question})

# 사업보고서 질문 답변 분기 함수
def handle_business(question: str) -> str:
    print("📥 business 처리 시작")
    docs = business_retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)

    return business_chain.invoke({"context": context, "question": question})


# 재무제표 질문 답변하는 분기 함수
def handle_financial(question: str) -> str:
    print("📥 financial 처리 시작")

    # 추출
    extracted_text = extract_chain.invoke({"question": question})
    extracted = parse_extracted_text(extracted_text)

    corp_code = find_corporation_code.invoke(extracted["company"])
    years = extracted.get("year_list", ["2024"])

    # 재무제표 연도별 구조화
    fin_blocks = []
    for y in years:
        rows = get_financial_state(corp_code, y, "11011", "CFS")
        if rows:
            fin_blocks.append(f"📅 {y}년 재무제표:\n" + "\n".join(rows))

    structured_financial = "\n\n".join(fin_blocks)

    # 체인 실행
    return financial_chain.invoke({
        "financial_data": structured_financial,
        "question": question
    })


# 하이브리드 분기 함수
def handle_hybrid(question: str) -> str:
    print("📥 hybrid 처리 시작")

    # 고정 재무제표 수집 함수 (CFS + 사업보고서만)
    def try_get_financial_strict(corp_code: str, year: str) -> str:
        rows = get_financial_state(corp_code, year, "11011", "CFS")
        if rows and "[API 오류]" not in rows[0]:
            return f"📅 {year}년 (CFS, 사업보고서):\n" + "\n".join(rows)
        return f"📅 {year}년 재무제표: 유효한 데이터를 찾을 수 없습니다."

    # 1. 회사명 및 연도 추출
    extracted_text = extract_chain.invoke({"question": question})
    extracted = parse_extracted_text(extracted_text)

    corp_code = find_corporation_code.invoke(extracted["company"])
    years = extracted.get("year_list", ["2024"])

    # 2. 재무제표 수집
    financials = [try_get_financial_strict(corp_code, y) for y in years]

    # 3. 회계 기준서 검색
    acct_docs = accounting_retriever.invoke(question)
    acct_context = "\n\n".join(doc.page_content for doc in acct_docs) if acct_docs else "관련 회계 기준서를 찾을 수 없습니다."

    # 4. 사업보고서 검색
    biz_docs = business_retriever.invoke(question)
    biz_context = "\n\n".join(doc.page_content for doc in biz_docs) if biz_docs else "관련 사업보고서를 찾을 수 없습니다."

    # 5. Hybrid 체인 실행
    return hybrid_chain.invoke({
        "question": question,
        "acct": acct_context,
        "biz": biz_context,
        "fin": "\n\n".join(financials)
    })

# 일반 질문 분기함수
def elief(question: str) -> str:
    print("일반 질문")
    return simple_chain.invoke({"question":{question}})

# 전체 분기 실행 함수
def run_flexible_rag(question: str) -> str:
    type_output = classification_chain.invoke({"question": question}).strip().lower()

    # '작업유형:' 파싱
    type_result = None
    if "작업유형:" in type_output:
        type_result = type_output.split("작업유형:")[-1].strip()
    else:
        type_result = type_output  # 혹시 몰라 fallback

    if type_result == "accounting":
        return handle_accounting(question)
    elif type_result == "hybrid":
        return handle_hybrid(question)
    elif type_result == "finance":
        return handle_financial(question)
    elif type_result == "business":
        return handle_business(question)
    elif type_result == "else":
        return elief(question)
    else:
        return f"❗질문의 유형을 정확히 분류할 수 없습니다.\n(모델 응답: {type_output})"

