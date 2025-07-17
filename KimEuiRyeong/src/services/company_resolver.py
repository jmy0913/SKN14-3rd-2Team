#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
회사명 -> 기업코드 변환 서비스
회사 이름만으로 기업 코드를 찾아주는 서비스
"""

from typing import Dict, List, Optional
import re

class CompanyResolver:
    """회사명을 기업코드로 변환하는 클래스"""
    
    def __init__(self):
        # 주요 상장기업 매핑 (회사명 -> 기업코드)
        self.company_map = {
            # 대기업
            "삼성전자": "005930",
            "삼성전자우": "005935",  # 삼성전자 우선주
            "SK하이닉스": "000660", 
            "현대차": "005380",
            "현대자동차": "005380",
            "현대": "005380",  # 현대차 별칭
            "LG화학": "051910",
            "LG에너지솔루션": "373220",  # LG에너지솔루션
            "삼성바이오로직스": "207940",
            "셀트리온": "068270",
            "NAVER": "035420",
            "네이버": "035420",
            "현대모비스": "012330",
            "기아": "000270",
            "LG전자": "066570",
            "삼성SDI": "006400",
            "SK이노베이션": "096770",
            "POSCO홀딩스": "005490",
            "포스코홀딩스": "005490",
            "POSCO": "005490",
            "포스코": "005490",
            
            # 금융
            "신한지주": "055550",
            "KB금융": "105560",
            "하나금융지주": "086790",
            "우리금융지주": "316140",
            "삼성화재": "000810",
            "삼성생명": "032830",
            
            # 통신
            "SK텔레콤": "017670",
            "KT": "030200",
            "LG유플러스": "032640",
            
            # IT/게임
            "카카오": "035720",
            "엔씨소프트": "036570",
            "넷마블": "251270",
            "삼성에스디에스": "018260",
            "LG이노텍": "011070",
            
            # 바이오/제약
            "셀트리온헬스케어": "091990",
            "SK바이오팜": "326030",
            "한미약품": "128940",
            "유한양행": "000100",
            "대웅제약": "069620",
            
            # 화학/에너지
            "LG생활건강": "051900",
            "아모레퍼시픽": "090430",
            "롯데케미칼": "011170",
            "S-Oil": "010950",
            "에스오일": "010950",
            "한화솔루션": "009830",
            
            # 건설/인프라
            "현대건설": "000720",
            "삼성물산": "028050",
            "대우건설": "047040",
            "GS건설": "006360",
            
            # 소비재/유통
            "아모레G": "002790",
            "CJ제일제당": "097950",
            "오리온": "271560",
            "농심": "004370",
            "롯데쇼핑": "023530",
            "신세계": "004170",
            "현대백화점": "069960",
            
            # 운송/물류
            "대한항공": "003490",
            "아시아나항공": "020560",
            "현대상선": "011200",
            "HMM": "011200",
            
            # 철강/조선
            "HD한국조선해양": "009540",
            "한국조선해양": "009540",
            "HD현대중공업": "329180",  # HD현대중공업
            "현대중공업": "329180",
            "삼성중공업": "010140",
            "두산에너빌리티": "034020",
            
            # 기타
            "SK": "034730",
            "LG": "003550",
            "CJ": "001040",
            "롯데지주": "004990",
            "한화": "000880",
            "한화에어로스페이스": "012450"  # 한화에어로스페이스
        }
        
        # 별칭 처리를 위한 정규화 맵
        self.alias_map = {
            "삼성": "삼성전자",
            "SK하이닉스": "SK하이닉스",
            "현대": "현대차",
            "LG": "LG전자",
            "포스코": "POSCO홀딩스",
            "신한": "신한지주",
            "KB": "KB금융",
            "하나": "하나금융지주",
            "우리": "우리금융지주"
        }
    
    def normalize_company_name(self, name: str) -> str:
        """회사명 정규화"""
        # 공백 제거
        name = name.strip()
        
        # 괄호 내용 제거 (예: "삼성전자(주)" -> "삼성전자")
        name = re.sub(r'\([^)]*\)', '', name)
        
        # 주식회사, (주) 등 제거
        name = re.sub(r'주식회사|㈜|\(주\)', '', name)
        
        # 다시 공백 제거
        name = name.strip()
        
        return name
    
    def resolve_company_code(self, company_name: str) -> Optional[str]:
        """회사명으로 기업 코드 찾기"""
        
        # 1. 정규화
        normalized_name = self.normalize_company_name(company_name)
        
        # 2. 직접 매칭
        if normalized_name in self.company_map:
            return self.company_map[normalized_name]
        
        # 3. 별칭 매칭
        if normalized_name in self.alias_map:
            alias_name = self.alias_map[normalized_name]
            if alias_name in self.company_map:
                return self.company_map[alias_name]
        
        # 4. 부분 매칭 (포함 관계)
        for company, code in self.company_map.items():
            if normalized_name in company or company in normalized_name:
                return code
        
        # 5. 영어/한글 변환 시도
        english_korean_map = {
            "samsung": "삼성전자",
            "sk": "SK하이닉스", 
            "hyundai": "현대차",
            "lg": "LG전자",
            "naver": "NAVER",
            "kakao": "카카오",
            "posco": "POSCO홀딩스",
            "kt": "KT"
        }
        
        normalized_lower = normalized_name.lower()
        for eng, kor in english_korean_map.items():
            if eng in normalized_lower:
                if kor in self.company_map:
                    return self.company_map[kor]
        
        return None
    
    def resolve_multiple_companies(self, company_names: List[str]) -> List[Dict[str, str]]:
        """여러 회사명을 한번에 변환"""
        results = []
        
        for name in company_names:
            corp_code = self.resolve_company_code(name)
            if corp_code:
                results.append({
                    "corp_code": corp_code,
                    "corp_name": name.strip(),
                    "normalized_name": self.normalize_company_name(name)
                })
            else:
                # 실패한 경우도 기록 (나중에 사용자에게 알림)
                results.append({
                    "corp_code": None,
                    "corp_name": name.strip(),
                    "normalized_name": self.normalize_company_name(name),
                    "error": "기업 코드를 찾을 수 없습니다"
                })
        
        return results
    
    def get_available_companies(self) -> List[str]:
        """사용 가능한 회사 리스트 반환"""
        return sorted(self.company_map.keys())
    
    def search_companies(self, keyword: str) -> List[str]:
        """키워드로 회사 검색"""
        keyword = keyword.strip().lower()
        matches = []
        
        for company in self.company_map.keys():
            if keyword in company.lower():
                matches.append(company)
        
        return sorted(matches)

# 전역 인스턴스
company_resolver = CompanyResolver() 