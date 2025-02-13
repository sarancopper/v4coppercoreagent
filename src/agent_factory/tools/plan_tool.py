# src/agent_factory/tools/plan_tool.py
import os
import json
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
    PlanAgent:
    - Takes the user's analyzed requirement (in JSON) from the AnalyzeAgent
    - Produces a concise, step-by-step plan or task list
    - If something is unclear, returns clarifying questions in JSON
    """

    try:
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        llm = ChatOpenAI(
            temperature=0,
            openai_api_key=openai_api_key,
            model_name=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4")
        )

        system_prompt = SystemMessagePromptTemplate.from_template("""
        You are an AI-powered specialized Plan Agent.
        Your role:
        1. Take the user's analyzed requirement (JSON).
        2. Produce a clear, step-by-step plan to implement the solution.
        3. If any parts are unclear, list clarifying questions in the JSON "questions" field.
        4. Keep your reasoning private.

        OUTPUT FORMAT (valid JSON):
        {
          "goal": "...",
          "tasks": [
            "task 1",
            "task 2"
          ],
          "questions": []
        }
        - "goal": short summary of what we're trying to achieve overall
        - "tasks": bullet list of tasks in logical order
        - "questions": any clarifications needed. if none, use an empty list []
        """)

        human_prompt = HumanMessagePromptTemplate.from_template("""
        The analyzed requirement (JSON) is:
        {analyzed_requirement}

        Please return a JSON plan with "goal", "tasks", and "questions".
        """)

        chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
        messages = chat_prompt.format_messages(analyzed_requirement=analyzed_requirement)

        response = llm(messages)
        content = response.content.strip()

        # Parse the JSON or fallback
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = {
                "goal": "Unable to parse. Raw response:",
                "tasks": [],
                "questions": [],
                "raw": content
            }

        # Log execution details
        log_agent_execution(
            db=db,
            task_id=task_id,
            user_id=user_id,
            project_id=project_id,
            agent_name="PlanAgent",
            status="completed",
            output=content
        )

        # Store any clarifying questions
        if data.get("questions"):
            store_ai_questions(
                db=db,
                task_id=task_id,
                user_id=user_id,
                project_id=project_id,
                agent_name="PlanAgent",
                questions=data["questions"]
            )

        # Return final plan as JSON string (or dict)
        return json.dumps(data, indent=2)

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
    description="Takes the 'analyzed requirement' (JSON) and returns a JSON plan with a goal, tasks, and clarifying questions if needed."
)
