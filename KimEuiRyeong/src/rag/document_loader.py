from tqdm import tqdm
from typing import List
from pathlib import Path

import pandas as pd
from langchain_core.documents import Document
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import CHUNK_SIZE, CHUNK_OVERLAP

CSV_EXTENSION = ".csv"
PDF_EXTENSION = ".pdf"

class DocumentLoader:
    def get_document_chunks(self, path: str) -> List[Document]:
        file = Path(path)
        file_ext: str = file.suffix
        if file_ext == CSV_EXTENSION:
            return self.get_csv_chunks(path)
        elif file_ext == PDF_EXTENSION:
            return self.get_pdf_chunks(path)
        raise Exception("Unable to chunk document.")

    def get_csv_chunks(self, path: str) -> List[Document]:
        loaded_csv = pd.read_csv(path)
        chunks: List[Document] = []
        for idx, row in tqdm(loaded_csv.iterrows()):
            chunks.append(Document(
                page_content=str(row)
            ))
        return chunks
    
    def get_pdf_chunks(self, path: str) -> List[Document]:
        text: str = ""
        with fitz.open(path) as pdf:
            for page in pdf:
                text += page.get_text()
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ".", "!", "?"],
            chunk_size=CHUNK_SIZE, 
            chunk_overlap=CHUNK_OVERLAP
        )
        texts: List[str] = text_splitter.split_text(text)
        print(texts)
        chunks: List[Document] = []
        for text in texts:
            chunks.append(Document(page_content=text))
        return chunks
        