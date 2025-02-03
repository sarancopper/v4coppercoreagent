# src/agent_factory/tools/deploy_tool.py

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def deploy_agent_func(code_snippet: str) -> str:
    """
    Stub that calls an LLM to 'simulate' deployment.
    Real usage might push to GitHub or a server.
    """

    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=openai_api_key,
        model_name=os.getenv("OPENAI_DEFAULT_MODEL","o1-preview")
    )

    system_prompt = SystemMessagePromptTemplate.from_template("""
You are DeployAgent. 
Simulate deploying the code snippet. 
Output a final message like 'Deployment successful: ...' or 'Deployment failed: ...'
""")

    human_prompt = HumanMessagePromptTemplate.from_template("""
Deploy this code snippet:
{code_snippet}
""")

    chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
    messages = chat_prompt.format_messages(code_snippet=code_snippet)

    response = llm(messages)
    deploy_result = response.content.strip()
    return deploy_result

DeployTool = Tool(
    name="deploy",
    func=deploy_agent_func,
    description=(
        "Deploys the final code snippet. Returns 'Deployment successful: ...' or 'Deployment failed: ...'."
    )
)
