# src/agent_factory/tools/codegen_tool.py

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
def codegen_agent_func(plan_step: str) -> str:
    """
    Takes a plan step (e.g. 'Create index.html') and returns actual code from the LLM.
    In production, you might add more context or existing code references.
    """

    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=openai_api_key,
        model_name=os.getenv("OPENAI_DEFAULT_MODEL","o1-preview")
    )

    system_prompt = SystemMessagePromptTemplate.from_template("""
You are CodeGenAgent. 
You generate or modify code to accomplish the user's plan step.
Output code in a single, clear block if possible.
""")

    human_prompt = HumanMessagePromptTemplate.from_template("""
Plan step to code:
"{plan_step}"

Generate the code that solves or implements this step. 
If needed, show docstrings or minimal comments.
""")

    chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
    messages = chat_prompt.format_messages(plan_step=plan_step)

    response = llm(messages)
    generated_code = response.content.strip()
    return generated_code

CodeGenTool = Tool(
    name="codegen",
    func=codegen_agent_func,
    description=(
        "Given a single plan step, produce or modify relevant code. "
        "For example: 'create index.html', 'build a python function', etc."
    )
)
