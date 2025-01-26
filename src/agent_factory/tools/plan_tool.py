# src/agent_factory/tools/plan_tool.py
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
def plan_agent_func(analyzed_requirement: str) -> str:
    """
    This agent tries to produce a list of sub-tasks or a plan for the project.
    It can mention high-level steps: code generation tasks, tests, etc.
    """

    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=openai_api_key,
        model_name=os.getenv("OPENAI_DEFAULT_MODEL","o1-preview")
    )

    system_prompt = SystemMessagePromptTemplate.from_template("""
You are 'PlanAgent'. Your role:
1. Take the user's analyzed requirement.
2. Produce a concise, step-by-step plan or task list to fulfill the requirement.
3. Keep the plan high-level yet actionable (e.g., "Implement X", "Write test for Y").
4. If you notice anything missing or ambiguous, list potential clarifications.
5. Keep your internal reasoning private; only provide the final plan.

Structure your output as:
- A short summary of the project goal
- A bullet list of tasks (in logical order)
- Optionally note any clarifications needed
"""
    )

    human_prompt = HumanMessagePromptTemplate.from_template(
        """
Analyzed Requirement:
"{analyzed_requirement}"

Based on this requirement, outline a clear plan of tasks (e.g., code steps, tests, validations, deployments).
If something is unclear, note possible questions or assumptions.
"""
    )

    chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
    messages = chat_prompt.format_messages(analyzed_requirement=analyzed_requirement)

    response = llm(messages)
    plan = response.content.strip()
    return plan

PlanTool = Tool(
    name="plan",
    func=plan_agent_func,
    description=(
        "Takes the 'analyzed requirement' and returns a step-by-step plan. "
        "Typically the next step is code generation or other tasks in the plan."
    )
)
