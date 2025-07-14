# ADD by EUIRYEONG
from typing import List, Dict
import os
import zipfile
import requests

from langchain_core.documents import Document
import pandas as pd
import xml.etree.ElementTree as ET

from src.config import DART_API_KEY, RAG_DOCUMENTS_FOLDER_NAME, FINANCIAL_REPORTS_FOLDER_NAME

import dart_fss as dart

CORP_CODE_FILE_NAME = 'corpCode.zip'
ELEMENT_TREE_NAME = 'CORPCODE.xml'
URL_CORP_CODE = f'https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_API_KEY}'
URL_FINANCIAL_STATE = 'https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json'
FINANCIAL_CODE = '11011'
YEAR = 2023

CORP_CODE = 'corp_code'
CORP_NAME = 'corp_name'
FILE_SUFFIX_FINANCIAL_STATE = '재무제표'
FILE_EXTENSION_CSV = '.csv'

class DocumentSaver:
    def get_corp_code_list(self):
        try:
            url = URL_CORP_CODE
            response = requests.get(url)
            response.raise_for_status()
            with open(CORP_CODE_FILE_NAME, 'wb') as f:
                f.write(response.content)

            with zipfile.ZipFile(CORP_CODE_FILE_NAME, 'r') as zip_ref:
                zip_ref.extractall('.')

            tree = ET.parse(ELEMENT_TREE_NAME)
            root = tree.getroot()

            corp_list = []
            for child in root.findall('list'):
                corp_list.append({
                    CORP_CODE: child.find(CORP_CODE).text,
                    CORP_NAME: child.find(CORP_NAME).text,
                })

            os.remove(CORP_CODE_FILE_NAME)
            os.remove(ELEMENT_TREE_NAME)

            return corp_list
        
        except Exception as e:
            print(f"[ERROR] 기업코드 리스트 가져오기 실패: {e}")
            return []
        
    def filter_corp_codes_by_name(self, target_names: List[str] = None) -> List[Dict[str, str]]:
        if target_names is None : 
            target_names = [
                "삼성전자",
                "LG화학",
                "현대자동차",
                "카카오"
            ]

        full_list = self.get_corp_code_list()
        filtered_dict = [item for item in full_list if item[CORP_NAME] in target_names]

        return filtered_dict

    def save_financial_reports_document(
            self, 
            filtered_dict: List[dict], 
            save_dir: str = os.path.join(RAG_DOCUMENTS_FOLDER_NAME, FINANCIAL_REPORTS_FOLDER_NAME)
        ) -> List[Document]:
        
        os.makedirs(save_dir, exist_ok=True)
        saved_documents = []
        for corp in filtered_dict:
            corp_code = corp[CORP_CODE]
            corp_name = corp[CORP_NAME]

            url = (
                f"{URL_FINANCIAL_STATE}"
                f"?crtfc_key={DART_API_KEY}"
                f"&corp_code={corp_code}"
                f"&bsns_year={str(YEAR)}"
                f"&reprt_code={FINANCIAL_CODE}"
                f"&fs_div=CFS"
            )
            resp = requests.get(url)
            data = resp.json()

            if data.get('status') == '013':  # 데이터 없음
                print(f"[INFO] {corp_name} - 해당 연도의 사업보고서가 없습니다.")
                continue

            if 'list' not in data:
                print(f"[WARNING] {corp_name} - 재무정보 없음 또는 응답 이상")
                continue

            df = pd.DataFrame(data['list'])
            
            filename = f"{corp_name}_{str(YEAR)}_{FILE_SUFFIX_FINANCIAL_STATE}{FILE_EXTENSION_CSV}"
            file_path = os.path.join(save_dir, filename)
            df.to_csv(file_path, index=False, encoding='utf-8-sig') 

            # Document로 변환 (예: 파일 내용 일부나 요약 가능)
            content = df.to_string()
            saved_documents.append(Document(page_content=content, metadata={"corp_name": corp_name, "year": YEAR, "file_path": file_path}))

        return saved_documents

    # def get_financial_document_chunks(self, path:str, documents: List[Document]) -> List[Document]:
    #     pass


