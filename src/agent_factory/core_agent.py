# src/agent_factory/core_agent.py
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, Tool
from langchain.schema.runnable import RunnableMap
from tenacity import retry, stop_after_attempt, wait_fixed

from .custom_parser import CustomOutputParser
from src.agent_factory.tools.analyze_tool import AnalyzeTool
from src.agent_factory.tools.plan_tool import PlanTool
from src.agent_factory.tools.codegen_tool import CodeGenTool
from src.agent_factory.tools.validate_tool import ValidateTool
from src.agent_factory.tools.test_tool import TestTool
from src.agent_factory.tools.deploy_tool import DeployTool
from src.agent_factory.tools.user_interaction_tool import UserInteractionTool
from src.utils.log_agent_execution import log_agent_execution
from src.utils.agent_tools import ToolExecutionTracker
from src.utils.log_user_interaction import (
    get_unanswered_questions,
    store_ai_questions,
    store_user_answers,
    store_agent_confirmation,
    get_pending_user_confirmation,
    update_user_confirmation_status
)
# from src.mapg.multi_agent_prompt_gen import MultiAgentPromptGenerator, SWEPromptConfig, AgentRole, AgentState

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class CoreAgent:
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(model_name='gpt-4o', temperature=0, api_key=openai_api_key)
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.tool_tracker = ToolExecutionTracker()
        self.state = AgentState(
            current_task="initializing",
            dependencies=[],
            artifacts={},
            constraints=[],
            quality_gates=[]
        )
       #  self.mapg = MultiAgentPromptGenerator(config_path=mapg_config_path)

        self.tools = [
            AnalyzeTool,
            PlanTool,
            CodeGenTool,
            ValidateTool,
            TestTool,
            DeployTool,
            UserInteractionTool
        ]
        # A default prompt that helps the agent decide which tool to call:
        self.prompt = PromptTemplate.from_template("""
        You are CoreAgent, an advanced, self-evolving software AGI with reinforcement-learning capabilities. 
        You orchestrate multiple sub-agents (or tools) for each phase of development: Analyze, Plan, CodeGen, Validate, Test, and Deploy.

        The user has provided the following requirement or task:
        {requirement}

        Your objectives:
        1. Figure out the best steps or subtasks needed to fulfill the requirement. 
        2. Call the appropriate tools in the correct sequence (analyze → plan → codegen → validate → test → deploy -> document) to produce a working solution.
        3. If you lack information or the requirement seems ambiguous, ask the user for clarification before proceeding.
        4. Keep your detailed chain-of-thought private, but provide concise reasoning summaries.
        5. Once all steps are complete, provide a final user-friendly answer (including code, instructions, or explanations as needed).

        You can call the following tools:
        {tools}

        Guidelines:
            - Always output in the following format:
              Action: <tool_name>
              Action Input: <tool_input>
            - When clarifications are needed, explicitly ask the user questions in the Action Input. For example:
                Action: "user_interaction"
                Action Input: "Ask the user the following questions: <question1>, <question2>"

            - Do not output anything other than the above format when deciding which tool to use.

        Now, begin by deciding which tool to call first:
        Action: 
        """)

        print(f"""    CORE AGENT prompt
            {self.prompt}
        """)
    
        self.agent_chain = self._build_agent_chain()
        
    def _build_agent_chain(self):
        # Initialize the agent with tools and the LLM
        agent_executor = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent="zero-shot-react-description",  # Use the standard zero-shot agent
            verbose=True,
            handle_parsing_errors=True,
            callback_manager=[self.tool_tracker]  # Attach callback tracker
        )
        return agent_executor

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def safe_run(self, agent_chain, input_data):
        """
        Safely run the agent chain with retries in case of errors.
        """
        return agent_chain.run(input=input_data)
    
    def run(self, db, user_id: int, project_id: int, project_name: str, requirement: str) -> str:
        """
        Executes the agent chain dynamically, ensuring database logs, user confirmations,
        and user interactions are handled correctly.
        """
        print(f"User's requirement:\n{requirement}\n")

        while True:
            try:
                # Run the agent safely with retries
                result = self.safe_run(self.agent_chain, requirement)
                print(f"Core agent result:\n{result}\n")

                # Log AI response and wait for confirmation before proceeding
                store_agent_confirmation(db, user_id, project_id, agent_name, result)

                # Wait for user confirmation
                pending_confirmations = get_pending_user_confirmation(db, user_id, project_id, agent_name)
                while pending_confirmations:
                    print("\nWaiting for user confirmation before proceeding...\n")
                    time.sleep(15)  # Polling every 5 seconds
                    pending_confirmations = get_pending_user_confirmation(db, user_id, project_id, agent_name)

                # Stop execution if AI has reached a final answer
                if "Final Answer:" in result:
                    print("Final answer received. Task completed.")
                    log_agent_execution(
                        db=db,
                        user_id=user_id,
                        project_id=project_id,
                        project_name=project_name,
                        agent_name="CoreAgent",
                        status="completed",
                        output=result
                    )
                    db.commit()  # Commit final result
                    return result

                # Store AI-generated batch of questions
                if "Ask the user" in result:
                    clarifying_questions = self.extract_clarifying_questions(result)
                    if clarifying_questions:
                        store_ai_questions(db, user_id, project_id, "CoreAgent", clarifying_questions)
                        return "Waiting for user input"

                # Wait for user answers
                unanswered_questions = get_unanswered_questions(db, user_id, project_id)
                while unanswered_questions:
                    print("\nWaiting for user responses...\n")
                    time.sleep(15)  # Polling every 15 seconds
                    unanswered_questions = get_unanswered_questions(db, user_id, project_id)

            except Exception as e:
                # db.rollback()
                log_agent_execution(
                    db=db,
                    user_id=user_id,
                    project_id=project_id,
                    project_name=project_name,
                    agent_name="CoreAgent",
                    status="failed",
                    output=str(e)
                )
                print(f"Error during execution: {e}")
                return f"Execution stopped due to error: {e}"

    def extract_clarifying_questions(self, result: str) -> str:
        """
        Extract clarifying questions from the agent's result.
        """
        try:
            questions_start = result.find("Ask the user the following questions:")
            if questions_start == -1:
                return None
            clarifying_questions = result[questions_start:].strip()
            return clarifying_questions
        except Exception as e:
            print(f"Error extracting clarifying questions: {e}")
            return None
