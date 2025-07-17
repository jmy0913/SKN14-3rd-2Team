# ADD by EUIRYEONG
from typing import List, Dict
import os
import zipfile
import requests
import uuid
import openai
import re

from langchain_core.documents import Document
import pandas as pd
import xml.etree.ElementTree as ET

from src.config import DART_API_KEY, RAG_DOCUMENTS_FOLDER_NAME, FINANCIAL_REPORTS_FOLDER_NAME

import dart_fss as dfs


CORP_CODE_FILE_NAME = 'corpCode.zip'
ELEMENT_TREE_NAME = 'CORPCODE.xml'
URL_CORP_CODE = f'https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_API_KEY}'
URL_FINANCIAL_STATE = 'https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json'
URL_BUSINESS_REPORT = 'https://opendart.fss.or.kr/api/document.json'
FINANCIAL_CODE = '11011'
YEAR = 2022

CORP_CODE = 'corp_code'
CORP_NAME = 'corp_name'
FILE_SUFFIX_FINANCIAL_STATE = '재무제표'
FILE_EXTENSION_CSV = '.csv'

class DocumentSaver:
    def __init__(self):
        pass

    def get_corp_code_list(self):
        try:
            url = URL_CORP_CODE
            response = requests.get(url)
            response.raise_for_status()
            with open(CORP_CODE_FILE_NAME, 'wb') as f:
                f.write(response.content)

            with zipfile.ZipFile(CORP_CODE_FILE_NAME, 'r') as zip_ref:
                zip_ref.extractall('.')

            tree = ET.parse(ELEMENT_TREE_NAME)
            root = tree.getroot()

            corp_list = []
            for child in root.findall('list'):
                corp_list.append({
                    CORP_CODE: child.find(CORP_CODE).text,
                    CORP_NAME: child.find(CORP_NAME).text,
                })

            return corp_list
        
        except Exception as e:
            print(f"[ERROR] 기업코드 리스트 가져오기 실패: {e}")
            return []
        
    def filter_corp_codes_by_name(self, target_names: List[str] = None) -> List[Dict[str, str]]:
        if target_names is None : 
            target_names = [
                "삼성전자",
                "SK하이닉스",
                "삼성바이오로직스",
                "LG에너지솔루션",
                "KB금융",
                "현대차",
                "기아",
                "NAVER",
                "셀트리온",
                "두산에너빌리티",
                "한화에어로스페이스",
                "신한지주",
                "HD현대중공업",
                "삼성물산",
                "현대모비스",
                "삼성생명",
                "하나금융지주",
                "HMM",
                "POSCO홀딩스",
                "LG화학",
            ]

        full_list = self.get_corp_code_list()
        filtered_dict = [item for item in full_list if item[CORP_NAME] in target_names]

        return filtered_dict

    def get_business_report_sections(self, corp_name: str, year: int) -> List[Document]:
        """사업보고서의 주요 정보들을 DART API의 다양한 엔드포인트에서 가져오는 함수"""
        try:
            print(f"[INFO] {corp_name} {year}년 사업보고서 정보 가져오기 시작")
            
            # 기업 코드 찾기
            corp_list = self.get_corp_code_list()
            corp_info = None
            for corp in corp_list:
                if corp[CORP_NAME] == corp_name:
                    corp_info = corp
                    break
            
            if not corp_info:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            corp_code = corp_info[CORP_CODE]
            print(f"[INFO] {corp_name} 기업 코드: {corp_code}")
            
            documents = []
            
            # 1. 정기보고서 주요정보 가져오기
            try:
                print("[INFO] 정기보고서 주요정보 가져오기")
                url = "https://opendart.fss.or.kr/api/alotMatter.json"
                params = {
                    'crtfc_key': DART_API_KEY,
                    'corp_code': corp_code,
                    'bsns_year': str(year),
                    'reprt_code': '11011'  # 사업보고서
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'list' in data and data['list']:
                    for item in data['list']:
                        content = f"""
                            {corp_name} {year}년 주요사항
                            항목: {item.get('se', '')}
                            당기: {item.get('thstrm', '')}
                            전기: {item.get('frmtrm', '')}
                            전전기: {item.get('lwfr', '')}
                        """.strip()
                        
                        documents.append(Document(
                            page_content=content,
                            metadata={
                                "corp_name": str(corp_name),
                                "corp_code": str(corp_code),
                                "year": str(year),
                                "section": "주요사항",
                                "source": "business_report",
                                "content_type": "key_matters"
                            }
                        ))
                    print(f"[SUCCESS] 주요사항 {len(data['list'])}개 처리 완료")
                else:
                    print(f"[INFO] 주요사항 데이터 없음")
            except Exception as e:
                print(f"[WARNING] 주요사항 가져오기 실패: {e}")
            
            # 2. 배당에 관한 사항 가져오기
            try:
                print("[INFO] 배당에 관한 사항 가져오기")
                url = "https://opendart.fss.or.kr/api/alotMatter.json"
                params = {
                    'crtfc_key': DART_API_KEY,
                    'corp_code': corp_code,
                    'bsns_year': str(year),
                    'reprt_code': '11011'
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'list' in data and data['list']:
                    dividend_items = [item for item in data['list'] if '배당' in item.get('se', '')]
                    for item in dividend_items:
                        content = f"""
{corp_name} {year}년 배당 정보
항목: {item.get('se', '')}
당기: {item.get('thstrm', '')}
전기: {item.get('frmtrm', '')}
전전기: {item.get('lwfr', '')}
                        """.strip()
                        
                        documents.append(Document(
                            page_content=content,
                            metadata={
                                "corp_name": str(corp_name),
                                "corp_code": str(corp_code),
                                "year": str(year),
                                "section": "배당에 관한 사항",
                                "source": "business_report",
                                "content_type": "dividend"
                            }
                        ))
                    print(f"[SUCCESS] 배당 정보 {len(dividend_items)}개 처리 완료")
            except Exception as e:
                print(f"[WARNING] 배당 정보 가져오기 실패: {e}")
            
            # 3. 임직원 현황 가져오기 (다른 API 사용)
            try:
                print("[INFO] 임직원 현황 가져오기")
                url = "https://opendart.fss.or.kr/api/empSttus.json"
                params = {
                    'crtfc_key': DART_API_KEY,
                    'corp_code': corp_code,
                    'bsns_year': str(year),
                    'reprt_code': '11011'
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'list' in data and data['list']:
                    for item in data['list']:
                        content = f"""
                            {corp_name} {year}년 임직원 현황
                            부문: {item.get('fo_bbm', '')}
                            성별: {item.get('sexdstn', '')}
                            정규직: {item.get('rgllbr_co', '')}명
                            계약직: {item.get('cnttk_co', '')}명
                            합계: {item.get('sm', '')}명
                            평균근속연수: {item.get('avrg_cnwk_sdytrn', '')}년
                        """.strip()
                        
                        documents.append(Document(
                            page_content=content,
                            metadata={
                                "corp_name": str(corp_name),
                                "corp_code": str(corp_code),
                                "year": str(year),
                                "section": "임직원 현황",
                                "source": "business_report",
                                "content_type": "employee_status"
                            }
                        ))
                    print(f"[SUCCESS] 임직원 현황 {len(data['list'])}개 처리 완료")
                else:
                    print(f"[INFO] 임직원 현황 데이터 없음")
            except Exception as e:
                print(f"[WARNING] 임직원 현황 가져오기 실패: {e}")
            
            # 4. 주주현황 가져오기
            try:
                print("[INFO] 주주현황 가져오기")
                url = "https://opendart.fss.or.kr/api/hyslrSttus.json"
                params = {
                    'crtfc_key': DART_API_KEY,
                    'corp_code': corp_code,
                    'bsns_year': str(year),
                    'reprt_code': '11011'
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'list' in data and data['list']:
                    for item in data['list']:
                        content = f"""
                            {corp_name} {year}년 주주현황
                            주주명: {item.get('nm', '')}
                            관계: {item.get('relate', '')}
                            기초 보유주식수: {item.get('bsis_posesn_stock_co', '')}
                            기초 지분율: {item.get('bsis_posesn_stock_qota_rt', '')}%
                            기말 보유주식수: {item.get('trmend_posesn_stock_co', '')}
                            기말 지분율: {item.get('trmend_posesn_stock_qota_rt', '')}%
                            비고: {item.get('rm', '')}
                        """.strip()
                        
                        documents.append(Document(
                            page_content=content,
                            metadata={
                                "corp_name": str(corp_name),
                                "corp_code": str(corp_code),
                                "year": str(year),
                                "section": "주주현황",
                                "source": "business_report",
                                "content_type": "shareholder_status"
                            }
                        ))
                    print(f"[SUCCESS] 주주현황 {len(data['list'])}개 처리 완료")
                else:
                    print(f"[INFO] 주주현황 데이터 없음")
            except Exception as e:
                print(f"[WARNING] 주주현황 가져오기 실패: {e}")
            
            # 5. 최대주주현황 가져오기
            try:
                print("[INFO] 최대주주현황 가져오기")
                url = "https://opendart.fss.or.kr/api/mrhlSttus.json"
                params = {
                    'crtfc_key': DART_API_KEY,
                    'corp_code': corp_code,
                    'bsns_year': str(year),
                    'reprt_code': '11011'
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'list' in data and data['list']:
                    for item in data['list']:
                        content = f"""
                            {corp_name} {year}년 최대주주현황
                            구분: {item.get('se', '')}
                            주주수: {item.get('shrholdr_co', '')}
                            전체주주수: {item.get('shrholdr_tot_co', '')}
                            주주비율: {item.get('shrholdr_rate', '')}%
                            보유주식수: {item.get('hold_stock_co', '')}
                            전체주식수: {item.get('stock_tot_co', '')}
                            지분율: {item.get('hold_stock_rate', '')}%
                        """.strip()
                        
                        documents.append(Document(
                            page_content=content,
                            metadata={
                                "corp_name": str(corp_name),
                                "corp_code": str(corp_code),
                                "year": str(year),
                                "section": "최대주주현황",
                                "source": "business_report",
                                "content_type": "major_shareholder"
                            }
                        ))
                    print(f"[SUCCESS] 최대주주현황 {len(data['list'])}개 처리 완료")
                else:
                    print(f"[INFO] 최대주주현황 데이터 없음")
            except Exception as e:
                print(f"[WARNING] 최대주주현황 가져오기 실패: {e}")
            
            # 6. 기업개요 정보 생성
            try:
                print("[INFO] 기업개요 정보 생성")
                content = f"""
                    {corp_name} 기업개요 ({year}년 기준)
                    기업명: {corp_name}
                    기업코드: {corp_code}
                    연도: {year}년
                    주요 사업: 전자제품 제조 및 판매
                    사업분야: 반도체, 디스플레이, 모바일 등
                """.strip()
                
                documents.append(Document(
                    page_content=content,
                    metadata={
                        "corp_name": str(corp_name),
                        "corp_code": str(corp_code),
                        "year": str(year),
                        "section": "기업개요",
                        "source": "business_report",
                        "content_type": "company_overview"
                    }
                ))
                print(f"[SUCCESS] 기업개요 정보 생성 완료")
            except Exception as e:
                print(f"[WARNING] 기업개요 정보 생성 실패: {e}")
            
            print(f"[SUCCESS] 총 {len(documents)}개 사업보고서 관련 문서 생성 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 사업보고서 섹션 가져오기 실패: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_section_content(self, content: str, section_name: str) -> str:
        """사업보고서 내용에서 특정 섹션을 추출하는 함수"""
        try:
            # 다양한 섹션 제목 패턴 (더 포괄적으로)
            patterns = [
                rf"【{re.escape(section_name)}】",
                rf"\[{re.escape(section_name)}\]",
                rf"\({re.escape(section_name)}\)",
                rf"제\s*\d+\s*장\s*{re.escape(section_name)}",
                rf"제\s*\d+\s*절\s*{re.escape(section_name)}",
                rf"{re.escape(section_name)}에\s*관한\s*사항",
                rf"{re.escape(section_name)}에\s*관한\s*사항들",
                rf"{re.escape(section_name)}",
                rf"{re.escape(section_name)}.*",
                # 숫자로 시작하는 경우
                rf"\d+\.\s*{re.escape(section_name)}",
                rf"\d+\)\s*{re.escape(section_name)}",
                # 영문 섹션명도 포함
                rf"{re.escape(section_name.upper())}",
                rf"{re.escape(section_name.lower())}",
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    start_pos = match.start()
                    
                    # 섹션 시작부터 다음 섹션까지 추출
                    # 더 포괄적인 다음 섹션 패턴
                    next_section_patterns = [
                        r"【[^】]+】",
                        r"\[[^\]]+\]",
                        r"제\s*\d+\s*장",
                        r"제\s*\d+\s*절",
                        r"\d+\.\s*[가-힣]+",
                        r"\d+\)\s*[가-힣]+",
                        r"【[^】]*】",
                        r"\[[^\]]*\]"
                    ]
                    
                    next_match = None
                    min_distance = float('inf')
                    
                    for next_pattern in next_section_patterns:
                        temp_match = re.search(next_pattern, content[start_pos + 1:])
                        if temp_match and temp_match.start() < min_distance:
                            next_match = temp_match
                            min_distance = temp_match.start()
                    
                    if next_match and min_distance < 10000:  # 너무 멀리 있는 섹션은 제외
                        end_pos = start_pos + 1 + next_match.start()
                        section_content = content[start_pos:end_pos].strip()
                    else:
                        # 다음 섹션이 없으면 적절한 길이로 제한
                        section_content = content[start_pos:start_pos + 15000].strip()  # 최대 15000자
                    
                    # 섹션 제목 제거하고 내용만 반환
                    lines = section_content.split('\n')
                    if len(lines) > 1:
                        # 첫 번째 줄(제목) 제거하고 정리
                        content_lines = lines[1:]
                        cleaned_content = '\n'.join(content_lines).strip()
                        
                        # 너무 짧은 내용은 제외
                        if len(cleaned_content) > 50:
                            return cleaned_content
                    else:
                        # 한 줄인 경우에도 최소 길이 확인
                        if len(section_content) > 50:
                            return section_content
            
            return ""
            
        except Exception as e:
            print(f"[ERROR] 섹션 추출 중 오류: {e}")
            return ""

    def save_financial_reports_document(
            self, 
            filtered_dict: List[dict], 
            save_dir: str = os.path.join(RAG_DOCUMENTS_FOLDER_NAME, FINANCIAL_REPORTS_FOLDER_NAME)
        ) -> List[Document]:
        
        os.makedirs(save_dir, exist_ok=True)
        saved_documents = []
        for corp in filtered_dict:
            corp_code = corp[CORP_CODE]
            corp_name = corp[CORP_NAME]

            url = (
                f"{URL_FINANCIAL_STATE}"
                f"?crtfc_key={DART_API_KEY}"
                f"&corp_code={corp_code}"
                f"&bsns_year={str(YEAR)}"
                f"&reprt_code={FINANCIAL_CODE}"
                f"&fs_div=CFS"
            )
            resp = requests.get(url)
            data = resp.json()

            if data.get('status') == '013':  # 데이터 없음
                print(f"[INFO] {corp_name} - 해당 연도의 사업보고서가 없습니다.")
                continue

            if 'list' not in data:
                print(f"[WARNING] {corp_name} - 재무정보 없음 또는 응답 이상")
                continue

            df = pd.DataFrame(data['list'])
            
            filename = f"{corp_name}_{str(YEAR)}_{FILE_SUFFIX_FINANCIAL_STATE}{FILE_EXTENSION_CSV}"
            file_path = os.path.join(save_dir, filename)
            df.to_csv(file_path, index=False, encoding='utf-8-sig') 

            # Document로 변환 (예: 파일 내용 일부나 요약 가능)
            content = df.to_string()
            saved_documents.append(Document(page_content=content, metadata={"corp_name": corp_name, "year": YEAR, "file_path": file_path}))

        return saved_documents

    def create_documents_for_corp(self, corp_name: str, year: int) -> List[Document]:
        """기업의 재무제표와 사업보고서 섹션들을 모두 가져오는 통합 함수"""
        try:
            print(f"[INFO] {corp_name} {year}년 문서 생성 시작")
            
            all_documents = []
            
            # 1. 재무제표 데이터 가져오기 (기존 CSV 파일 사용)
            print(f"[INFO] 재무제표 데이터 가져오기 시작")
            financial_docs = self.create_documents_from_existing_csv(corp_name, year)
            all_documents.extend(financial_docs)
            print(f"[INFO] 재무제표 문서 {len(financial_docs)}개 추가")
            
            # 2. 사업보고서 섹션들 가져오기 (새로운 API 사용)
            print(f"[INFO] 사업보고서 섹션 가져오기 시작")
            business_docs = self.get_business_report_sections(corp_name, year)
            all_documents.extend(business_docs)
            print(f"[INFO] 사업보고서 섹션 문서 {len(business_docs)}개 추가")
            
            print(f"[SUCCESS] 총 {len(all_documents)}개 문서 생성 완료")
            return all_documents
            
        except Exception as e:
            print(f"[ERROR] create_documents_for_corp 실행 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return []

    def create_documents_from_existing_csv(self, corp_name: str, year: int) -> List[Document]:
        """기존 CSV 파일에서 문서 생성 (DART API 실패 시 대안)"""
        try:
            # CSV 파일 경로
            csv_filename = f"{corp_name}_{str(year)}_재무제표.csv"
            csv_path = os.path.join(RAG_DOCUMENTS_FOLDER_NAME, FINANCIAL_REPORTS_FOLDER_NAME, csv_filename)
            
            if not os.path.exists(csv_path):
                print(f"[ERROR] CSV 파일을 찾을 수 없습니다: {csv_path}")
                return []
            
            # CSV 파일 읽기
            df = pd.read_csv(csv_path)
            print(f"[INFO] CSV 파일 로드 완료: {len(df)}행")
            
            # 주요 재무 지표 추출
            documents = []
            
            # 재무상태표 주요 항목 (더 포괄적으로)
            bs_items = [
                "자산총계", "부채총계", "자본총계", 
                "유동자산", "비유동자산", "유동부채", "비유동부채",
                "현금및현금성자산", "매출채권", "재고자산", "유형자산", "무형자산",
                "단기차입금", "장기차입금", "사채", "이익잉여금", "자본금"
            ]
            
            # 손익계산서 주요 항목
            is_items = [
                "영업수익", "영업이익", "당기순이익", "매출원가", "판매비와관리비",
                "매출총이익", "영업손실", "법인세비용", "기본주당이익", "희석주당이익"
            ]
            
            # 현금흐름표 주요 항목
            cf_items = [
                "영업활동현금흐름", "투자활동현금흐름", "재무활동현금흐름",
                "현금및현금성자산의순증감", "기초현금및현금성자산", "기말현금및현금성자산"
            ]
            
            all_items = bs_items + is_items + cf_items
            
            for item in all_items:
                # 해당 항목이 있는 행 찾기
                matching_rows = df[df['account_nm'].str.contains(item, na=False)]
                if not matching_rows.empty:
                    row = matching_rows.iloc[0]
                    
                    # 더 상세한 재무 정보 생성
                    content = f"""
                        {corp_name} {year}년 {item}
                        - 금액: {row['thstrm_amount']}원
                        - 기간: 제{row['thstrm_nm']}
                        - 이전년도: {row['frmtrm_amount']}원 (제{row['frmtrm_nm']})
                        - 전전년도: {row['bfefrmtrm_amount']}원 (제{row['bfefrmtrm_nm']})
                        - 통화: {row['currency']}
                        - 계정과목: {row['account_nm']}
                        - 계정코드: {row['account_id']}
                                            """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(row.get('corp_code', '')),
                            "year": str(year),
                            "section": "재무지표",
                            "category": "재무제표",
                            "item": str(item),
                            "source": "csv",
                            "rcept_no": str(row.get('rcept_no', '')),
                            "currency": str(row.get('currency', 'KRW')),
                            "account_id": str(row.get('account_id', '')),
                            "account_nm": str(row.get('account_nm', ''))
                        }
                    ))
                    print(f"[INFO] {item} 항목 처리 완료 (길이: {len(content)}자)")
            
            print(f"[SUCCESS] CSV에서 {len(documents)}개 재무지표 문서 생성 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] CSV 파일 처리 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return []


