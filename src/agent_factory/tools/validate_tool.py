# src/agent_factory/tools/validate_tool.py

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
def validate_agent_func(code_snippet: str) -> str:
    """
    A stub that calls an LLM to do a 'theoretical validation'.
    In Phase 2, you might run a real sandbox or lint check.
    """

    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=openai_api_key,
        model_name=os.getenv("OPENAI_DEFAULT_MODEL","o1-preview")
    )

    system_prompt = SystemMessagePromptTemplate.from_template("""
You are ValidateAgent. 
You check code for errors or basic issues.
Output either 'Validation passed' or 'Validation failed: <reason>'.
This is a theoretical check for now.
""")

    human_prompt = HumanMessagePromptTemplate.from_template("""{code_snippet}""")

    chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
    messages = chat_prompt.format_messages(code_snippet=code_snippet)

    response = llm(messages)
    validation_result = response.content.strip()
    return validation_result

ValidateTool = Tool(
    name="validate",
    func=validate_agent_func,
    description=(
        "Checks code snippet for errors or issues. Returns a string like "
        "'Validation passed' or 'Validation failed: <reason>'."
    )
)
