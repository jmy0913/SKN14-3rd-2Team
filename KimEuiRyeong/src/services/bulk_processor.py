import asyncio
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from dataclasses import dataclass

from ..clients.dart_client import DartClient
from ..processors.document_processor import DocumentProcessor
from ..services.document_service import DocumentService

@dataclass
class ProcessingJob:
    """처리 작업 정보"""
    corp_code: str
    corp_name: str
    year: int
    status: str = "pending"  # pending, processing, completed, failed
    error_message: Optional[str] = None
    document_count: int = 0

class BulkProcessor:
    """대량 기업 데이터 처리 클래스"""
    
    def __init__(self, dart_client: DartClient, document_service: DocumentService, 
                 max_workers: int = 5, delay_between_requests: float = 1.0,
                 essential_only: bool = True):
        self.dart_client = dart_client
        self.document_service = document_service
        self.max_workers = max_workers
        self.delay_between_requests = delay_between_requests
        self.essential_only = essential_only  # 필수 섹션만 처리할지 여부
        self.logger = logging.getLogger(__name__)
        
    def process_multiple_companies(self, 
                                 company_list: List[Dict[str, str]], 
                                 years: List[int],
                                 batch_size: int = 10) -> List[ProcessingJob]:
        """
        여러 기업의 여러 년도 데이터를 배치로 처리
        
        Args:
            company_list: [{"corp_code": "005930", "corp_name": "삼성전자"}, ...]
            years: [2021, 2022, 2023]
            batch_size: 한 번에 처리할 작업 수
        """
        
        # 모든 작업 생성
        jobs = []
        for company in company_list:
            for year in years:
                job = ProcessingJob(
                    corp_code=company["corp_code"],
                    corp_name=company["corp_name"],
                    year=year
                )
                jobs.append(job)
        
        self.logger.info(f"총 {len(jobs)}개 작업 생성 완료")
        
        # 배치 단위로 처리
        completed_jobs = []
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            self.logger.info(f"배치 {i//batch_size + 1} 처리 중... ({len(batch)}개 작업)")
            
            batch_results = self._process_batch(batch)
            completed_jobs.extend(batch_results)
            
            # 배치 간 딜레이
            if i + batch_size < len(jobs):
                time.sleep(self.delay_between_requests * 2)
                
        return completed_jobs
    
    def _process_batch(self, jobs: List[ProcessingJob]) -> List[ProcessingJob]:
        """배치 단위로 작업 처리"""
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_job = {
                executor.submit(self._process_single_job, job): job 
                for job in jobs
            }
            
            completed_jobs = []
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                try:
                    result = future.result()
                    completed_jobs.append(result)
                    self.logger.info(f"완료: {job.corp_name} ({job.year}) - {result.document_count}개 문서")
                except Exception as e:
                    job.status = "failed"
                    job.error_message = str(e)
                    completed_jobs.append(job)
                    self.logger.error(f"실패: {job.corp_name} ({job.year}) - {e}")
                
                # 요청 간 딜레이
                time.sleep(self.delay_between_requests)
        
        return completed_jobs
    
    def _process_single_job(self, job: ProcessingJob) -> ProcessingJob:
        """단일 작업 처리"""
        try:
            job.status = "processing"
            
            # 문서 생성 및 업로드 (성능 최적화)
            if self.essential_only:
                documents = self.document_service.create_essential_documents_only(
                    corp_name=job.corp_name,
                    year=job.year
                )
            else:
                documents = self.document_service.create_comprehensive_documents(
                    corp_name=job.corp_name,
                    year=job.year,
                    include_optional_sections=True
                )
            
            if documents:
                # Pinecone에 업로드
                success = self.document_service.upload_documents_to_vector_store(documents)
                if not success:
                    raise Exception("파인콘 업로드 실패")
                job.document_count = len(documents)
                job.status = "completed"
            else:
                job.status = "failed"
                job.error_message = "문서 생성 실패"
                
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            
        return job
    
    def get_processing_summary(self, jobs: List[ProcessingJob]) -> Dict:
        """처리 결과 요약"""
        summary = {
            "total_jobs": len(jobs),
            "completed": len([j for j in jobs if j.status == "completed"]),
            "failed": len([j for j in jobs if j.status == "failed"]),
            "total_documents": sum(j.document_count for j in jobs),
            "failed_jobs": [
                {"corp_name": j.corp_name, "year": j.year, "error": j.error_message}
                for j in jobs if j.status == "failed"
            ]
        }
        return summary
    
    def retry_failed_jobs(self, failed_jobs: List[ProcessingJob]) -> List[ProcessingJob]:
        """실패한 작업 재시도"""
        self.logger.info(f"{len(failed_jobs)}개 실패 작업 재시도")
        
        # 상태 초기화
        for job in failed_jobs:
            job.status = "pending"
            job.error_message = None
            job.document_count = 0
        
        return self._process_batch(failed_jobs) 