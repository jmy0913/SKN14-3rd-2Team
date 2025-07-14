# Split the import into groups like below.
# Typing is for adding types to variable. example: line 7 (tools: List[Callable])

# Default python packages.
from typing import List, Callable, Union, Dict, Any

# The packages that you need to install.
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, BaseMessage

# The files that you made.
from src.config import OPENAI_KEY, MODEL_NAME

class LLM:
    def __init__(self, tools: List[Callable] = None):
        try:
            self.llm = ChatOpenAI( # set up the llm as using the langchain
                model=MODEL_NAME,
                api_key=OPENAI_KEY
            )
        except Exception as e:
            print(f"An error occurred while creating LLM: {e}")
            raise e
        if tools: # If there are tools, then I connect with the llm tools
            self.tools: List[Callable] = tools
            try:
                self.llm_with_tools = self.llm.bind_tools(self.tools) # bind_tools() : method of chatopenai, to connect the llm with tools.
            except Exception as e:
                print(f"An error occurred while binding tools to LLM: {e}")
                raise e

    def invoke(
        self, 
        prompt: List[Union[HumanMessage, SystemMessage, AIMessage, ToolMessage]]
    ) -> str:
        response: BaseMessage = self.llm.invoke(prompt)
        return response.content
    
    def invoke_with_tools(
        self, 
        prompt: List[Union[HumanMessage, SystemMessage, AIMessage, ToolMessage]]
    ) -> str:
        # If the LLM responds with a tool call, it will provide you with the input arguments in a structured output
        response: AIMessage = self.llm_with_tools.invoke(prompt)
        #If the response has 'tool_calls' attribute
        if response.tool_calls:
            # Add response to messages in the prompt as the LLM will need it later
            prompt.append(response)
            # Go through all calls in 'tool_calls', bc there could be multiple tools calls
            for tool_call in response.tool_calls:
                # Get tool response, which is just the result from the function itself
                # Don't need to worry rigt now about this.
                tool_response: ToolMessage = self.handle_tool_call(tool_call)
                # Add this tool response to messages in the prompt, bc LLM will make final response
                prompt.append(tool_response)
            
            # LLM makes final response
            response: AIMessage = self.llm_with_tools.invoke(prompt)
        return response.content
    
    def handle_tool_call(self, tool_call: Dict[str, Any]) -> ToolMessage:
        for tool in self.tools:
            if tool.name == tool_call['name']:
                tool_response: ToolMessage = tool.invoke(tool_call)
                break
        return tool_response