# src/agent_factory/tools/test_tool.py

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def test_agent_func(code_snippet: str) -> str:
    """
    Stub that calls the LLM to 'simulate' testing. 
    In real usage, you'd run actual tests in Docker or local environment.
    """

    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=openai_api_key,
        model_name=os.getenv("OPENAI_DEFAULT_MODEL","o1-preview")
    )

    system_prompt = SystemMessagePromptTemplate.from_template("""
You are TestAgent. 
Simulate running tests on the given code. 
Output either 'Tests passed' or 'Tests failed: <reason>'. 
This is only a placeholder for real test logic.
""")

    human_prompt = HumanMessagePromptTemplate.from_template("""
{code_snippet}
Give pass/fail result.
""")

    chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
    messages = chat_prompt.format_messages(code_snippet=code_snippet)

    response = llm(messages)
    test_result = response.content.strip()
    return test_result

TestTool = Tool(
    name="test",
    func=test_agent_func,
    description=(
        "Runs a simulated test on code snippet. Returns 'Tests passed' or 'Tests failed: <reason>'."
    )
)
