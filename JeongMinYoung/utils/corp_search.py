import os
import json
import requests
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()



# 기업 코드 조회 함수
@tool
def find_corp_code(company_name: str) -> str:
    """
    :param company_name:
    :return: company_code
    """
    company_name = company_name.strip("'\"")  # 작은따옴표, 큰따옴표 모두 제거
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'corp_list.json')

        with open(file_path, encoding='utf-8') as f:
            corp_list = json.load(f)

    except Exception as e:
        return f"[ERROR] corp_list.json 로드 실패: {str(e)}"

    for corp in corp_list:
        if corp["corp_name"] == company_name:
            return corp["corp_code"]

    return f"'{company_name}'을 찾을 수 없습니다."



corp_code = find_corp_code('삼성전자')
print(corp_code)

# 재무제표 조회 API 호출용 함수 (Agent에서는 직접 사용하지 않음)
def get_financial_statement(
    corp_code: str,
    bsns_year: str,
    reprt_code: str,
    fs_div: str
) -> list[str]:
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


# Agent용 Tool 래퍼 함수
@tool
def get_financial_statement_wrapper(input_str: str) -> str:
    """
    LangChain Agent가 문자열 입력으로 재무제표를 조회할 수 있도록 래핑된 도구입니다.
    입력 예시: "00126380,2023"
    """
    try:
        parts = [s.strip().replace("'", "") for s in input_str.strip("()").split(",")]
        if len(parts) != 2:
            return "[ERROR] '기업코드, 연도' 형태로 입력해주세요. 예: '005930, 2023'"

        corp_code, bsns_year = parts

        result_lines = get_financial_statement(
            corp_code=corp_code,
            bsns_year=bsns_year,
            reprt_code="11011",  # 사업보고서
            fs_div="OFS"         # 연결재무제표
        )
        return "\n".join(result_lines)

    except Exception as e:
        return f"[ERROR] 재무제표 조회 중 오류 발생: {str(e)}"
