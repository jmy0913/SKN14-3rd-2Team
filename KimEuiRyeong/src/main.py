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
SAVE_FINANCIAL_REPORTS_ARGS = 'save_financial_reports'

UPLOAD_DOC_PATH_CMD = "--path"
UPLOAD_DOC_PATH_HELP_MESSAGE = "Path if uploading doc."

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        ACTION_ARG_CMD, 
        type=str, 
        required=True,
        choices=[
            UPLOAD_DOCS_ARG, QUERY_RAG_ARG, 
            QUERY_ARG, 
            DELETE_ALL_VECTORS_ARG, 
            SAVE_FINANCIAL_REPORTS_ARGS
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
        response: List[str] = orchestrator.upload_docs_to_rag(args.path)
        print(response)
    elif args.action == QUERY_RAG_ARG:
        query: str = input("Enter your query: ")
        response: str = orchestrator.query_rag(query)
        print(response)
    elif args.action == QUERY_ARG:
        query: str = input("Enter your query: ")
        response: str = orchestrator.query_llm(query)
        print(response)
    elif args.action == DELETE_ALL_VECTORS_ARG:
        orchestrator.delete_all_vectors()
    elif args.action == SAVE_FINANCIAL_REPORTS_ARGS:
        response: List[str] = orchestrator.save_financial_reports()
        print(response)

if __name__ == "__main__": 
    main()
