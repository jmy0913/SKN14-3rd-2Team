from .handle_node import handle_accounting, handle_business, handle_financial, handle_hybrid, elief
from .chain_setting import create_chain

simple_chain, classification_chain, account_chain, extract_chain, business_chain, hybrid_chain, financial_chain = create_chain()



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
