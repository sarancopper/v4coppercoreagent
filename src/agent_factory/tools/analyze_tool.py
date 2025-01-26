# src/agent_factory/tools/analyze_tool.py

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
from langchain.agents import Tool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def analyze_agent_func(requirement: str) -> str:
    """
    A more advanced "AnalyzeAgent" function that uses an LLM to:
      1) Summarize the user's requirement
      2) Identify if there are ambiguous or missing details
      3) Return a refined statement of the requirement
      4) If something is unclear, highlight it or propose clarifying questions
      5) If a repository link is provided, note relevant files/structure
    """

    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=openai_api_key,
        model_name=os.getenv("OPENAI_DEFAULT_MODEL","o1-preview")
    )

    # ---- Updated System Prompt ----
    system_prompt = SystemMessagePromptTemplate.from_template(
        """
You are a specialized 'AnalyzeAgent'. Your responsibilities:
1) Summarize the key points of the user's requirement.
2) Identify ambiguous or missing details.
3) Restate or refine the requirement in your own words.
4) If a repository link is provided, note any relevant files or details, but do not expose full chain-of-thought.
5) If information is unclear, propose specific clarifying questions.

Your final output should be concise yet structured, covering:
- A brief **Summary** of the request
- A list of **Potential Ambiguities** or missing info
- Any **Clarifying Questions** you have
- A **Refined Requirement** that incorporates what you know so far

Keep your internal reasoning private. Provide only the final analysis in a clear, user-friendly format.
"""
    )

    # ---- Updated Human Prompt ----
    human_prompt = HumanMessagePromptTemplate.from_template(
        """
User's requirement:
"{requirement}"

Analyze the above requirement, following your instructions.
"""
    )

    chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
    messages = chat_prompt.format_messages(requirement=requirement)

    # Call the LLM
    response = llm(messages)
    refined_analysis = response.content.strip()
    return refined_analysis

AnalyzeTool = Tool(
    name="analyze",
    func=analyze_agent_func,
    description=(
        "Analyzes user requirements, identifies missing details, and returns a refined statement or clarifying questions."
    )
)
