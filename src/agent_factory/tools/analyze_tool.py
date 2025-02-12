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

def analyze_agent_func(requirement: str, task_id: int, user_id: int, project_id: int, db: Session) -> str:
    """
    AnalyzeAgent:
    - Summarizes the user requirement
    - Identifies missing information
    - Requests clarifications where needed
    - Ensures the AI response includes "Ask the user" if questions exist
    """

    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=openai_api_key,
        model_name=os.getenv("OPENAI_DEFAULT_MODEL", "o1-preview")
    )

    system_prompt = SystemMessagePromptTemplate.from_template(
        """
        You are an AI-powered specialized Analysis Agent responsible for refining user requirements.
        Your responsibilities:
        1. Summarize the provided requirement in concise terms.
        2. Identify ambiguities, missing information, or vague details.
        3. If additional details are needed, explicitly ask the user for clarification.
        4. Do not include chain-of-thought or internal reasoning. Provide only the final summarized insights.

        **Response Format (strictly adhere to these sections):**
        1. Summary:
        - A concise, one- to two-sentence explanation of the requirement.
        2. Potential Ambiguities:
        - A bullet-point list of anything that is unclear, missing, or contradictory.
        - If there are no ambiguities, write "None" or "No ambiguities found."
        3. Clarifying Questions:
        - A bullet-point list of direct questions to ask the user if ambiguities exist.
        - If no questions are needed, write "None."
        4. Refined Requirement:
        - A clean, rewritten version of the requirement based on your analysis and any existing clarifications.

        **IMPORTANT**:
        - If clarifying questions are needed, you **MUST** output them in the exact format below:
        ```
        Ask the user:
        <question1>
        <question2>
        ```
        (Add more lines if there are more questions.)
        - If no clarifications are required, do **NOT** output "Ask the user" at all.
        - Do **NOT** include any additional explanations or reasoning beyond the specified sections.
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

        # Regex pattern to capture each labeled section
        pattern = (
            r"1\. Summary:\s*(?P<summary>.*?)"
            r"2\. Potential Ambiguities:\s*(?P<ambiguities>.*?)"
            r"3\. Clarifying Questions:\s*(?P<questions>.*?)"
            r"4\. Refined Requirement:\s*(?P<refined>.*)"
        )

        match = re.search(pattern, refined_analysis, re.DOTALL)
        if not match:
            # Fallback if the agent didn't adhere to format; just store the raw response
            summary = ambiguities = questions_block = refined_req = ""
        else:
            summary = match.group("summary").strip()
            ambiguities = match.group("ambiguities").strip()
            questions_block = match.group("questions").strip()
            refined_req = match.group("refined").strip()

        # Parse any "Ask the user:" block
        clarification_questions = []
        ask_user_pattern = r"(?s)Ask the user:\s*\n(.*)"
        ask_user_match = re.search(ask_user_pattern, refined_analysis)
        if ask_user_match:
            questions_text = ask_user_match.group(1).strip()
            # Split lines
            lines = [ln.strip() for ln in questions_text.split("\n") if ln.strip()]
            # Remove any leading bullet symbols (e.g., "- ")
            clarification_questions = [q.lstrip("-").strip() for q in lines]

        # Log the entire analysis
        log_agent_execution(
            db=db,
            task_id=task_id,
            user_id=user_id,
            project_id=project_id,
            agent_name="AnalyzeAgent",
            status="success",
            output=refined_analysis
        )

        # If we found clarifying questions, store them
        if clarification_questions:
            store_ai_questions(
                db=db,
                task_id=task_id,
                user_id=user_id,
                project_id=project_id,
                agent_name="AnalyzeAgent",
                questions=clarification_questions
            )

        # Construct final output
        # Optionally, you can reassemble the 4 sections in a standardized format:
        final_output = (
            f"1. Summary:\n{summary}\n\n"
            f"2. Potential Ambiguities:\n{ambiguities}\n\n"
            f"3. Clarifying Questions:\n{questions_block}\n\n"
            f"4. Refined Requirement:\n{refined_req}"
        )

        # If clarifications exist, add them again at the bottom
        if clarification_questions:
            q_str = "\n".join([f"- {q}" for q in clarification_questions])
            final_output += f"\n\n**Ask the user:**\n{q_str}"

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

AnalyzeTool = Tool(
    name="analyze",
    func=partial(analyze_agent_func),
    description=(
        "Analyzes user requirements, identifies missing details, and returns a refined statement or clarifying questions."
    )
)
