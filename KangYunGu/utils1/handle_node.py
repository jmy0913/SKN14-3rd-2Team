from .normalize_code_search import find_corporation_code, normalize_company_name, parse_extracted_text
from .retreiver_setting import faiss_retriever_loading, preprocess, calculate_bm25
from .api_get import get_financial_state
from .chain_setting import create_chain
import os
from langchain.chat_models import ChatOpenAI

simple_chain, classification_chain, extract_chain,hybrid_chain1, hybrid_chain2, hybrid_chain3,account_chain1, account_chain2, account_chain3,business_chain1, business_chain2, business_chain3, financial_chain1, financial_chain2, financial_chain3 = create_chain()

accounting_retriever, business_retriever, business_retriever2, self_retriever = faiss_retriever_loading()


# 초급 회계 질문 답변 분기 함수
def handle_accounting1(question: str) -> str:
    print("📥 accounting 처리 시작")
    docs = accounting_retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    return account_chain1.invoke({"context": context, "question": question})


# 중급 회계 질문 답변 분기 함수
def handle_accounting2(question: str) -> str:
    print("📥 accounting 처리 시작")
    docs = accounting_retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    return account_chain2.invoke({"context": context, "question": question})

# 고급 회계 질문 답변 분기 함수
def handle_accounting3(question: str) -> str:
    print("📥 accounting 처리 시작")
    docs = accounting_retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    return account_chain3.invoke({"context": context, "question": question})

# 초급 사업보고서 질문 답변 분기 함수
def handle_business1(question: str) -> str:
    print("📥 business 처리 시작")
    # docs = business_retriever.invoke(question)
    # docs = business_retriever2.invoke(question)
    docs = self_retriever.get_relevant_documents(question)
    context = "\n\n".join(doc.page_content for doc in docs)

    return business_chain1.invoke({"context": context, "question": question})

# 중급 사업보고서 질문 답변 분기 함수
def handle_business2(question: str) -> str:
    print("📥 business 처리 시작")
    # docs = business_retriever.invoke(question)
    # docs = business_retriever2.invoke(question)
    docs = self_retriever.get_relevant_documents(question)
    context = "\n\n".join(doc.page_content for doc in docs)

    return business_chain2.invoke({"context": context, "question": question})


# 고급 사업보고서 질문 답변 분기 함수
def handle_business3(question: str) -> str:
    print("📥 business 처리 시작")
    # docs = business_retriever.invoke(question)
    # docs = business_retriever2.invoke(question)
    docs = self_retriever.get_relevant_documents(question)
    context = "\n\n".join(doc.page_content for doc in docs)

    return business_chain3.invoke({"context": context, "question": question})


# 초급 재무제표 질문 답변하는 분기 함수
def handle_financial1(question: str) -> str:
    print("📥 financial 처리 시작")

    # 추출
    extracted_text = extract_chain.invoke({"question": question})
    extracted = parse_extracted_text(extracted_text)

    corp_code = find_corporation_code(extracted["company"])
    years = extracted.get("year_list", ["2024"])

    # 재무제표 연도별 구조화
    fin_blocks = []
    for y in years:
        rows = get_financial_state(corp_code, y, "11011", "CFS")
        if rows:
            fin_blocks.append(f"📅 {y}년 재무제표:\n" + "\n".join(rows))

    structured_financial = "\n\n".join(fin_blocks)

    # 체인 실행
    return financial_chain1.invoke({
        "financial_data": structured_financial,
        "question": question,
        "resolved_corp_name": extracted["company"],
    })


# 중급 재무제표 질문 답변하는 분기 함수
def handle_financial2(question: str) -> str:
    print("📥 financial 처리 시작")

    # 추출
    extracted_text = extract_chain.invoke({"question": question})
    extracted = parse_extracted_text(extracted_text)

    corp_code = find_corporation_code(extracted["company"])
    years = extracted.get("year_list", ["2024"])

    # 재무제표 연도별 구조화
    fin_blocks = []
    for y in years:
        rows = get_financial_state(corp_code, y, "11011", "CFS")
        if rows:
            fin_blocks.append(f"📅 {y}년 재무제표:\n" + "\n".join(rows))

    structured_financial = "\n\n".join(fin_blocks)

    # 체인 실행
    return financial_chain2.invoke({
        "financial_data": structured_financial,
        "question": question,
        "resolved_corp_name": extracted["company"],
    })


# 고급 재무제표 질문 답변하는 분기 함수
def handle_financial3(question: str) -> str:
    print("📥 financial 처리 시작")

    # 추출
    extracted_text = extract_chain.invoke({"question": question})
    extracted = parse_extracted_text(extracted_text)

    corp_code = find_corporation_code(extracted["company"])
    years = extracted.get("year_list", ["2024"])

    # 재무제표 연도별 구조화
    fin_blocks = []
    for y in years:
        rows = get_financial_state(corp_code, y, "11011", "CFS")
        if rows:
            fin_blocks.append(f"📅 {y}년 재무제표:\n" + "\n".join(rows))

    structured_financial = "\n\n".join(fin_blocks)

    # 체인 실행
    return financial_chain3.invoke({
        "financial_data": structured_financial,
        "question": question,
        "resolved_corp_name": extracted["company"],
    })



# 초급 하이브리드 분기 함수
def handle_hybrid1(question: str) -> str:
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

    corp_code = find_corporation_code(extracted["company"])
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
    return hybrid_chain1.invoke({
        "question": question,
        "acct": acct_context,
        "biz": biz_context,
        "fin": "\n\n".join(financials)
    })


# 중급 하이브리드 분기 함수
def handle_hybrid2(question: str) -> str:
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

    corp_code = find_corporation_code(extracted["company"])
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
    return hybrid_chain2.invoke({
        "question": question,
        "acct": acct_context,
        "biz": biz_context,
        "fin": "\n\n".join(financials)
    })

# 고급 하이브리드 분기 함수
def handle_hybrid3(question: str) -> str:
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

    corp_code = find_corporation_code(extracted["company"])
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
    return hybrid_chain3.invoke({
        "question": question,
        "acct": acct_context,
        "biz": biz_context,
        "fin": "\n\n".join(financials)
    })


# 일반 질문 분기함수
def elief(question: str) -> str:
    print("일반 질문")
    return simple_chain.invoke({"question":{question}})