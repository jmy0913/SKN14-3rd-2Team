# import OpenDartReader
# import os
# from dotenv import load_dotenv

# def fetch_and_print_financial_statements():
#     # 환경변수 및 API 키 로드
#     load_dotenv()
#     api_key = os.getenv('DART_API_KEY')
#     dart = OpenDartReader(api_key)

#     # 회사명-종목코드 매핑
#     company_map = {
#         '삼성전자': '005930',
#         'SK하이닉스': '000660',
#         'LG에너지솔루션': '373220',
#         '삼성바이오로직스': '207940',
#         'KB금융': '105560',
#         '현대차': '005380',
#         '기아': '000270',
#         'NAVER': '035420',
#         '한화에어로스페이스': '012450',
#         'HD현대중공업': '329180',
#         '신한지주': '055550',
#         '삼성물산': '028260',
#         '현대모비스': '012330',
#         '하나금융지주': '086790',
#         '카카오': '035720',
#         '삼성생명': '032830',
#         'HMM': '011200'
#     }

#     # 반드시 포함: 사업보고서(연간) 코드
#     REPORT_CODE = '11011'  # 사업보고서(연간)

#     def get_financial_statement(company_name, year):
#         corp_code = company_map[company_name]
#         fs = dart.finstate(corp_code, year, REPORT_CODE)
#         if fs is not None and len(fs) > 0:
#             cfs = fs[fs['fs_div'] == 'CFS']
#             if len(cfs) > 0:
#                 return cfs
#             ofs = fs[fs['fs_div'] == 'OFS']
#             return ofs if len(ofs) > 0 else fs
#         return None

#     for company in company_map:
#         for year in [2022, 2023, 2024]:
#             fs = get_financial_statement(company, year)
#             print(f"{company} {year}년 재무제표:")
#             print(fs)

# # 함수 실행 예시
# if __name__ == "__main__":
#     fetch_and_print_financial_statements()
# dart_api.py
import OpenDartReader
import os
from dotenv import load_dotenv

# LangChain Document 객체가 없다면 아래처럼 정의해도 무방합니다
class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

def fetch_financial_docs_from_dart(company="삼성전자", year=2023):
    load_dotenv()
    api_key = os.getenv('DART_API_KEY')
    dart = OpenDartReader(api_key)
    company_map = {
        '삼성전자': '005930', 'SK하이닉스': '000660',
        # ...(중략)
    }
    REPORT_CODE = '11011'
    corp_code = company_map.get(company)
    if corp_code is None:
        return []
    fs = dart.finstate(corp_code, year, REPORT_CODE)
    if fs is not None and len(fs) > 0:
        cfs = fs[fs['fs_div'] == 'CFS']
        if len(cfs) == 0:
            cfs = fs
        text = cfs.to_string(index=False)
        return [Document(page_content=text, metadata={'company': company, 'year': year})]
    return []
