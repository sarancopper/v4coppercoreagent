# src/agent_factory/tools/codegen_tool.py

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from sqlalchemy.orm import Session
from src.utils.log_agent_execution import log_agent_execution
from src.utils.log_user_interaction import store_ai_questions
from src.utils.file_operations import ensure_project_directory, create_or_update_file

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def codegen_agent_func(plan_step: str, task_id: int, user_id: int, project_id: int, project_name: str, filename: str, db: Session) -> str:
    """
    Takes a plan step (e.g. 'Create index.html') and generates code using LLM.
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
        You are a Code Generation Agent. You generate, modify or delete code to accomplish the user's plan step. 
        Ensure your response is formatted as clean, functional code.
        """)

        human_prompt = HumanMessagePromptTemplate.from_template("""
        Plan step to code:
        "{plan_step}"

        Generate the code that solves or implements this step. 
        If needed, include minimal comments or docstrings.
        """)

        chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
        messages = chat_prompt.format_messages(plan_step=plan_step)

        response = llm(messages)
        generated_code = response.content.strip()

        # Extract clarification questions if any
        clarification_questions = []
        if "**Clarifying Questions**:" in generated_code:
            questions_part = generated_code.split("**Clarifying Questions**:")[1].split("\n")
            clarification_questions = [q.strip("- ") for q in questions_part if q.strip()]

        # Ensure project directory exists
        project_path = ensure_project_directory(project_name)

        # Create or update file
        file_path = create_or_update_file(project_name, filename, generated_code)

        # Log execution details
        log_agent_execution(
            db=db,
            task_id=task_id,
            user_id=user_id,
            project_id=project_id,
            project_name=project_name,
            agent_name="CodeGenAgent",
            status="completed",
            output=f"Generated code saved to {file_path}."
        )

        # Store clarification questions if any
        if clarification_questions:
            store_ai_questions(
                db=db,
                task_id=task_id,
                user_id=user_id,
                project_id=project_id,
                agent_name="CodeGenAgent",
                questions=clarification_questions
            )

        return f"Code generation completed. File saved at: {file_path}"

    except Exception as e:
        log_agent_execution(
            db=db,
            task_id=task_id,
            user_id=user_id,
            project_id=project_id,
            project_name=project_name,
            agent_name="CodeGenAgent",
            status="failed",
            output=str(e)
        )
        return f"Error: {str(e)}"

CodeGenTool = Tool(
    name="codegen",
    func=codegen_agent_func,
    description=(
        "Generates or modifies code for a given plan step and stores it in the project directory."
    )
)
