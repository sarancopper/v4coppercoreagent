import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from sqlalchemy.orm import Session
from functools import partial
from src.utils.log_agent_execution import log_agent_execution
from src.utils.log_user_interaction import store_ai_questions

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def analyze_agent_func(input_str: str, user_id: int, task_id: int, project_id: int, db: Session) -> str:
    """
    AnalyzeAgent:
    - Summarizes the user requirement
    - Identifies missing information
    - Requests clarifications where needed
    - Ensures the AI response includes "Ask the user" if questions exist
    """
    try:
        data = json.loads(input_str)
    except json.JSONDecodeError:
        data = {"requirement": input_str}

    requirement = data.get("requirement", "No requirement provided")

    analysis_result = f"Analysis for requirement: {requirement}"

    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=openai_api_key,
        model_name=os.getenv("OPENAI_DEFAULT_MODEL", "o1-preview")
    )

    system_prompt = SystemMessagePromptTemplate.from_template(
        """
        You are an AI-powered specialized Analysis Agent responsible for refining user requirements.
        Your responsibilities and follow these steps:
        1. Summarize the provided requirement in concise terms.
        2. Identify ambiguities, missing information, or vague details.
        3. If additional details are needed, explicitly ask the user for clarification.
        4. Do not include chain-of-thought or internal reasoning. Provide only the final summarized insights.
    
        OUTPUT FORMAT (in valid JSON and dont include comments inside the json code block)
        {
        "summary": "...",
        "ambiguities": ["..."],
        "questions": ["..."],
        "refined_requirement": "..."
        }

        - "summary": A short, 1-2 sentence summary.
        - "ambiguities": A list of unclear or missing details. If none, use an empty list [].
        - "questions": A list of clarifying questions. If none, use an empty list [].
        - "refined_requirement": A concise, final re-statement of the requirement.
        """
    )

    human_prompt = HumanMessagePromptTemplate.from_template(
        """
        User's requirement:
        "{requirement}"

        Please analyze and return structured JSON.
        """
    )

    chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
    messages = chat_prompt.format_messages(requirement=requirement)
    try:
        response = llm(messages)
        refined_analysis = response.content.strip()
        print(f"Analyze agent response : {refined_analysis}")
        # Attempt to parse JSON
        # If the LLM returned something else, fallback or raise an error.
        try:
            data = json.loads(refined_analysis)
            print(f"Analyze agent response data : {data}")
        except json.JSONDecodeError as e:
            # If the AI didn't comply with JSON, treat entire refined_analysis as fallback
            data = {
                "summary": f"Parsing Error. Raw response: {e}",
                "ambiguities": [],
                "questions": [],
                "refined_requirement": refined_analysis
            }
            safe_summary = data.get("summary", "(No summary provided)")

        # Extract clarifying questions, if any
        clarification_questions = data.get("questions", [])
        final_output = json.dumps(data, indent=2)

        # Log the result
        log_agent_execution(
            db=db,
            task_id=task_id,
            user_id=user_id,
            project_id=project_id,
            agent_name="AnalyzeAgent",
            status="success",
            output=final_output
        )

        # Store questions, if any
        if clarification_questions:
            store_ai_questions(
                db=db,
                task_id=task_id,
                user_id=user_id,
                project_id=project_id,
                agent_name="AnalyzeAgent",
                questions=clarification_questions
            )

        return final_output

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

def make_analyze_tool(
    db: Session,
    user_id: int,
    task_id: int,
    project_id: int
) -> Tool:
    """
    Factory function that returns a LangChain Tool for 'analyze'.
    We create a partial that bakes in db, user_id, project_id.
    """
    from functools import partial

    analyze_func = partial(
        analyze_agent_func,
        user_id=user_id,
        task_id=task_id,
        project_id=project_id,
        db=db
    )
    
    return Tool(
        name="analyze",
        func=analyze_func,
        description="Analyze the user's requirement. Expects a single string of input."
    )
