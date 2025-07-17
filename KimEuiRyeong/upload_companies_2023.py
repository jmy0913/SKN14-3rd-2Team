#!/usr/bin/env python3
"""
2023년도 주요 기업 재무 데이터 대량 업로드 스크립트
리팩토링된 DocumentService와 BulkProcessor 사용
"""

import time
from typing import List, Dict

from src.clients.dart_client import DartClient  
from src.services.document_service import DocumentService
from src.services.bulk_processor import BulkProcessor

# 주요 기업 리스트 (2023년 CSV 파일이 있는 기업들)
MAJOR_COMPANIES = [
    {"corp_code": "005930", "corp_name": "삼성전자"},
    {"corp_code": "000660", "corp_name": "SK하이닉스"},
    {"corp_code": "035420", "corp_name": "NAVER"},
    {"corp_code": "005380", "corp_name": "현대차"},
    {"corp_code": "000270", "corp_name": "기아"},
    {"corp_code": "012330", "corp_name": "현대모비스"},
    {"corp_code": "051910", "corp_name": "LG화학"},
    {"corp_code": "006400", "corp_name": "삼성SDI"},
    {"corp_code": "207940", "corp_name": "삼성바이오로직스"},
    {"corp_code": "068270", "corp_name": "셀트리온"},
    {"corp_code": "005490", "corp_name": "POSCO홀딩스"},
    {"corp_code": "105560", "corp_name": "KB금융"},
    {"corp_code": "055550", "corp_name": "신한지주"},
    {"corp_code": "086790", "corp_name": "하나금융지주"},
    {"corp_code": "010950", "corp_name": "S-Oil"},
    {"corp_code": "003670", "corp_name": "포스코퓨처엠"},
    {"corp_code": "009540", "corp_name": "HD한국조선해양"},
    {"corp_code": "011070", "corp_name": "LG이노텍"},
    {"corp_code": "028260", "corp_name": "삼성물산"},
    {"corp_code": "096770", "corp_name": "SK이노베이션"}
]

def main():
    print("🚀 2023년도 주요 기업 재무 데이터 대량 업로드")
    print("=" * 60)
    
    # 처리 설정
    years = [2023]
    batch_size = 5  # 한 번에 처리할 기업 수
    max_workers = 3  # 동시 처리 스레드 수
    
    print(f"📊 처리 대상:")
    print(f"  • 기업 수: {len(MAJOR_COMPANIES)}개")
    print(f"  • 연도: {years}")
    print(f"  • 배치 크기: {batch_size}")
    print(f"  • 최대 워커: {max_workers}")
    print(f"  • 처리 방식: 필수 섹션만 (성능 최적화)")
    
    print(f"\n시작하시겠습니까? (y/N): ", end="")
    
    try:
        response = input().strip().lower()
        if response not in ['y', 'yes']:
            print("업로드가 취소되었습니다.")
            return
    except KeyboardInterrupt:
        print("\n업로드가 중단되었습니다.")
        return
    
    # 시작 시간 기록
    start_time = time.time()
    
    try:
        # 서비스 초기화
        print(f"\n🔧 서비스 초기화 중...")
        dart_client = DartClient()
        document_service = DocumentService()
        
        # BulkProcessor 초기화 (필수 섹션만 처리)
        processor = BulkProcessor(
            dart_client=dart_client,
            document_service=document_service,
            max_workers=max_workers,
            delay_between_requests=2.0,  # API 안정성을 위해 2초 딜레이
            essential_only=True  # 필수 섹션만 처리
        )
        
        # 현재 파인콘 상태 확인
        print(f"\n📊 업로드 전 파인콘 상태:")
        before_stats = document_service.get_vector_store_stats()
        before_count = before_stats.get('total_vector_count', 0)
        print(f"  • 현재 벡터 수: {before_count:,}개")
        
        # 대량 처리 시작
        print(f"\n🚀 대량 처리 시작...")
        print(f"예상 처리 시간: 약 {len(MAJOR_COMPANIES) * 2:.0f}분")
        
        jobs = processor.process_multiple_companies(
            company_list=MAJOR_COMPANIES,
            years=years,
            batch_size=batch_size
        )
        
        # 처리 시간 계산
        total_time = time.time() - start_time
        
        # 결과 요약
        summary = processor.get_processing_summary(jobs)
        
        print(f"\n" + "=" * 60)
        print(f"📊 처리 결과 요약")
        print(f"=" * 60)
        print(f"  • 총 작업 수: {summary['total_jobs']}")
        print(f"  • 성공: {summary['completed']}")
        print(f"  • 실패: {summary['failed']}")
        print(f"  • 총 문서 수: {summary['total_documents']:,}")
        print(f"  • 처리 시간: {total_time:.1f}초 ({total_time/60:.1f}분)")
        print(f"  • 평균 처리 시간: {total_time/len(MAJOR_COMPANIES):.1f}초/기업")
        
        # 실패한 작업 정보
        if summary['failed_jobs']:
            print(f"\n❌ 실패한 작업 ({len(summary['failed_jobs'])}개):")
            for job in summary['failed_jobs']:
                print(f"  • {job['corp_name']} {job['year']}: {job['error']}")
        
        # 업로드 후 파인콘 상태 확인
        if summary['completed'] > 0:
            print(f"\n📊 업로드 후 파인콘 상태:")
            after_stats = document_service.get_vector_store_stats()
            after_count = after_stats.get('total_vector_count', 0)
            added_count = after_count - before_count
            
            print(f"  • 현재 벡터 수: {after_count:,}개")
            print(f"  • 추가된 벡터: {added_count:,}개")
            
            # 업로드 검증
            validation = document_service.validate_upload_success(summary['total_documents'])
            if validation.get('meets_expectation'):
                print(f"  ✅ 업로드 검증: 성공")
            else:
                print(f"  ⚠️ 업로드 검증: 경고 - 예상보다 적은 벡터 수")
        
        # 성공률 계산
        success_rate = (summary['completed'] / summary['total_jobs']) * 100 if summary['total_jobs'] > 0 else 0
        
        print(f"\n🎯 성과 요약:")
        print(f"  • 성공률: {success_rate:.1f}%")
        print(f"  • 문서 생성 속도: {summary['total_documents']/total_time:.1f}개/초")
        print(f"  • 기업당 평균 문서 수: {summary['total_documents']/summary['completed']:.1f}개" if summary['completed'] > 0 else "")
        
        if success_rate >= 80:
            print(f"\n🎉 업로드 성공! 파인콘에 {summary['total_documents']:,}개 문서가 저장되었습니다.")
        else:
            print(f"\n⚠️ 일부 실패가 있었지만 {summary['completed']}개 기업 업로드 완료")
        
        # 재시도 옵션
        if summary['failed_jobs'] and len(summary['failed_jobs']) <= 5:
            print(f"\n실패한 작업을 재시도하시겠습니까? (y/N): ", end="")
            try:
                retry_response = input().strip().lower()
                if retry_response in ['y', 'yes']:
                    print(f"\n🔄 실패한 작업 재시도 중...")
                    failed_jobs = [job for job in jobs if job.status == "failed"]
                    retry_jobs = processor.retry_failed_jobs(failed_jobs)
                    retry_summary = processor.get_processing_summary(retry_jobs)
                    
                    print(f"재시도 결과: {retry_summary['completed']}/{retry_summary['total_jobs']} 성공")
            except KeyboardInterrupt:
                print("\n재시도가 중단되었습니다.")
        
    except Exception as e:
        print(f"\n❌ 업로드 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print(f"\n업로드 스크립트 종료")


if __name__ == "__main__":
    main() 