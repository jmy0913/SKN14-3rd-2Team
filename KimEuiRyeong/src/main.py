import argparse
import sys
from typing import List

from src.orchestrator import Orchestrator

ACTION_ARG_CMD = "--action"
ACTION_HELP_MESSAGE = "Actions that can be used."
UPLOAD_DOCS_ARG = "upload_docs"
QUERY_RAG_ARG = "query_rag"
QUERY_ARG = "query"
DELETE_ALL_VECTORS_ARG = "delete_all_vectors"

UPLOAD_DOC_PATH_CMD = "--path"
UPLOAD_DOC_PATH_HELP_MESSAGE = "Path if uploading doc."

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        ACTION_ARG_CMD, 
        type=str, 
        required=True,
        choices=[
            UPLOAD_DOCS_ARG, 
            QUERY_RAG_ARG, 
            QUERY_ARG, 
            DELETE_ALL_VECTORS_ARG
        ],
        help=ACTION_HELP_MESSAGE
    )
    argparser.add_argument(
        UPLOAD_DOC_PATH_CMD, 
        type=str,
        help=UPLOAD_DOC_PATH_HELP_MESSAGE
    )
    args = argparser.parse_args()
    
    if args.action == UPLOAD_DOCS_ARG and not args.path:
        print("An error occurred as upload doc path not specified")
        sys.exit(1)

    orchestrator = Orchestrator()
    if args.action == UPLOAD_DOCS_ARG:
        uploaded_ids: List[str] = orchestrator.upload_docs_to_rag(args.path)
        print(uploaded_ids)
    elif args.action == QUERY_RAG_ARG:
        rag_query: str = input("Enter your query: ")
        rag_response: str = orchestrator.query_rag(rag_query)
        print(rag_response)
    elif args.action == QUERY_ARG:
        llm_query: str = input("Enter your query: ")
        llm_response: str = orchestrator.query_llm(llm_query)
        print(llm_response)
    elif args.action == DELETE_ALL_VECTORS_ARG:
        orchestrator.delete_all_vectors()

if __name__ == "__main__":
    main()
