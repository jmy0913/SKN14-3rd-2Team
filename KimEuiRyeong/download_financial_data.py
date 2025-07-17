#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
20개 기업 2023년 재무 데이터 다운로드 스크립트
DART API를 통해 재무제표 CSV 파일을 다운로드
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict

# 프로젝트 루트를 Python path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import load_config
from src.rag.document_saver import DocumentSaver

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'download_financial_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class FinancialDataDownloader:
    """재무 데이터 다운로드 클래스"""
    
    def __init__(self):
        self.config = load_config()
        self.document_saver = DocumentSaver()
        self.logger = logging.getLogger(__name__)
        
        # 20개 기업 목록 (사용자가 언급한 순서대로)
        self.target_companies = [
            "삼성전자", "SK하이닉스", "삼성바이오로직스", "LG에너지솔루션", "KB금융",
            "현대차", "삼성전자우", "기아", "NAVER", "셀트리온",
            "두산에너빌리티", "한화에어로스페이스", "신한지주", "HD현대중공업", "삼성물산",
            "현대모비스", "삼성생명", "하나금융지주", "HMM", "POSCO홀딩스"
        ]
        
        self.target_year = 2023
        
    def validate_companies(self) -> List[Dict[str, str]]:
        """회사명을 기업코드로 변환하고 유효성 검증"""
        self.logger.info("회사명 → 기업코드 변환 시작")
        
        # 전체 기업 리스트 가져오기
        all_companies = self.document_saver.get_corp_code_list()
        self.logger.info(f"전체 기업 수: {len(all_companies)}개")
        
        valid_companies = []
        failed_companies = []
        
        for company_name in self.target_companies:
            # 기업명으로 찾기
            found = False
            for corp in all_companies:
                if corp['corp_name'] == company_name:
                    valid_companies.append({
                        "corp_code": corp['corp_code'],
                        "corp_name": corp['corp_name']
                    })
                    self.logger.info(f"✓ {company_name} → {corp['corp_code']}")
                    found = True
                    break
            
            if not found:
                failed_companies.append(company_name)
                self.logger.warning(f"✗ {company_name} → 변환 실패")
        
        self.logger.info(f"변환 결과: {len(valid_companies)}/{len(self.target_companies)} 성공")
        
        if failed_companies:
            self.logger.warning(f"실패한 기업들: {', '.join(failed_companies)}")
        
        return valid_companies
    
    def download_single_company(self, company_info: Dict[str, str]) -> bool:
        """단일 기업 재무 데이터 다운로드"""
        corp_name = company_info["corp_name"]
        corp_code = company_info["corp_code"]
        
        try:
            self.logger.info(f"🔄 {corp_name} ({corp_code}) {self.target_year}년 재무 데이터 다운로드 시작")
            
            # 재무제표 다운로드
            documents = self.document_saver.save_financial_reports_document([company_info])
            
            if documents:
                self.logger.info(f"✅ {corp_name} 재무 데이터 다운로드 완료")
                return True
            else:
                self.logger.warning(f"⚠️ {corp_name} 재무 데이터 없음")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ {corp_name} 다운로드 중 오류: {str(e)}")
            return False
    
    def download_all_companies(self) -> Dict:
        """모든 기업 재무 데이터 다운로드"""
        self.logger.info("🚀 20개 기업 2023년 재무 데이터 다운로드 시작")
        self.logger.info("=" * 60)
        
        # 회사명 검증
        valid_companies = self.validate_companies()
        
        if not valid_companies:
            self.logger.error("유효한 기업이 없습니다. 종료합니다.")
            return {"success": False, "message": "유효한 기업이 없습니다."}
        
        # 처리 계획 표시
        self.logger.info(f"📋 처리 계획:")
        self.logger.info(f"   - 대상 기업: {len(valid_companies)}개")
        self.logger.info(f"   - 대상 연도: {self.target_year}년")
        self.logger.info(f"   - 저장 위치: {self.config['rag_documents_folder_name']}/{self.config['financial_reports_folder_name']}")
        
        # 사용자 확인
        response = input("\n계속 진행하시겠습니까? (y/N): ").strip().lower()
        if response not in ['y', 'yes', '예']:
            self.logger.info("다운로드가 취소되었습니다.")
            return {"success": False, "message": "사용자가 취소했습니다."}
        
        # 다운로드 시작
        start_time = datetime.now()
        success_count = 0
        failed_companies = []
        
        self.logger.info(f"\n🔄 다운로드 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 60)
        
        for i, company_info in enumerate(valid_companies, 1):
            self.logger.info(f"\n[{i}/{len(valid_companies)}] {company_info['corp_name']} 처리 중...")
            
            success = self.download_single_company(company_info)
            
            if success:
                success_count += 1
            else:
                failed_companies.append(company_info['corp_name'])
            
            # 진행률 표시
            progress = (i / len(valid_companies)) * 100
            self.logger.info(f"진행률: {progress:.1f}% ({i}/{len(valid_companies)})")
            
            # 중간 통계
            if i % 5 == 0:
                self.logger.info(f"중간 통계: 성공 {success_count}개, 실패 {len(failed_companies)}개")
        
        # 완료 통계
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 다운로드 완료 통계")
        self.logger.info("=" * 60)
        self.logger.info(f"총 소요 시간: {duration}")
        self.logger.info(f"성공: {success_count}개")
        self.logger.info(f"실패: {len(failed_companies)}개")
        self.logger.info(f"성공률: {(success_count/len(valid_companies)*100):.1f}%")
        
        if failed_companies:
            self.logger.warning(f"실패한 기업들: {', '.join(failed_companies)}")
        
        return {
            "success": success_count > 0,
            "total_companies": len(valid_companies),
            "success_count": success_count,
            "failed_count": len(failed_companies),
            "failed_companies": failed_companies,
            "duration": str(duration),
            "target_year": self.target_year
        }
    
    def show_download_summary(self, result: Dict):
        """다운로드 결과 요약 표시"""
        print("\n" + "🎉" * 20)
        print("재무 데이터 다운로드 완료!")
        print("🎉" * 20)
        print(f"📅 대상 연도: {result['target_year']}년")
        print(f"🏢 총 기업 수: {result['total_companies']}개")
        print(f"✅ 성공: {result['success_count']}개")
        print(f"❌ 실패: {result['failed_count']}개")
        print(f"⏱️  소요 시간: {result['duration']}")
        
        if result['failed_companies']:
            print(f"\n⚠️  실패한 기업들:")
            for company in result['failed_companies']:
                print(f"   - {company}")
        
        print(f"\n💡 다음 단계:")
        print(f"   1. 파인콘 업로드: python upload_companies_2023.py")
        print(f"   2. Streamlit UI 실행: streamlit run src/streamlit_ui.py")

def main():
    """메인 실행 함수"""
    print("🚀 20개 기업 2023년 재무 데이터 다운로드")
    print("=" * 60)
    
    try:
        downloader = FinancialDataDownloader()
        result = downloader.download_all_companies()
        downloader.show_download_summary(result)
        
    except KeyboardInterrupt:
        print("\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        logging.error(f"메인 실행 중 오류: {e}", exc_info=True)

if __name__ == "__main__":
    main() 