"""
문서 서비스 모듈
문서 생성, 처리, 관리에 대한 비즈니스 로직
"""

from typing import List, Optional
from langchain_core.documents import Document

from src.processors.document_processor import DocumentProcessor
from src.rag.vector_store import VectorStore
from src.config import VECTOR_STORE_INDEX_NAME


class DocumentService:
    """문서 관련 서비스"""
    
    def __init__(self):
        self.processor = DocumentProcessor()
        index_name = VECTOR_STORE_INDEX_NAME or "financial-reports"
        self.vector_store = VectorStore(index_name)
    
    def create_comprehensive_documents(self, corp_name: str, year: int, 
                                     include_optional_sections: bool = False) -> List[Document]:
        """기업의 종합적인 문서를 생성합니다.
        
        Args:
            corp_name: 기업명
            year: 연도
            include_optional_sections: 선택적 섹션 포함 여부 (기본값: False)
        """
        print(f"[INFO] {corp_name} {year}년 종합 문서 생성 시작")
        
        all_documents = []
        
        # === 핵심 필수 섹션들 ===
        
        # 1. 재무제표 데이터 (CSV) - 가장 중요
        print(f"[INFO] 재무제표 데이터 처리 중...")
        financial_docs = self.processor.process_financial_data_from_csv(corp_name, year)
        all_documents.extend(financial_docs)
        print(f"[SUCCESS] 재무제표 문서 {len(financial_docs)}개 생성")
        
        # 2. 제1장 회사의 개요 - 기업 기본 정보
        print(f"[INFO] 제1장 회사의 개요 처리 중...")
        chapter1_docs = self.processor.process_chapter1_company_overview(corp_name, year)
        all_documents.extend(chapter1_docs)
        print(f"[SUCCESS] 회사 개요 문서 {len(chapter1_docs)}개 생성")
        
        # 3. 제2장 사업의 내용 - 핵심 사업 정보
        print(f"[INFO] 제2장 사업의 내용 처리 중...")
        chapter2_docs = self.processor.process_chapter2_business_content(corp_name, year)
        all_documents.extend(chapter2_docs)
        print(f"[SUCCESS] 사업 내용 문서 {len(chapter2_docs)}개 생성")
        
        # 4. 제3장 재무에 관한 사항 - 재무 정보
        print(f"[INFO] 제3장 재무에 관한 사항 처리 중...")
        chapter3_docs = self.processor.process_chapter3_financial_matters(corp_name, year)
        all_documents.extend(chapter3_docs)
        print(f"[SUCCESS] 재무 사항 문서 {len(chapter3_docs)}개 생성")
        
        # 5. 주요사항 - 핵심 지표
        print(f"[INFO] 주요사항 처리 중...")
        key_matters_docs = self.processor.process_key_matters(corp_name, year)
        all_documents.extend(key_matters_docs)
        print(f"[SUCCESS] 주요사항 문서 {len(key_matters_docs)}개 생성")
        
        # === 선택적 섹션들 (성능 최적화를 위해 기본적으로 비활성화) ===
        if include_optional_sections:
            print(f"[INFO] 선택적 섹션들 처리 중...")
            
            # 주주 및 지배구조
            chapter4_docs = self.processor.process_chapter4_shareholders_governance(corp_name, year)
            all_documents.extend(chapter4_docs)
            
            # 주주 정보
            shareholder_docs = self.processor.process_shareholder_info(corp_name, year)
            all_documents.extend(shareholder_docs)
            
            # 임직원 현황
            employee_docs = self.processor.process_employee_status(corp_name, year)
            all_documents.extend(employee_docs)
            
            # 배당 정보
            dividend_docs = self.processor.process_dividend_info(corp_name, year)
            all_documents.extend(dividend_docs)
            
            print(f"[SUCCESS] 선택적 섹션 처리 완료")
        
        print(f"[SUCCESS] 총 {len(all_documents)}개 문서 생성 완료")
        return all_documents
    
    def create_essential_documents_only(self, corp_name: str, year: int) -> List[Document]:
        """필수 섹션만으로 빠른 문서 생성 (재무제표 + 기본 사업 정보)"""
        print(f"[INFO] {corp_name} {year}년 필수 문서만 생성 시작")
        
        all_documents = []
        
        # 1. 재무제표 데이터 (가장 중요)
        financial_docs = self.processor.process_financial_data_from_csv(corp_name, year)
        all_documents.extend(financial_docs)
        
        # 2. 회사 개요
        chapter1_docs = self.processor.process_chapter1_company_overview(corp_name, year)
        all_documents.extend(chapter1_docs)
        
        # 3. 주요사항
        key_matters_docs = self.processor.process_key_matters(corp_name, year)
        all_documents.extend(key_matters_docs)
        
        print(f"[SUCCESS] 필수 문서 {len(all_documents)}개 생성 완료")
        return all_documents
    
    def upload_documents_to_vector_store(self, documents: List[Document]) -> bool:
        """문서들을 벡터 스토어에 업로드합니다."""
        if not documents:
            print("[WARNING] 업로드할 문서가 없습니다.")
            return False
            
        try:
            print(f"[INFO] 벡터 스토어 준비 중...")
            self.vector_store.get_index_ready()
            
            print(f"[INFO] {len(documents)}개 문서 업로드 중...")
            success_count = 0
            failed_count = 0
            
            for i, doc in enumerate(documents, 1):
                try:
                    # 메타데이터 정리 및 검증
                    cleaned_metadata = self._clean_metadata(doc.metadata)
                    
                    # 문서 내용 검증 강화
                    content = doc.page_content.strip()
                    if not content or len(content) < 20:
                        print(f"[WARNING] 문서 {i}: 내용이 너무 짧아 건너뜀 (길이: {len(content)})")
                        failed_count += 1
                        continue
                    
                    # 무의미한 내용 필터링
                    if self._is_meaningless_content(content):
                        print(f"[WARNING] 문서 {i}: 무의미한 내용으로 건너뜀")
                        failed_count += 1
                        continue
                    
                    cleaned_doc = Document(
                        page_content=content,
                        metadata=cleaned_metadata
                    )
                    
                    self.vector_store.add_documents_to_index([cleaned_doc])
                    success_count += 1
                    
                    if i % 10 == 0:
                        print(f"[PROGRESS] {i}/{len(documents)} 문서 업로드 완료")
                        
                except Exception as e:
                    print(f"[ERROR] 문서 {i} 업로드 실패: {e}")
                    failed_count += 1
                    continue
            
            print(f"[SUCCESS] {success_count}/{len(documents)}개 문서 업로드 완료")
            if failed_count > 0:
                print(f"[WARNING] {failed_count}개 문서 업로드 실패")
            
            return success_count > 0
            
        except Exception as e:
            print(f"[ERROR] 벡터 스토어 업로드 실패: {e}")
            return False
    
    def _is_meaningless_content(self, content: str) -> bool:
        """문서 내용이 무의미한지 확인합니다."""
        # 빈 값들로만 구성된 내용 체크
        meaningless_patterns = [
            "당기: -\n전기: -\n전전기: -",
            "당기: 해당없음",
            "전기: 해당없음", 
            "전전기: 해당없음",
            "당기: 0\n전기: 0\n전전기: 0",
            "금액: 0원"
        ]
        
        for pattern in meaningless_patterns:
            if pattern in content:
                return True
        
        # 대부분이 "-" 문자인 경우
        dash_count = content.count('-')
        if dash_count > len(content) * 0.3:  # 30% 이상이 -인 경우
            return True
        
        # 실제 숫자나 의미있는 단어가 거의 없는 경우
        import re
        meaningful_content = re.sub(r'[-\s\n당기전기전전기항목:]', '', content)
        if len(meaningful_content) < 10:
            return True
            
        return False
    
    def _clean_metadata(self, metadata: dict) -> dict:
        """메타데이터를 정리합니다."""
        cleaned_metadata = {}
        for key, value in metadata.items():
            # None 값 처리
            if value is None:
                cleaned_metadata[key] = ""
            # 문자열로 변환
            elif isinstance(value, (int, float)):
                cleaned_metadata[key] = str(value)
            elif isinstance(value, str):
                cleaned_metadata[key] = value.strip()
            else:
                cleaned_metadata[key] = str(value)
        return cleaned_metadata
    
    def validate_upload_success(self, expected_count: int) -> dict:
        """업로드 성공 여부를 검증합니다."""
        try:
            stats = self.get_vector_store_stats()
            current_count = stats.get('total_vector_count', 0)
            
            validation_result = {
                "success": current_count > 0,
                "current_vector_count": current_count,
                "expected_minimum": expected_count,
                "meets_expectation": current_count >= expected_count * 0.8,  # 80% 이상 성공하면 OK
                "stats": stats
            }
            
            if validation_result["meets_expectation"]:
                print(f"[SUCCESS] 업로드 검증 성공: {current_count}개 벡터 존재")
            else:
                print(f"[WARNING] 업로드 검증 실패: 예상 {expected_count}개, 실제 {current_count}개")
                
            return validation_result
            
        except Exception as e:
            print(f"[ERROR] 업로드 검증 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def search_documents(self, query: str, k: int = 5) -> List[Document]:
        """문서를 검색합니다."""
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            print(f"[ERROR] 문서 검색 실패: {e}")
            return []
    
    def get_vector_store_stats(self) -> dict:
        """벡터 스토어 통계를 가져옵니다."""
        return self.vector_store.get_index_stats()
    
    def clear_vector_store(self) -> bool:
        """벡터 스토어를 비웁니다."""
        try:
            self.vector_store.delete_all_vectors()
            return True
        except Exception as e:
            print(f"[ERROR] 벡터 스토어 삭제 실패: {e}")
            return False 