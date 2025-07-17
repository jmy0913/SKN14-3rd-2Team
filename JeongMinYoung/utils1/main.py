from .handle_node import (handle_accounting1, handle_accounting2, handle_accounting3,
                          handle_business1, handle_business2, handle_business3,
                          handle_financial1, handle_financial2, handle_financial3,
                          handle_hybrid1, handle_hybrid2, handle_hybrid3, elief)
from .chain_setting import create_chain
import os

simple_chain, classification_chain, extract_chain,hybrid_chain1, hybrid_chain2, hybrid_chain3,account_chain1, account_chain2, account_chain3,business_chain1, business_chain2, business_chain3, financial_chain1, financial_chain2, financial_chain3 = create_chain()

# 초급 전체 분기 실행 함수
def run_flexible_rag1(question: str) -> str:
    type_output = classification_chain.invoke({"question": question}).strip().lower()

    # '작업유형:' 파싱
    type_result = None
    if "작업유형:" in type_output:
        type_result = type_output.split("작업유형:")[-1].strip()
    else:
        type_result = type_output  # 혹시 몰라 fallback

    if type_result == "accounting":
        return handle_accounting1(question)
    elif type_result == "hybrid":
        return handle_hybrid1(question)
    elif type_result == "finance":
        return handle_financial1(question)
    elif type_result == "business":
        return handle_business1(question)
    elif type_result == "else":
        return elief(question)
    else:
        return f"❗질문의 유형을 정확히 분류할 수 없습니다.\n(모델 응답: {type_output})"


# 중급 전체 분기 실행 함수
def run_flexible_rag2(question: str) -> str:
    type_output = classification_chain.invoke({"question": question}).strip().lower()

    # '작업유형:' 파싱
    type_result = None
    if "작업유형:" in type_output:
        type_result = type_output.split("작업유형:")[-1].strip()
    else:
        type_result = type_output  # 혹시 몰라 fallback

    if type_result == "accounting":
        return handle_accounting2(question)
    elif type_result == "hybrid":
        return handle_hybrid2(question)
    elif type_result == "finance":
        return handle_financial2(question)
    elif type_result == "business":
        return handle_business2(question)
    elif type_result == "else":
        return elief(question)
    else:
        return f"❗질문의 유형을 정확히 분류할 수 없습니다.\n(모델 응답: {type_output})"


# 고급 전체 분기 실행 함수
def run_flexible_rag3(question: str) -> str:
    type_output = classification_chain.invoke({"question": question}).strip().lower()

    # '작업유형:' 파싱
    type_result = None
    if "작업유형:" in type_output:
        type_result = type_output.split("작업유형:")[-1].strip()
    else:
        type_result = type_output  # 혹시 몰라 fallback

    if type_result == "accounting":
        return handle_accounting3(question)
    elif type_result == "hybrid":
        return handle_hybrid3(question)
    elif type_result == "finance":
        return handle_financial3(question)
    elif type_result == "business":
        return handle_business3(question)
    elif type_result == "else":
        return elief(question)
    else:
        return f"❗질문의 유형을 정확히 분류할 수 없습니다.\n(모델 응답: {type_output})"
