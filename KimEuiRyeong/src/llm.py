from typing import List, Callable, Union, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, BaseMessage

# The files that you made.
from src.config import OPENAI_KEY, MODEL_NAME

class LLM:
    def __init__(self, tools: List[Callable] = None):
        try:
            self.llm = ChatOpenAI(
                model=MODEL_NAME,
                api_key=OPENAI_KEY
            )
        except Exception as e:
            print(f"An error occurred while creating LLM: {e}")
            raise e
        if tools:
            self.tools: List[Callable] = tools
            try:
                self.llm_with_tools = self.llm.bind_tools(self.tools) 
            except Exception as e:
                print(f"An error occurred while binding tools to LLM: {e}")
                raise e

    def invoke(
        self, 
        prompt: List[Union[HumanMessage, SystemMessage, AIMessage, ToolMessage]]
    ) -> str:
        response: BaseMessage = self.llm.invoke(prompt)
        return response.content