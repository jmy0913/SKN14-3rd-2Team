"""
DART API 클라이언트 모듈
다양한 DART API 엔드포인트에 대한 통합 클라이언트
"""

import requests
import zipfile
import xml.etree.ElementTree as ET
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from src.config import DART_API_KEY


@dataclass
class CompanyInfo:
    """기업 정보 데이터 클래스"""
    corp_code: str
    corp_name: str


@dataclass
class FinancialData:
    """재무 데이터 클래스"""
    corp_name: str
    corp_code: str
    year: int
    account_name: str
    current_amount: str
    previous_amount: str
    account_id: str
    currency: str


@dataclass
class BusinessReportData:
    """사업보고서 데이터 클래스"""
    corp_name: str
    corp_code: str
    year: int
    section: str
    content: str
    data_type: str


class DartClient:
    """DART API 통합 클라이언트"""
    
    BASE_URL = "https://opendart.fss.or.kr/api"
    
    def __init__(self, api_key: str = DART_API_KEY):
        self.api_key = api_key
        self._company_list_cache = None
        self._cache_file = Path("corpcode_cache.xml")
        
    def _download_corpcode_if_needed(self) -> bool:
        """필요한 경우에만 corpcode.xml을 다운로드합니다."""
        try:
            # 캐시 파일이 있으면 사용
            if self._cache_file.exists():
                print(f"[INFO] 기존 캐시 파일 사용: {self._cache_file}")
                return True
            
            # 캐시 파일이 없으면 다운로드
            print(f"[INFO] corpcode.xml 다운로드 중...")
            url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={self.api_key}"
            response = requests.get(url)
            response.raise_for_status()
            
            # ZIP 파일로 저장
            corp_code_file = 'corpCode.zip'
            with open(corp_code_file, 'wb') as f:
                f.write(response.content)
            
            # ZIP 파일 압축 해제
            with zipfile.ZipFile(corp_code_file, 'r') as zip_ref:
                zip_ref.extractall('.')
            
            # 임시 ZIP 파일 삭제
            if os.path.exists(corp_code_file):
                os.remove(corp_code_file)
            
            # CORPCODE.xml을 캐시 파일로 이동
            if os.path.exists('CORPCODE.xml'):
                os.rename('CORPCODE.xml', self._cache_file)
                print(f"[INFO] corpcode.xml 캐시 파일로 저장: {self._cache_file}")
                return True
            else:
                print(f"[ERROR] CORPCODE.xml 파일을 찾을 수 없습니다")
                return False
                
        except Exception as e:
            print(f"[ERROR] corpcode.xml 다운로드 실패: {e}")
            return False
    
    def _load_companies_from_cache(self) -> List[CompanyInfo]:
        """캐시 파일에서 기업 리스트를 로드합니다."""
        try:
            tree = ET.parse(self._cache_file)
            root = tree.getroot()
            
            companies = []
            for child in root.findall('list'):
                corp_code = child.find('corp_code').text
                corp_name = child.find('corp_name').text
                companies.append(CompanyInfo(corp_code=corp_code, corp_name=corp_name))
            
            print(f"[INFO] 캐시에서 {len(companies)}개 기업 정보 로드 완료")
            return companies
            
        except Exception as e:
            print(f"[ERROR] 캐시 파일 로드 실패: {e}")
            return []
    
    def get_company_list(self) -> List[CompanyInfo]:
        """기업 코드 리스트를 가져옵니다. (캐시 사용)"""
        # 이미 메모리에 캐시된 경우
        if self._company_list_cache is not None:
            return self._company_list_cache
        
        # 캐시 파일 다운로드 또는 로드
        if self._download_corpcode_if_needed():
            self._company_list_cache = self._load_companies_from_cache()
            return self._company_list_cache
        else:
            return []
    
    def clear_cache(self) -> None:
        """캐시를 삭제합니다."""
        self._company_list_cache = None
        if self._cache_file.exists():
            self._cache_file.unlink()
            print(f"[INFO] 캐시 파일 삭제: {self._cache_file}")
    
    def refresh_company_list(self) -> List[CompanyInfo]:
        """기업 리스트를 새로 다운로드합니다."""
        self.clear_cache()
        return self.get_company_list()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """API 요청을 수행합니다."""
        params['crtfc_key'] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def find_company_by_name(self, company_name: str) -> Optional[CompanyInfo]:
        """기업명으로 기업 정보를 찾습니다."""
        companies = self.get_company_list()
        for company in companies:
            if company.corp_name == company_name:
                return company
        return None
    
    def get_financial_data(self, corp_code: str, year: int) -> List[Dict[str, Any]]:
        """재무제표 데이터를 가져옵니다."""
        try:
            params = {
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': '11011',  # 사업보고서
                'fs_div': 'CFS'  # 연결재무제표
            }
            
            data = self._make_request('fnlttSinglAcntAll.json', params)
            
            if data.get('status') == '013':  # 데이터 없음
                print(f"[WARNING] 해당 연도의 재무데이터가 없습니다.")
                return []
            
            return data.get('list', [])
            
        except Exception as e:
            print(f"[ERROR] 재무데이터 가져오기 실패: {e}")
            return []
    
    def get_key_matters(self, corp_code: str, year: int) -> List[Dict[str, Any]]:
        """주요사항을 가져옵니다."""
        try:
            params = {
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': '11011'
            }
            
            data = self._make_request('alotMatter.json', params)
            return data.get('list', [])
            
        except Exception as e:
            print(f"[ERROR] 주요사항 가져오기 실패: {e}")
            return []
    
    def get_employee_status(self, corp_code: str, year: int) -> List[Dict[str, Any]]:
        """임직원 현황을 가져옵니다."""
        try:
            params = {
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': '11011'
            }
            
            data = self._make_request('empSttus.json', params)
            return data.get('list', [])
            
        except Exception as e:
            print(f"[ERROR] 임직원 현황 가져오기 실패: {e}")
            return []
    
    def get_shareholder_status(self, corp_code: str, year: int) -> List[Dict[str, Any]]:
        """주주현황을 가져옵니다."""
        try:
            params = {
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': '11011'
            }
            
            data = self._make_request('hyslrSttus.json', params)
            return data.get('list', [])
            
        except Exception as e:
            print(f"[ERROR] 주주현황 가져오기 실패: {e}")
            return []
    
    def get_major_shareholder_status(self, corp_code: str, year: int) -> List[Dict[str, Any]]:
        """최대주주현황을 가져옵니다."""
        try:
            params = {
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': '11011'
            }
            
            data = self._make_request('mrhlSttus.json', params)
            return data.get('list', [])
            
        except Exception as e:
            print(f"[ERROR] 최대주주현황 가져오기 실패: {e}")
            return []
    
    def get_major_contracts(self, corp_code: str, year: int) -> List[Dict[str, Any]]:
        """주요 계약 및 거래를 가져옵니다."""
        try:
            params = {
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': '11011'
            }
            
            data = self._make_request('majorContract.json', params)
            return data.get('list', [])
            
        except Exception as e:
            print(f"[ERROR] 주요 계약 및 거래 가져오기 실패: {e}")
            return []
    
    def get_related_party_transactions(self, corp_code: str, year: int) -> List[Dict[str, Any]]:
        """특수관계자 거래를 가져옵니다."""
        try:
            params = {
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': '11011'
            }
            
            data = self._make_request('rltdtTrnsctn.json', params)
            return data.get('list', [])
            
        except Exception as e:
            print(f"[ERROR] 특수관계자 거래 가져오기 실패: {e}")
            return []
    
    def get_business_report_sections(self, corp_code: str, year: int) -> Dict[str, Any]:
        """사업보고서의 주요 섹션들을 가져옵니다."""
        try:
            params = {
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': '11011'
            }
            
            # 사업보고서 문서 정보 가져오기
            data = self._make_request('document.json', params)
            return data
            
        except Exception as e:
            print(f"[ERROR] 사업보고서 섹션 가져오기 실패: {e}")
            return {}
    
    def get_research_development(self, corp_code: str, year: int) -> List[Dict[str, Any]]:
        """연구개발 활동을 가져옵니다."""
        try:
            params = {
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': '11011'
            }
            
            data = self._make_request('rdInvestment.json', params)
            return data.get('list', [])
            
        except Exception as e:
            print(f"[ERROR] 연구개발 활동 가져오기 실패: {e}")
            return []
    
    def get_litigation_disputes(self, corp_code: str, year: int) -> List[Dict[str, Any]]:
        """소송 및 분쟁 현황을 가져옵니다."""
        try:
            params = {
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': '11011'
            }
            
            data = self._make_request('litigation.json', params)
            return data.get('list', [])
            
        except Exception as e:
            print(f"[ERROR] 소송 및 분쟁 현황 가져오기 실패: {e}")
            return []
    
    def get_internal_control(self, corp_code: str, year: int) -> List[Dict[str, Any]]:
        """내부회계관리제도 운영실태를 가져옵니다."""
        try:
            params = {
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': '11011'
            }
            
            data = self._make_request('internalControl.json', params)
            return data.get('list', [])
            
        except Exception as e:
            print(f"[ERROR] 내부회계관리제도 운영실태 가져오기 실패: {e}")
            return [] 