#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대량 처리 설정 모듈
.env 파일에서 회사명/년도를 읽어서 처리하는 설정
"""

import os
from typing import List, Dict, Optional
from .services.company_resolver import company_resolver

# 환경변수 로드
TARGET_COMPANIES = os.environ.get("TARGET_COMPANIES", "")
TARGET_YEARS = os.environ.get("TARGET_YEARS", "")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "3"))
DELAY_BETWEEN_REQUESTS = float(os.environ.get("DELAY_BETWEEN_REQUESTS", "2.0"))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "5"))

def get_target_companies_from_env() -> List[Dict[str, str]]:
    """
    환경변수에서 대상 회사 리스트를 파싱하여 반환
    회사명만 있어도 자동으로 기업코드 찾아줌
    """
    if not TARGET_COMPANIES.strip():
        return []
    
    # 쉼표로 분리
    company_inputs = [comp.strip() for comp in TARGET_COMPANIES.split(",") if comp.strip()]
    
    results = []
    failed_companies = []
    
    for company_input in company_inputs:
        # 1. 6자리 숫자면 기업코드로 간주
        if company_input.isdigit() and len(company_input) == 6:
            results.append({
                "corp_code": company_input,
                "corp_name": f"기업_{company_input}"  # 기업명 모를 때 임시명
            })
        else:
            # 2. 회사명으로 간주하고 기업코드 찾기
            corp_code = company_resolver.resolve_company_code(company_input)
            if corp_code:
                results.append({
                    "corp_code": corp_code,
                    "corp_name": company_input
                })
            else:
                failed_companies.append(company_input)
    
    # 실패한 회사들 알림
    if failed_companies:
        print(f"⚠️  다음 회사들의 기업코드를 찾을 수 없습니다: {', '.join(failed_companies)}")
        print("💡 사용 가능한 회사명 확인: python -c \"from src.services.company_resolver import company_resolver; print('\\n'.join(company_resolver.get_available_companies()[:20]))\"")
    
    return results

def get_target_years_from_env() -> List[int]:
    """환경변수에서 대상 년도 리스트를 파싱하여 반환"""
    year_str = TARGET_YEARS.strip()
    if not year_str:
        return [2023]  # 기본값
    
    try:
        years = [int(year.strip()) for year in year_str.split(",") if year.strip().isdigit()]
        return years if years else [2023]
    except ValueError:
        return [2023]  # 파싱 실패 시 기본값

def get_bulk_processing_settings() -> Dict:
    """대량 처리 성능 설정 반환"""
    return {
        "max_workers": MAX_WORKERS,
        "delay_between_requests": DELAY_BETWEEN_REQUESTS,
        "batch_size": BATCH_SIZE
    }

def validate_env_settings() -> Dict:
    """환경변수 설정 검증"""
    companies = get_target_companies_from_env()
    years = get_target_years_from_env()
    settings = get_bulk_processing_settings()
    
    validation_result = {
        "valid": True,
        "companies": companies,
        "years": years,
        "settings": settings,
        "errors": [],
        "warnings": []
    }
    
    # 검증
    if not companies:
        validation_result["valid"] = False
        validation_result["errors"].append("TARGET_COMPANIES가 설정되지 않았거나 올바르지 않습니다")
    
    if not years:
        validation_result["warnings"].append("TARGET_YEARS가 설정되지 않아 기본값(2023)을 사용합니다")
    
    if not (1 <= settings["max_workers"] <= 10):
        validation_result["warnings"].append(f"MAX_WORKERS({settings['max_workers']})가 권장 범위(1-10)를 벗어났습니다")
    
    if not (0.5 <= settings["delay_between_requests"] <= 5.0):
        validation_result["warnings"].append(f"DELAY_BETWEEN_REQUESTS({settings['delay_between_requests']})가 권장 범위(0.5-5.0)를 벗어났습니다")
    
    if not (1 <= settings["batch_size"] <= 20):
        validation_result["warnings"].append(f"BATCH_SIZE({settings['batch_size']})가 권장 범위(1-20)를 벗어났습니다")
    
    return validation_result 