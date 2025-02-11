import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from sqlalchemy.orm import Session
from src.db.models import get_db
from src.utils.log_agent_execution import log_agent_execution
from src.utils.log_user_interaction import store_ai_questions

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def analyze_agent_func(requirement: str, task_id: int, user_id: int, project_id: int, db: Session) -> str:
    """
    Updated AnalyzeAgent function:
    - Logs execution details in DB
    - Stores AI-generated clarification questions if any
    """

    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=openai_api_key,
        model_name=os.getenv("OPENAI_DEFAULT_MODEL", "o1-preview")
    )

    system_prompt = SystemMessagePromptTemplate.from_template(
        """
        You are a specialized 'AnalyzeAgent'. Your responsibilities:
        1) Summarize the key points of the user's requirement.
        2) Identify ambiguous or missing details.
        3) Restate or refine the requirement in your own words.
        4) If a repository link is provided, note any relevant files.
        5) If information is unclear, propose specific clarifying questions.

        Your output format:
        - **Summary**: (brief explanation)
        - **Potential Ambiguities**: (list of unclear aspects)
        - **Clarifying Questions**: (list of questions if applicable)
        - **Refined Requirement**: (final cleaned-up version)
        """
    )

    human_prompt = HumanMessagePromptTemplate.from_template(
        """
        User's requirement:
        "{requirement}"

        Analyze and return results.
        """
    )

    chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
    messages = chat_prompt.format_messages(requirement=requirement)

    try:
        response = llm(messages)
        refined_analysis = response.content.strip()

        # Extract clarification questions (if any)
        clarification_questions = []
        if "**Clarifying Questions**:" in refined_analysis:
            print(f">>>---> Questions existis in refined_analysis analyze agent")
            questions_part = refined_analysis.split("**Clarifying Questions**:")[1].split("\n")
            clarification_questions = [q.strip("- ") for q in questions_part if q.strip()]

        # Log execution details
        log_agent_execution(
            db=db,
            task_id=task_id,
            user_id=user_id,
            project_id=project_id,
            agent_name="AnalyzeAgent",
            status="success",
            output=refined_analysis
        )

        # Store clarification questions if any
        if clarification_questions:
            store_ai_questions(
                db=db,
                task_id=task_id,
                user_id=user_id,
                project_id=project_id,
                agent_name="AnalyzeAgent",
                questions=clarification_questions
            )

        return refined_analysis

    except Exception as e:
        log_agent_execution(
            db=db,
            task_id=task_id,
            user_id=user_id,
            project_id=project_id,
            agent_name="AnalyzeAgent",
            status="failed",
            output=str(e)
        )
        return f"Error: {str(e)}"

AnalyzeTool = Tool(
    name="analyze",
    func=analyze_agent_func,
    description=(
        "Analyzes user requirements, identifies missing details, and returns a refined statement or clarifying questions."
    )
)
