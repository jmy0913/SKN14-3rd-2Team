# Korean Financial RAG System

한국 기업 재무/사업 보고서 기반 RAG(Retrieval-Augmented Generation) 시스템

## 🚀 주요 기능

- **회사명 기반 설정**: 기업코드를 몰라도 회사 이름만으로 간편 설정
- **대량 처리**: 30-40개 기업의 여러 년도 데이터를 자동으로 처리
- **포괄적 데이터**: 사업보고서의 모든 주요 섹션 지원 (15개 섹션)
- **Streamlit UI**: 사용자 친화적인 웹 인터페이스 + 대화 저장 기능
- **벡터 검색**: Pinecone 기반 의미론적 검색

## 📁 프로젝트 구조

```
skn-3rd-project/
├── src/                           # 핵심 소스코드
│   ├── clients/                   # 외부 API 클라이언트
│   ├── processors/                # 데이터 처리
│   ├── services/                  # 비즈니스 로직
│   ├── rag/                      # RAG 관련 모듈
│   ├── tools/                    # 유틸리티
│   ├── config.py                 # 기본 설정
│   ├── bulk_config.py            # 대량 처리 설정
│   ├── llm.py                    # LLM 인터페이스
│   ├── orchestrator.py           # 메인 오케스트레이터
│   └── streamlit_ui.py           # Streamlit UI
├── tests/                        # 테스트 파일들
├── bulk_processing_from_env.py   # 🎯 메인 실행 스크립트
├── company_list_manager.py       # 회사 리스트 관리
├── requirements.txt              # 패키지 의존성
└── README.md                     # 이 파일
```

## ⚡ 빠른 시작

### 1. 환경 설정

```bash
# 패키지 설치
pip install -r requirements.txt

# .env 파일 생성 (프로젝트 루트에)
# 아래 내용 참고하여 API 키들 설정
```

### 2. .env 파일 설정

```bash
# API 키 설정
OPENAI_KEY=your_openai_api_key_here
PINECONE_KEY=your_pinecone_api_key_here
DART_API_KEY=your_dart_api_key_here

# 기본 설정
MODEL_NAME=gpt-4o-mini
EMBEDDING_MODEL_NAME=text-embedding-3-small
VECTOR_STORE_INDEX_NAME=financial-reports
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# 🎉 회사명으로 간편 설정!
TARGET_COMPANIES=삼성전자,현대차,LG화학,NAVER,카카오
TARGET_YEARS=2021,2022,2023

# 성능 설정
MAX_WORKERS=3
DELAY_BETWEEN_REQUESTS=2.0
BATCH_SIZE=5
```

### 3. 시스템 테스트

```bash
# 빠른 전체 시스템 체크
python tests/quick_test.py
```

### 4. 대량 데이터 처리

```bash
# .env 설정 기반 자동 처리
python bulk_processing_from_env.py
```

### 5. Streamlit UI 실행

```bash
# 웹 인터페이스 시작
streamlit run src/streamlit_ui.py
```

## 🏢 지원하는 회사들

### 대기업
삼성전자, SK하이닉스, 현대차, LG화학, 삼성바이오로직스, 셀트리온, NAVER, 현대모비스, 기아, LG전자

### IT/게임  
NAVER, 카카오, 엔씨소프트, 넷마블, 삼성에스디에스

### 금융
신한지주, KB금융, 하나금융지주, 우리금융지주, 삼성화재

### 바이오/제약
삼성바이오로직스, 셀트리온, 셀트리온헬스케어, SK바이오팜, 한미약품

### 총 30 + 개 주요 상장기업

> 💡 **전체 리스트 확인**: `python tests/test_company_resolver.py`

## 📋 지원하는 사업보고서 섹션

### 🎯 15개 주요 섹션 완전 지원

1. **💰 재무에 관한 사항**
   - 요약재무정보, 연결/별도재무제표, 주요 재무지표

2. **🏢 회사개요**
   - 기업 기본정보, 사업 영역

3. **📊 사업의 내용**
   - 주요 사업 분야, 매출 구성, 제품/서비스

4. **🔬 연구개발 활동**
   - 연구개발 투자, 주요 연구 분야, 성과

5. **📝 주요 계약 및 거래**
   - 공급계약, 구매계약, 특수관계자 거래

6. **👥 주요 주주 현황**
   - 일반 주주현황, 최대주주 및 특수관계인 현황

7. **💼 임원 및 직원 현황**
   - 부문별 임직원 수, 근속연수, 성별 구성

8. **🏛️ 이사회 및 감사기구 현황**
   - 이사회 구성, 감사위원회, 독립성 확보

9. **💎 배당에 관한 사항**
   - 배당 정책, 배당 이력, 배당 계획

10. **🔄 합병·분할 등 주요 경영사항**
    - 합병/인수, 분할/분사, 조직 개편

11. **⚖️ 소송 및 분쟁 현황**
    - 진행 중인 소송, 소송 충당금, 리스크 관리

12. **📋 내부회계관리제도 운영실태**
    - 제도 운영 현황, 외부감사인 검토

13. **🌱 ESG(환경·사회·지배구조) 정보**
    - 환경 활동, 사회 공헌, 지배구조 개선

14. **📄 기타 중요사항**
    - 공시책임자, 감사보고서, 주주총회 의결사항

15. **🔍 주요사항**
    - 기타 중요한 경영 현황

## 🔧 사용법

### 기본 사용법

```bash
# 1. 설정 확인
python tests/quick_test.py

# 2. 대량 처리 실행 (15개 섹션 모두 처리)
python bulk_processing_from_env.py

# 3. UI에서 검색 테스트
streamlit run src/streamlit_ui.py
```

### 고급 사용법

```bash
# 특정 회사들만 처리하고 싶을 때
# .env 파일에서 TARGET_COMPANIES 수정 후
python bulk_processing_from_env.py

# 회사명 변환 기능 테스트
python tests/test_company_resolver.py

# 환경변수 설정 검증
python tests/test_env_config.py
```

## 📊 데이터 처리 예시

### 설정 예시 1: IT 대기업
```bash
TARGET_COMPANIES=삼성전자,NAVER,카카오,엔씨소프트
TARGET_YEARS=2021,2022,2023
```
→ 4개 회사 × 3년 = 12개 작업, 약 780개 문서 생성

### 설정 예시 2: 바이오 섹터
```bash
TARGET_COMPANIES=삼성바이오로직스,셀트리온,SK바이오팜
TARGET_YEARS=2022,2023
```
→ 3개 회사 × 2년 = 6개 작업, 약 390개 문서 생성

### 설정 예시 3: 대량 처리
```bash
TARGET_COMPANIES=삼성전자,현대차,LG화학,NAVER,카카오,신한지주,KB금융,셀트리온,SK바이오팜,포스코
TARGET_YEARS=2021,2022,2023
```
→ 10개 회사 × 3년 = 30개 작업, 약 1,950개 문서 생성

## 🔍 테스트 가이드

자세한 테스트 방법은 [`tests/README.md`](tests/README.md)를 참고하세요.

### 빠른 테스트
```bash
python tests/quick_test.py  # 1분 안에 전체 시스템 확인
```

### 문제 해결
```bash
python tests/test_company_resolver.py  # 회사명 변환 문제
python tests/test_env_config.py        # 설정 파일 문제
```

## ⚙️ 설정 커스터마이징

### 성능 튜닝
```bash
# 빠른 처리 (API 제한 주의)
MAX_WORKERS=5
DELAY_BETWEEN_REQUESTS=1.0
BATCH_SIZE=8

# 안정적 처리 (권장)
MAX_WORKERS=3
DELAY_BETWEEN_REQUESTS=2.0
BATCH_SIZE=5

# 신중한 처리 (API 제한 걱정 시)
MAX_WORKERS=2
DELAY_BETWEEN_REQUESTS=3.0
BATCH_SIZE=3
```

### 회사 설정 방법
```bash
# 1. 회사명 사용 (추천!)
TARGET_COMPANIES=삼성전자,현대차,LG화학

# 2. 기업코드 사용 (기존 방식)
TARGET_COMPANIES=005930,005380,051910

# 3. 혼합 사용
TARGET_COMPANIES=삼성전자,005380,LG화학
```

## 🚨 문제 해결

### 자주 발생하는 문제

**1. 회사명을 찾을 수 없습니다**
```bash
# 해결: 사용 가능한 회사명 확인
python tests/test_company_resolver.py
```

**2. API 요청 제한 오류**
```bash
# 해결: .env에서 딜레이 증가
DELAY_BETWEEN_REQUESTS=3.0
MAX_WORKERS=2
```

**3. 모듈 import 오류**
```bash
# 해결: 패키지 재설치
pip install -r requirements.txt
```

## 📈 성능 모니터링

### 처리 속도 예상치
- **소규모** (5개 회사 × 2년): 약 5분
- **중간규모** (10개 회사 × 3년): 약 15분  
- **대규모** (30개 회사 × 3년): 약 45분

### 생성 문서 수
- **회사당 연간**: 약 65개 문서 (재무 32개 + 사업보고서 33개)
- **총 벡터 수**: 문서 수 × 1.5 (청킹으로 인한 증가)

## 💡 팁 & 트릭

1. **단계적 확장**: 소수 회사로 테스트 → 점진적 확장
2. **섹터별 처리**: 비슷한 업종끼리 묶어서 처리
3. **로그 활용**: 실행 시 생성되는 로그 파일로 오류 분석
4. **정기 백업**: Pinecone 데이터 정기적으로 백업
5. **API 사용량 모니터링**: OpenAI, Pinecone 사용량 주기적 확인

## 🤝 기여하기

1. 새로운 회사 추가: `src/services/company_resolver.py` 수정
2. 새로운 기능 추가: 해당 모듈에 구현 + 테스트 추가
3. 버그 신고: 상세한 로그와 함께 이슈 등록

## 📄 라이선스

이 프로젝트는 개인 학습/연구 목적으로 제작되었습니다.
