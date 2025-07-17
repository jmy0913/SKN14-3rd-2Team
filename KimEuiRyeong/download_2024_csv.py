`#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2024년도 재무제표 CSV 파일 다운로드 스크립트
"""

import os
import sys
from typing import List

# 프로젝트 루트를 Python path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.rag.document_saver import DocumentSaver

def download_2024_financial_csv():
    """2024년도 재무제표 CSV 파일만 다운로드"""
    print("=" * 60)
    print("2024년도 재무제표 CSV 파일 다운로드 시작")
    print("=" * 60)
    
    # 20개 기업 리스트
    companies = [
        "삼성전자", "SK하이닉스", "삼성바이오로직스", "LG에너지솔루션", "KB금융",
        "현대차", "기아", "NAVER", "셀트리온", "두산에너빌리티", 
        "한화에어로스페이스", "신한지주", "HD현대중공업", "삼성물산",
        "현대모비스", "삼성생명", "하나금융지주", "HMM", "POSCO홀딩스"
    ]
    
    document_saver = DocumentSaver()
    
    # 기업코드로 변환
    print("기업코드 변환 중...")
    corp_codes = []
    failed_companies = []
    
    for company in companies:
        corp_list = document_saver.get_corp_code_list()
        corp_info = None
        for corp in corp_list:
            if corp['corp_name'] == company:
                corp_info = corp
                break
        
        if corp_info:
            corp_codes.append(corp_info)
            print(f"✅ {company} → {corp_info['corp_code']}")
        else:
            failed_companies.append(company)
            print(f"❌ {company} → 기업코드 찾기 실패")
    
    if failed_companies:
        print(f"\n⚠️ 실패한 기업들: {', '.join(failed_companies)}")
    
    # 2024년도 재무제표 다운로드
    print(f"\n📥 2024년도 재무제표 CSV 다운로드 중...")
    print(f"대상: {len(corp_codes)}개 기업")
    
    try:
        saved_documents = document_saver.save_financial_reports_document(
            corp_codes, 
            year=2024
        )
        
        print(f"\n✅ 다운로드 완료!")
        print(f"📊 성공: {len(saved_documents)}개 기업")
        
        # 다운로드된 파일 목록 확인
        csv_dir = os.path.join("rag_documents_folder", "financial_reports")
        if os.path.exists(csv_dir):
            csv_files = [f for f in os.listdir(csv_dir) if f.endswith('_2024_재무제표.csv')]
            print(f"\n📁 다운로드된 2024년 CSV 파일들:")
            for csv_file in sorted(csv_files):
                file_path = os.path.join(csv_dir, csv_file)
                file_size = os.path.getsize(file_path) / 1024  # KB
                print(f"   - {csv_file} ({file_size:.1f} KB)")
        
        return saved_documents
        
    except Exception as e:
        print(f"\n❌ 다운로드 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return []

def check_existing_2024_csv():
    """기존 2024년도 CSV 파일 확인"""
    print("=" * 60)
    print("기존 2024년도 CSV 파일 확인")
    print("=" * 60)
    
    csv_dir = os.path.join("rag_documents_folder", "financial_reports")
    if not os.path.exists(csv_dir):
        print("❌ CSV 디렉토리가 존재하지 않습니다.")
        return []
    
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('_2024_재무제표.csv')]
    
    if csv_files:
        print(f"✅ 기존 2024년도 CSV 파일 {len(csv_files)}개 발견:")
        for csv_file in sorted(csv_files):
            file_path = os.path.join(csv_dir, csv_file)
            file_size = os.path.getsize(file_path) / 1024  # KB
            print(f"   - {csv_file} ({file_size:.1f} KB)")
    else:
        print("❌ 2024년도 CSV 파일이 없습니다.")
    
    return csv_files

def main():
    """메인 실행 함수"""
    print("🚀 2024년도 재무제표 CSV 다운로드 시작")
    
    # 1단계: 기존 파일 확인
    existing_files = check_existing_2024_csv()
    
    if existing_files:
        response = input(f"\n기존 2024년도 CSV 파일이 {len(existing_files)}개 있습니다. 다시 다운로드하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("다운로드를 취소했습니다.")
            return
    
    # 2단계: 새로 다운로드
    download_2024_financial_csv()
    
    print("\n🎉 2024년도 CSV 다운로드 완료!")

if __name__ == "__main__":
    main() 