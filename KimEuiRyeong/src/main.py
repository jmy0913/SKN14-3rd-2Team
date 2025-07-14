import argparse
import sys
from typing import List

from src.orchestrator import Orchestrator

ACTION_ARG_CMD = "--action"
ACTION_HELP_MESSAGE = "Actions that can be used."
UPLOAD_DOCS_ARG = "upload_docs"
QUERY_RAG_ARG = "query_rag"
QUERY_TOOLS_ARG = "query_tools"
QUERY_ARG = "query"
DELETE_ALL_VECTORS_ARG = "delete_all_vectors"
# ADD by EUIRYEONG
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
            QUERY_TOOLS_ARG, QUERY_ARG, 
            DELETE_ALL_VECTORS_ARG, 
            # ADD by EUIRYEONG
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
    
    # If the user inputs --action as upload_docs but doesn't specify --path, then system exits
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
    elif args.action == QUERY_TOOLS_ARG:
        query: str = input("Enter your query: ")
        response: str = orchestrator.query_llm_with_tools(query)
        print(response)
    elif args.action == QUERY_ARG:
        query: str = input("Enter your query: ")
        response: str = orchestrator.query_llm(query)
        print(response)
    elif args.action == DELETE_ALL_VECTORS_ARG:
        orchestrator.delete_all_vectors()

    # ADD by EUIRYEONG
    elif args.action == SAVE_FINANCIAL_REPORTS_ARGS:
        response: List[str] = orchestrator.save_financial_reports()
        print(response)

# This block runs only when the Python file is executed directly.
# It's useful for testing, running, or reusing the code more conveniently.
# When this file is imported as a module (e.g., `import main`), this block won't be executed automatically.
if __name__ == "__main__": # always staring like this is really good habit
    main()

# f there is a white circle on the file name, it means that you gotta save the file!!!! 
# and also on the left, if there is blue line, it means that you added something on the line.
# if it's a green color, it means you wrote down new line.