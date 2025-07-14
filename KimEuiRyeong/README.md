# llm-project

## Setup

To setup this project, do the following:

1. Clone this repo: `git clone https://github.com/JamesGitHub50/llm-project.git`
2. Enter this repo's root directory: ` cd llm-project`
3. Creat virtual environment: `python -m venv .venv`
4. If using Mac, enter the virtual environment: `source .venv/bin/activate`
5. Install required packages: `pip install -r requirements.txt`
6. Create `.env` in root directory, and add the following environment variables:
```
OPENAI_KEY="..."
MODEL_NAME="gpt-4o-mini"
```

## How to Run Program

1. Enter the root directory
2. Run `python -m src.main`