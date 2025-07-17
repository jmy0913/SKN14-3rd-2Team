"""
문서 처리 모듈
DART API 데이터를 LangChain Document 객체로 변환
"""

from typing import List, Dict, Any
from langchain_core.documents import Document
import pandas as pd
import os

from src.clients.dart_client import DartClient, CompanyInfo
from src.config import RAG_DOCUMENTS_FOLDER_NAME, FINANCIAL_REPORTS_FOLDER_NAME


class DocumentProcessor:
    """문서 처리 클래스"""
    
    def __init__(self):
        self.dart_client = DartClient()
    
    def _is_valid_data(self, value: str) -> bool:
        """데이터가 유효한지 검증합니다."""
        if not value or not isinstance(value, str):
            return False
        
        # 무의미한 값들
        invalid_values = ['-', '해당없음', '해당사항없음', 'N/A', 'n/a', '없음', '0', '0원']
        cleaned_value = value.strip()
        
        if not cleaned_value or cleaned_value in invalid_values:
            return False
        
        # 너무 짧은 값
        if len(cleaned_value) < 2:
            return False
            
        return True
    
    def _has_meaningful_content(self, data_item: dict) -> bool:
        """주요사항 데이터가 의미있는 내용을 포함하는지 확인합니다."""
        current = data_item.get('thstrm', '')
        previous = data_item.get('frmtrm', '')
        before_previous = data_item.get('lwfr', '')
        
        # 적어도 하나의 값이 유효해야 함
        return any(self._is_valid_data(val) for val in [current, previous, before_previous])
    
    def _create_document_content_key(self, corp_name: str, year: int, section: str, item_name: str) -> str:
        """문서 중복 방지를 위한 키 생성"""
        return f"{corp_name}_{year}_{section}_{item_name}".replace(" ", "_")

    def process_financial_data_from_csv(self, corp_name: str, year: int) -> List[Document]:
        """CSV 파일에서 재무 데이터를 처리합니다 (빈 데이터 필터링 포함)."""
        try:
            csv_filename = f"{corp_name}_{str(year)}_재무제표.csv"
            csv_path = os.path.join(RAG_DOCUMENTS_FOLDER_NAME, FINANCIAL_REPORTS_FOLDER_NAME, csv_filename)
            
            if not os.path.exists(csv_path):
                print(f"[ERROR] CSV 파일을 찾을 수 없습니다: {csv_path}")
                return []
            
            df = pd.read_csv(csv_path)
            print(f"[INFO] CSV 파일 로드 완료: {len(df)}행")
            
            documents = []
            processed_items = set()  # 중복 방지용
            
            # 주요 재무 지표들 (우선순위 순)
            key_financial_items = [
                "자산총계", "부채총계", "자본총계", 
                "영업수익", "영업이익", "당기순이익",
                "유동자산", "비유동자산", "유동부채", "비유동부채",
                "현금및현금성자산", "매출채권", "재고자산", "유형자산", 
                "단기차입금", "장기차입금", "이익잉여금", "자본금",
                "매출원가", "판매비와관리비", "법인세비용",
                "영업활동현금흐름", "투자활동현금흐름", "재무활동현금흐름"
            ]
            
            valid_count = 0
            filtered_count = 0
            
            for item in key_financial_items:
                matching_rows = df[df['account_nm'].str.contains(item, na=False)]
                if not matching_rows.empty:
                    row = matching_rows.iloc[0]
                    
                    # 중복 방지
                    item_key = f"{corp_name}_{year}_{item}"
                    if item_key in processed_items:
                        continue
                    processed_items.add(item_key)
                    
                    # 데이터 유효성 검증
                    current_amount = str(row.get('thstrm_amount', ''))
                    previous_amount = str(row.get('frmtrm_amount', ''))
                    
                    if not self._is_valid_data(current_amount) and not self._is_valid_data(previous_amount):
                        filtered_count += 1
                        continue
                    
                    # 유효한 데이터만 포함하여 내용 생성
                    content_parts = [f"{corp_name} {year}년 {item}"]
                    
                    if self._is_valid_data(current_amount):
                        content_parts.append(f"- 금액: {current_amount}원")
                        content_parts.append(f"- 기간: 제{row['thstrm_nm']}")
                    
                    if self._is_valid_data(previous_amount):
                        content_parts.append(f"- 이전년도: {previous_amount}원 (제{row['frmtrm_nm']})")
                    
                    before_previous_amount = str(row.get('bfefrmtrm_amount', ''))
                    if self._is_valid_data(before_previous_amount):
                        content_parts.append(f"- 전전년도: {before_previous_amount}원 (제{row['bfefrmtrm_nm']})")
                    
                    content_parts.extend([
                        f"- 통화: {row['currency']}",
                        f"- 계정과목: {row['account_nm']}",
                        f"- 계정코드: {row['account_id']}"
                    ])
                    
                    content = "\n".join(content_parts)
                    
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
                    valid_count += 1
                else:
                    filtered_count += 1
            
            print(f"[SUCCESS] CSV에서 {valid_count}개 재무지표 문서 생성 완료 (필터링: {filtered_count}개)")
            return documents
            
        except Exception as e:
            print(f"[ERROR] CSV 파일 처리 중 오류: {e}")
            return []

    def process_key_matters(self, corp_name: str, year: int) -> List[Document]:
        """주요사항 데이터를 처리합니다 (빈 데이터 필터링 포함)."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []

            data = self.dart_client.get_key_matters(company.corp_code, year)
            documents = []
            processed_keys = set()  # 중복 방지용

            valid_count = 0
            filtered_count = 0

            for item in data:
                # 데이터 유효성 검증
                if not self._has_meaningful_content(item):
                    filtered_count += 1
                    continue
                
                item_name = item.get('se', '').strip()
                if not item_name:
                    filtered_count += 1
                    continue
                
                # 중복 방지
                content_key = self._create_document_content_key(corp_name, year, "주요사항", item_name)
                if content_key in processed_keys:
                    filtered_count += 1
                    continue
                
                processed_keys.add(content_key)
                
                # 유효한 값들만 포함하여 내용 생성
                content_parts = [f"{corp_name} {year}년 주요사항", f"항목: {item_name}"]
                
                current = item.get('thstrm', '')
                previous = item.get('frmtrm', '')
                before_previous = item.get('lwfr', '')
                
                if self._is_valid_data(current):
                    content_parts.append(f"당기: {current}")
                if self._is_valid_data(previous):
                    content_parts.append(f"전기: {previous}")
                if self._is_valid_data(before_previous):
                    content_parts.append(f"전전기: {before_previous}")
                
                # 최소 2개 이상의 정보가 있어야 문서 생성
                if len(content_parts) < 3:
                    filtered_count += 1
                    continue
                
                content = "\n".join(content_parts)
                
                documents.append(Document(
                    page_content=content,
                    metadata={
                        "corp_name": str(corp_name),
                        "corp_code": str(company.corp_code),
                        "year": str(year),
                        "section": "주요사항",
                        "source": "business_report",
                        "content_type": "key_matters",
                        "item_name": str(item_name)
                    }
                ))
                valid_count += 1

            print(f"[SUCCESS] 주요사항 {valid_count}개 처리 완료 (필터링: {filtered_count}개)")
            return documents

        except Exception as e:
            print(f"[ERROR] 주요사항 처리 실패: {e}")
            return []
    
    def process_dividend_info(self, corp_name: str, year: int) -> List[Document]:
        """배당 정보를 처리합니다 (빈 데이터 필터링 포함)."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                return []

            data = self.dart_client.get_key_matters(company.corp_code, year)
            documents = []
            processed_keys = set()  # 중복 방지용

            # 배당 관련 항목 필터링
            dividend_items = []
            for item in data:
                item_name = item.get('se', '').strip()
                if '배당' in item_name and self._has_meaningful_content(item):
                    dividend_items.append(item)

            if not dividend_items:
                print(f"[INFO] {corp_name} {year}년 배당 정보 없음 - 문서 생성 생략")
                return []

            valid_count = 0
            for item in dividend_items:
                item_name = item.get('se', '').strip()
                
                # 중복 방지
                content_key = self._create_document_content_key(corp_name, year, "배당정보", item_name)
                if content_key in processed_keys:
                    continue
                processed_keys.add(content_key)
                
                # 유효한 값들만 포함하여 내용 생성
                content_parts = [f"{corp_name} {year}년 배당 정보", f"항목: {item_name}"]
                
                current = item.get('thstrm', '')
                previous = item.get('frmtrm', '')
                before_previous = item.get('lwfr', '')
                
                if self._is_valid_data(current):
                    content_parts.append(f"당기: {current}")
                if self._is_valid_data(previous):
                    content_parts.append(f"전기: {previous}")
                if self._is_valid_data(before_previous):
                    content_parts.append(f"전전기: {before_previous}")
                
                content = "\n".join(content_parts)
                
                documents.append(Document(
                    page_content=content,
                    metadata={
                        "corp_name": str(corp_name),
                        "corp_code": str(company.corp_code),
                        "year": str(year),
                        "section": "배당에 관한 사항",
                        "source": "business_report",
                        "content_type": "dividend",
                        "item_name": str(item_name)
                    }
                ))
                valid_count += 1

            print(f"[SUCCESS] 배당 정보 {valid_count}개 처리 완료")
            return documents

        except Exception as e:
            print(f"[ERROR] 배당 정보 처리 실패: {e}")
            return []
    
    def process_employee_status(self, corp_name: str, year: int) -> List[Document]:
        """임직원 현황을 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                return []
            
            data = self.dart_client.get_employee_status(company.corp_code, year)
            documents = []
            
            for item in data:
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
                        "corp_code": str(company.corp_code),
                        "year": str(year),
                        "section": "임직원 현황",
                        "source": "business_report",
                        "content_type": "employee_status"
                    }
                ))
            
            print(f"[SUCCESS] 임직원 현황 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 임직원 현황 처리 실패: {e}")
            return []
    
    def process_shareholder_info(self, corp_name: str, year: int) -> List[Document]:
        """주주 정보를 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                return []
            
            documents = []
            
            # 일반 주주현황
            shareholder_data = self.dart_client.get_shareholder_status(company.corp_code, year)
            for item in shareholder_data:
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
                        "corp_code": str(company.corp_code),
                        "year": str(year),
                        "section": "주주현황",
                        "source": "business_report",
                        "content_type": "shareholder_status"
                    }
                ))
            
            # 최대주주현황
            major_shareholder_data = self.dart_client.get_major_shareholder_status(company.corp_code, year)
            for item in major_shareholder_data:
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
                        "corp_code": str(company.corp_code),
                        "year": str(year),
                        "section": "최대주주현황",
                        "source": "business_report",
                        "content_type": "major_shareholder"
                    }
                ))
            
            total_count = len(shareholder_data) + len(major_shareholder_data)
            print(f"[SUCCESS] 주주 정보 {total_count}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 주주 정보 처리 실패: {e}")
            return []
    
    def process_company_overview(self, corp_name: str, year: int) -> List[Document]:
        """기업개요를 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 주요사항에서 기업 개요 관련 정보 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            overview_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['설립', '대표이사', '주소', '자본금', '주식수', '사업'])]
            
            if overview_matters:
                for matter in overview_matters:
                    content = f"""
                        {corp_name} {year}년 {matter.get('se', '')}
                        - 당기: {matter.get('thstrm', '')}
                        - 전기: {matter.get('frmtrm', '')}
                        - 전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "기업개요",
                            "source": "business_report",
                            "content_type": "company_overview"
                        }
                    ))
            
            # 데이터가 없는 경우 문서 생성하지 않음
            if not documents:
                print(f"[INFO] {corp_name} {year}년 기업개요 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] 기업개요 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 기업개요 처리 실패: {e}")
            return []
    
    # === 새로운 사업보고서 섹션 처리 메서드들 ===
    
    def process_business_content(self, corp_name: str, year: int) -> List[Document]:
        """사업의 내용을 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 1. 주요사항에서 사업 관련 정보 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            business_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['사업', '매출', '제품', '서비스', '영업'])]
            
            if business_matters:
                for matter in business_matters:
                    content = f"""
                        {corp_name} {year}년 사업 관련 주요사항
                        항목: {matter.get('se', '')}
                        당기: {matter.get('thstrm', '')}
                        전기: {matter.get('frmtrm', '')}
                        전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "사업 관련 주요사항",
                            "source": "business_report",
                            "content_type": "business_matters"
                        }
                    ))
            
            # 데이터가 없는 경우 문서 생성하지 않음
            if not documents:
                print(f"[INFO] {corp_name} {year}년 사업의 내용 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] 사업의 내용 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 사업의 내용 처리 실패: {e}")
            return []
    

    
    def process_research_development(self, corp_name: str, year: int) -> List[Document]:
        """연구개발 활동을 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 1. 연구개발 데이터 가져오기
            rd_data = self.dart_client.get_research_development(company.corp_code, year)
            if rd_data:
                for rd_item in rd_data:
                    content = f"""
                        {corp_name} {year}년 연구개발 활동
                        연구개발 분야: {rd_item.get('rd_field', '')}
                        연구개발비: {rd_item.get('rd_cost', '')}원
                        연구개발 인력: {rd_item.get('rd_personnel', '')}명
                        연구개발 성과: {rd_item.get('rd_result', '')}
                        특허 출원: {rd_item.get('patent_application', '')}건
                        특허 등록: {rd_item.get('patent_registration', '')}건
                        비고: {rd_item.get('rm', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "연구개발 활동",
                            "source": "business_report",
                            "content_type": "research_development"
                        }
                    ))
            
            # 2. 주요사항에서 연구개발 관련 정보 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            rd_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['연구', '개발', 'R&D', '특허', '기술'])]
            
            if rd_matters:
                for matter in rd_matters:
                    content = f"""
                        {corp_name} {year}년 연구개발 관련 주요사항
                        항목: {matter.get('se', '')}
                        당기: {matter.get('thstrm', '')}
                        전기: {matter.get('frmtrm', '')}
                        전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "연구개발 관련 주요사항",
                            "source": "business_report",
                            "content_type": "rd_matters"
                        }
                    ))
            
            # 데이터가 없는 경우 문서 생성하지 않음
            if not documents:
                print(f"[INFO] {corp_name} {year}년 연구개발 활동 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] 연구개발 활동 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 연구개발 활동 처리 실패: {e}")
            return []
    

    
    def process_major_contracts(self, corp_name: str, year: int) -> List[Document]:
        """주요 계약 및 거래를 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 1. 주요 계약 데이터 가져오기
            major_contracts_data = self.dart_client.get_major_contracts(company.corp_code, year)
            if major_contracts_data:
                for contract in major_contracts_data:
                    content = f"""
                        {corp_name} {year}년 주요 계약
                        계약명: {contract.get('cntrct_nm', '')}
                        계약상대방: {contract.get('cntrct_party', '')}
                        계약금액: {contract.get('cntrct_amount', '')}원
                        계약기간: {contract.get('cntrct_period', '')}
                        계약내용: {contract.get('cntrct_content', '')}
                        계약일자: {contract.get('cntrct_date', '')}
                        비고: {contract.get('rm', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "주요 계약",
                            "source": "business_report",
                            "content_type": "major_contracts"
                        }
                    ))
            
            # 2. 특수관계자 거래 데이터 가져오기
            related_party_data = self.dart_client.get_related_party_transactions(company.corp_code, year)
            if related_party_data:
                for transaction in related_party_data:
                    content = f"""
                        {corp_name} {year}년 특수관계자 거래
                        거래상대방: {transaction.get('rltdt_party', '')}
                        거래내용: {transaction.get('trnsctn_content', '')}
                        거래금액: {transaction.get('trnsctn_amount', '')}원
                        거래기간: {transaction.get('trnsctn_period', '')}
                        거래조건: {transaction.get('trnsctn_condition', '')}
                        승인절차: {transaction.get('approval_procedure', '')}
                        비고: {transaction.get('rm', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "특수관계자 거래",
                            "source": "business_report",
                            "content_type": "related_party_transactions"
                        }
                    ))
            
            # 3. 데이터가 없는 경우 기본 정보 생성
            if not documents:
                # 주요사항에서 계약 관련 정보 찾기
                key_matters = self.dart_client.get_key_matters(company.corp_code, year)
                contract_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['계약', '거래', '공급', '구매'])]
                
                if contract_matters:
                    for matter in contract_matters:
                        content = f"""
                            {corp_name} {year}년 계약 관련 주요사항
                            항목: {matter.get('se', '')}
                            당기: {matter.get('thstrm', '')}
                            전기: {matter.get('frmtrm', '')}
                            전전기: {matter.get('lwfr', '')}
                        """.strip()
                        
                        documents.append(Document(
                            page_content=content,
                            metadata={
                                "corp_name": str(corp_name),
                                "corp_code": str(company.corp_code),
                                "year": str(year),
                                "section": "계약 관련 주요사항",
                                "source": "business_report",
                                "content_type": "contract_matters"
                            }
                        ))
                else:
                    # 데이터가 없는 경우 문서 생성하지 않음
                    print(f"[INFO] {corp_name} {year}년 주요 계약 및 거래 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] 주요 계약 및 거래 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 주요 계약 및 거래 처리 실패: {e}")
            return []
    

    
    def process_board_audit_info(self, corp_name: str, year: int) -> List[Document]:
        """이사회 및 감사기구 현황을 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 주요사항에서 이사회 관련 정보 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            board_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['이사', '감사', '이사회', '감사위원회', '사외이사'])]
            
            if board_matters:
                for matter in board_matters:
                    content = f"""
                        {corp_name} {year}년 {matter.get('se', '')}
                        - 당기: {matter.get('thstrm', '')}
                        - 전기: {matter.get('frmtrm', '')}
                        - 전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "이사회 및 감사기구 현황",
                            "source": "business_report",
                            "content_type": "board_audit"
                        }
                    ))
            
            # 데이터가 없는 경우 문서 생성하지 않음
            if not documents:
                print(f"[INFO] {corp_name} {year}년 이사회 및 감사기구 현황 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] 이사회 및 감사기구 현황 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 이사회 및 감사기구 현황 처리 실패: {e}")
            return []
    
    def process_merger_acquisition(self, corp_name: str, year: int) -> List[Document]:
        """합병·분할 등 주요 경영사항을 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 주요사항에서 합병·분할 관련 정보 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            merger_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['합병', '분할', '인수', '매수', '투자', '제휴', '자회사'])]
            
            if merger_matters:
                for matter in merger_matters:
                    content = f"""
                        {corp_name} {year}년 {matter.get('se', '')}
                        - 당기: {matter.get('thstrm', '')}
                        - 전기: {matter.get('frmtrm', '')}
                        - 전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "합병·분할 등 주요 경영사항",
                            "source": "business_report",
                            "content_type": "merger_acquisition"
                        }
                    ))
            
            # 데이터가 없는 경우 문서 생성하지 않음
            if not documents:
                print(f"[INFO] {corp_name} {year}년 합병·분할 등 주요 경영사항 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] 합병·분할 등 주요 경영사항 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 합병·분할 등 주요 경영사항 처리 실패: {e}")
            return []
    
    def process_litigation_disputes(self, corp_name: str, year: int) -> List[Document]:
        """소송 및 분쟁 현황을 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 1. 소송 및 분쟁 데이터 가져오기
            litigation_data = self.dart_client.get_litigation_disputes(company.corp_code, year)
            if litigation_data:
                for litigation in litigation_data:
                    content = f"""
                        {corp_name} {year}년 소송 및 분쟁 현황
                        소송명: {litigation.get('litigation_name', '')}
                        소송상대방: {litigation.get('litigation_party', '')}
                        소송내용: {litigation.get('litigation_content', '')}
                        소송금액: {litigation.get('litigation_amount', '')}원
                        소송상태: {litigation.get('litigation_status', '')}
                        소송기간: {litigation.get('litigation_period', '')}
                        예상결과: {litigation.get('expected_result', '')}
                        비고: {litigation.get('rm', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "소송 및 분쟁 현황",
                            "source": "business_report",
                            "content_type": "litigation_disputes"
                        }
                    ))
            
            # 2. 주요사항에서 소송 관련 정보 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            litigation_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['소송', '분쟁', '소송충당금', '법적분쟁'])]
            
            if litigation_matters:
                for matter in litigation_matters:
                    content = f"""
                        {corp_name} {year}년 소송 관련 주요사항
                        항목: {matter.get('se', '')}
                        당기: {matter.get('thstrm', '')}
                        전기: {matter.get('frmtrm', '')}
                        전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "소송 관련 주요사항",
                            "source": "business_report",
                            "content_type": "litigation_matters"
                        }
                    ))
            
            # 데이터가 없는 경우 문서 생성하지 않음
            if not documents:
                print(f"[INFO] {corp_name} {year}년 소송 및 분쟁 현황 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] 소송 및 분쟁 현황 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 소송 및 분쟁 현황 처리 실패: {e}")
            return []
    

    
    def process_internal_control(self, corp_name: str, year: int) -> List[Document]:
        """내부회계관리제도 운영실태를 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 주요사항에서 내부회계관리제도 관련 정보 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            control_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['내부회계관리', '감사', '컴플라이언스', '내부통제'])]
            
            if control_matters:
                for matter in control_matters:
                    content = f"""
                        {corp_name} {year}년 {matter.get('se', '')}
                        - 당기: {matter.get('thstrm', '')}
                        - 전기: {matter.get('frmtrm', '')}
                        - 전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "내부회계관리제도 운영실태",
                            "source": "business_report",
                            "content_type": "internal_control"
                        }
                    ))
            
            # 데이터가 없는 경우 문서 생성하지 않음
            if not documents:
                print(f"[INFO] {corp_name} {year}년 내부회계관리제도 운영실태 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] 내부회계관리제도 운영실태 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 내부회계관리제도 운영실태 처리 실패: {e}")
            return []
    
    def process_esg_information(self, corp_name: str, year: int) -> List[Document]:
        """ESG(환경·사회·지배구조) 정보를 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 주요사항에서 ESG 관련 정보 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            esg_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['환경', '사회', '지배구조', 'ESG', '지속가능', '친환경', '온실가스', '공헌'])]
            
            if esg_matters:
                for matter in esg_matters:
                    content = f"""
                        {corp_name} {year}년 {matter.get('se', '')}
                        - 당기: {matter.get('thstrm', '')}
                        - 전기: {matter.get('frmtrm', '')}
                        - 전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "ESG(환경·사회·지배구조) 정보",
                            "source": "business_report",
                            "content_type": "esg_information"
                        }
                    ))
            
            # 데이터가 없는 경우 문서 생성하지 않음
            if not documents:
                print(f"[INFO] {corp_name} {year}년 ESG 정보 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] ESG 정보 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] ESG 정보 처리 실패: {e}")
            return []
    
    def process_other_important_matters(self, corp_name: str, year: int) -> List[Document]:
        """기타 중요사항을 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 주요사항에서 기타 중요사항 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            other_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['공시', '감사', '주주총회', '정관', '계획', '변동'])]
            
            if other_matters:
                for matter in other_matters:
                    content = f"""
                        {corp_name} {year}년 {matter.get('se', '')}
                        - 당기: {matter.get('thstrm', '')}
                        - 전기: {matter.get('frmtrm', '')}
                        - 전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "기타 중요사항",
                            "source": "business_report",
                            "content_type": "other_important_matters"
                        }
                    ))
            
            # 데이터가 없는 경우 문서 생성하지 않음
            if not documents:
                print(f"[INFO] {corp_name} {year}년 기타 중요사항 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] 기타 중요사항 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 기타 중요사항 처리 실패: {e}")
            return []
    
    # === 사업보고서 표준 구조에 따른 처리 메서드들 ===
    
    def process_chapter1_company_overview(self, corp_name: str, year: int) -> List[Document]:
        """제1장 회사의 개요를 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 주요사항에서 회사 개요 관련 정보 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            company_overview_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['설립', '대표이사', '주소', '자본금', '주식수'])]
            
            if company_overview_matters:
                for matter in company_overview_matters:
                    content = f"""
                        {corp_name} {year}년 {matter.get('se', '')}
                        - 당기: {matter.get('thstrm', '')}
                        - 전기: {matter.get('frmtrm', '')}
                        - 전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "회사의 개요",
                            "source": "business_report",
                            "content_type": "company_overview"
                        }
                    ))
            
            print(f"[SUCCESS] 제1장 회사의 개요 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 제1장 회사의 개요 처리 실패: {e}")
            return []
    
    def process_chapter2_business_content(self, corp_name: str, year: int) -> List[Document]:
        """제2장 사업의 내용을 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 주요사항에서 사업 관련 정보 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            business_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['사업', '매출', '제품', '서비스', '영업', '생산', '매출액'])]
            
            if business_matters:
                for matter in business_matters:
                    content = f"""
                        {corp_name} {year}년 {matter.get('se', '')}
                        - 당기: {matter.get('thstrm', '')}
                        - 전기: {matter.get('frmtrm', '')}
                        - 전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "사업의 내용",
                            "source": "business_report",
                            "content_type": "business_content"
                        }
                    ))
            
            # 데이터가 없는 경우 문서 생성하지 않음
            if not documents:
                print(f"[INFO] {corp_name} {year}년 사업의 내용 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] 제2장 사업의 내용 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 제2장 사업의 내용 처리 실패: {e}")
            return []
    
    def process_chapter3_financial_matters(self, corp_name: str, year: int) -> List[Document]:
        """제3장 재무에 관한 사항을 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 실제 재무 데이터 가져오기 (CSV 파일에서)
            financial_docs = self.process_financial_data_from_csv(corp_name, year)
            if financial_docs:
                # 주요 재무 지표만 선택
                key_financial_items = ["자산총계", "부채총계", "자본총계", "영업수익", "영업이익", "당기순이익"]
                key_docs = [doc for doc in financial_docs if any(item in doc.page_content for item in key_financial_items)]
                
                for doc in key_docs[:5]:  # 처음 5개만 사용
                    content = f"""
                        {corp_name} {year}년 재무 정보
                        {doc.page_content}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "재무에 관한 사항",
                            "source": "business_report",
                            "content_type": "financial_matters"
                        }
                    ))
            
            # 주요사항에서 재무 관련 정보 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            financial_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['자산', '부채', '자본', '매출', '이익', '손실', 'ROE', 'ROA'])]
            
            if financial_matters:
                for matter in financial_matters:
                    content = f"""
                        {corp_name} {year}년 {matter.get('se', '')}
                        - 당기: {matter.get('thstrm', '')}
                        - 전기: {matter.get('frmtrm', '')}
                        - 전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "재무에 관한 사항",
                            "source": "business_report",
                            "content_type": "financial_matters"
                        }
                    ))
            
            # 데이터가 없는 경우 문서 생성하지 않음
            if not documents:
                print(f"[INFO] {corp_name} {year}년 재무 정보 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] 제3장 재무에 관한 사항 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 제3장 재무에 관한 사항 처리 실패: {e}")
            return []
    
    def process_chapter4_shareholders_governance(self, corp_name: str, year: int) -> List[Document]:
        """제4장 주주 및 지배구조에 관한 사항을 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 실제 주주 현황 데이터 가져오기
            shareholder_docs = self.process_shareholder_info(corp_name, year)
            if shareholder_docs:
                for doc in shareholder_docs[:3]:  # 처음 3개만 사용
                    content = f"""
                        {corp_name} {year}년 주주 및 지배구조
                        {doc.page_content}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "주주 및 지배구조에 관한 사항",
                            "source": "business_report",
                            "content_type": "shareholders_governance"
                        }
                    ))
            
            # 이사회 및 감사기구 현황 가져오기
            board_audit_docs = self.process_board_audit_info(corp_name, year)
            if board_audit_docs:
                for doc in board_audit_docs:
                    content = f"""
                        {corp_name} {year}년 이사회 및 감사기구
                        {doc.page_content}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "주주 및 지배구조에 관한 사항",
                            "source": "business_report",
                            "content_type": "shareholders_governance"
                        }
                    ))
            
            # 주요사항에서 주주 관련 정보 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            shareholder_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['주주', '이사', '감사', '지배구조', '주식'])]
            
            if shareholder_matters:
                for matter in shareholder_matters:
                    content = f"""
                        {corp_name} {year}년 {matter.get('se', '')}
                        - 당기: {matter.get('thstrm', '')}
                        - 전기: {matter.get('frmtrm', '')}
                        - 전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "주주 및 지배구조에 관한 사항",
                            "source": "business_report",
                            "content_type": "shareholders_governance"
                        }
                    ))
            
            # 데이터가 없는 경우 문서 생성하지 않음
            if not documents:
                print(f"[INFO] {corp_name} {year}년 주주 및 지배구조 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] 제4장 주주 및 지배구조에 관한 사항 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 제4장 주주 및 지배구조에 관한 사항 처리 실패: {e}")
            return []
    
    def process_chapter5_other_important_matters(self, corp_name: str, year: int) -> List[Document]:
        """제5장 기타 중요사항을 처리합니다."""
        try:
            company = self.dart_client.find_company_by_name(corp_name)
            if not company:
                print(f"[ERROR] {corp_name} 기업을 찾을 수 없습니다.")
                return []
            
            documents = []
            
            # 배당 정보 가져오기
            dividend_docs = self.process_dividend_info(corp_name, year)
            if dividend_docs:
                for doc in dividend_docs:
                    content = f"""
                        {corp_name} {year}년 배당 정보
                        {doc.page_content}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "기타 중요사항",
                            "source": "business_report",
                            "content_type": "other_important_matters"
                        }
                    ))
            
            # 연구개발 활동 가져오기
            rd_docs = self.process_research_development(corp_name, year)
            if rd_docs:
                for doc in rd_docs[:2]:  # 처음 2개만 사용
                    content = f"""
                        {corp_name} {year}년 연구개발 활동
                        {doc.page_content}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "연구개발 활동",
                            "source": "business_report",
                            "content_type": "other_important_matters"
                        }
                    ))
            
            # 주요 계약 및 거래 가져오기
            contract_docs = self.process_major_contracts(corp_name, year)
            if contract_docs:
                for doc in contract_docs[:2]:  # 처음 2개만 사용
                    content = f"""
                        {corp_name} {year}년 주요 계약 및 거래
                        {doc.page_content}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "주요 계약 및 거래",
                            "source": "business_report",
                            "content_type": "other_important_matters"
                        }
                    ))
            
            # 소송 및 분쟁 현황 가져오기
            litigation_docs = self.process_litigation_disputes(corp_name, year)
            if litigation_docs:
                for doc in litigation_docs[:2]:  # 처음 2개만 사용
                    content = f"""
                        {corp_name} {year}년 소송 및 분쟁 현황
                        {doc.page_content}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "소송 및 분쟁 현황",
                            "source": "business_report",
                            "content_type": "other_important_matters"
                        }
                    ))
            
            # 주요사항에서 기타 중요사항 찾기
            key_matters = self.dart_client.get_key_matters(company.corp_code, year)
            other_matters = [item for item in key_matters if any(keyword in item.get('se', '') for keyword in ['배당', '연구', '계약', '소송', '감사', '공시'])]
            
            if other_matters:
                for matter in other_matters:
                    content = f"""
                        {corp_name} {year}년 {matter.get('se', '')}
                        - 당기: {matter.get('thstrm', '')}
                        - 전기: {matter.get('frmtrm', '')}
                        - 전전기: {matter.get('lwfr', '')}
                    """.strip()
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "corp_name": str(corp_name),
                            "corp_code": str(company.corp_code),
                            "year": str(year),
                            "section": "기타 중요사항",
                            "source": "business_report",
                            "content_type": "other_important_matters"
                        }
                    ))
            
            # 데이터가 없는 경우 문서 생성하지 않음
            if not documents:
                print(f"[INFO] {corp_name} {year}년 기타 중요사항 데이터 없음 - 문서 생성 생략")
            
            print(f"[SUCCESS] 제5장 기타 중요사항 {len(documents)}개 처리 완료")
            return documents
            
        except Exception as e:
            print(f"[ERROR] 제5장 기타 중요사항 처리 실패: {e}")
            return [] 