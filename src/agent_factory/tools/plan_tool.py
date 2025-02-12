# src/agent_factory/tools/plan_tool.py
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from sqlalchemy.orm import Session
from functools import partial
from src.utils.log_agent_execution import log_agent_execution
from src.utils.log_user_interaction import store_ai_questions

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def plan_agent_func(analyzed_requirement: str, task_id: int, user_id: int, project_id: int, db: Session) -> str:
    """
    Generates a step-by-step execution plan based on the analyzed requirement.
    - Logs execution details in DB.
    - Stores AI-generated clarification questions if needed.
    """
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        llm = ChatOpenAI(
            temperature=0,
            openai_api_key=openai_api_key,
            model_name=os.getenv("OPENAI_DEFAULT_MODEL", "o1-preview")
        )

        system_prompt = SystemMessagePromptTemplate.from_template("""
        You are AI powered specialized Plan Agent. Your role:
        1. Take the user's analyzed requirement.
        2. Produce a concise, step-by-step plan or task list to fulfill the requirement.
        3. Keep the plan high-level yet actionable (e.g., "Implement X", "Write test for Y").
        4. If you notice anything missing or ambiguous, list potential clarifications.
        5. Keep your internal reasoning private; only provide the final plan.

        Structure your output as:
        - A short summary of the project goal
        - A bullet list of tasks (in logical order)
        - Optionally note any clarifications needed
        """)

        human_prompt = HumanMessagePromptTemplate.from_template("""
        Analyzed Requirement:
        "{analyzed_requirement}"

        Based on this requirement, outline a clear plan of tasks (e.g., code steps, tests, validations, deployments).
        If something is unclear, note possible questions or assumptions.
        """)

        chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
        messages = chat_prompt.format_messages(analyzed_requirement=analyzed_requirement)

        response = llm(messages)
        generated_plan = response.content.strip()

        # Extract clarification questions if any
        clarification_questions = []
        if "**Optionally note any clarifications needed**:" in generated_plan:
            questions_part = generated_plan.split("**Optionally note any clarifications needed**:")[1].split("\n")
            clarification_questions = [q.strip("- ") for q in questions_part if q.strip()]

        # Log execution details
        log_agent_execution(
            db=db,
            task_id=task_id,
            user_id=user_id,
            project_id=project_id,
            agent_name="PlanAgent",
            status="completed",
            output=generated_plan
        )

        # Store clarification questions if any
        if clarification_questions:
            store_ai_questions(
                db=db,
                task_id=task_id,
                user_id=user_id,
                project_id=project_id,
                agent_name="PlanAgent",
                questions=clarification_questions
            )

        return generated_plan

    except Exception as e:
        log_agent_execution(
            db=db,
            task_id=task_id,
            user_id=user_id,
            project_id=project_id,
            agent_name="PlanAgent",
            status="failed",
            output=str(e)
        )
        return f"Error: {str(e)}"

PlanTool = Tool(
    name="plan",
    func=partial(plan_agent_func, task_id=None, user_id=None, project_id=None, db=None),
    description=(
        "Takes the 'analyzed requirement' and returns a step-by-step plan. "
        "Typically the next step is code generation or other tasks in the plan."
    )
)
