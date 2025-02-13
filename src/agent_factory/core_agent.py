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
from src.agent_factory.tools.analyze_tool import make_analyze_tool
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
from .multi_agent_prompt_generator import MultiAgentPromptGenerator, SWEPromptConfig, AgentRole, AgentState

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class CoreAgent:
    def __init__(
        self,
        db, # The DB session
        user_id: int,
        task_id: int,
        project_id: int,
        project_name: str,
        requirement: str):
        """
        We now pass db, user_id, project_id, etc. into CoreAgent's constructor
        so we can create Tools with partials that embed them.
        """
        self.db = db
        self.user_id = user_id
        self.task_id = task_id
        self.project_id = project_id
        self.project_name = project_name
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
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
            make_analyze_tool(db, user_id, task_id, project_id),
            PlanTool,
            CodeGenTool,
            ValidateTool,
            TestTool,
            DeployTool,
            UserInteractionTool
        ]
        # A default prompt that helps the agent decide which tool to call:
        self.prompt = PromptTemplate.from_template("""
        You are AI Core Agent, an advanced, self-evolving software AGI with reinforcement-learning capabilities. 
        You orchestrate multiple sub-agents (or tools) for each phase of development including: 
        ---
        **Sub-Agents and Their Roles**:
        1. **analyze**  Examine the requirement, identify needs, and outline preliminary ideas or possible strategies.
        2. **plan**  Develop a structured plan or sequence of steps to implement the solution.
        3. **codegen**  Generate production-ready code according to the plan.
        4. **validate**  Check the generated code for errors, correctness, or alignment with the requirement.
        5. **test**  Run tests (unit, integration, etc.) on the solution and provide test results.
        6. **docgen**  Generate documentation, usage instructions, or other helpful materials.
        7. **deploy**  Provide instructions or scripts to deploy the solution, if applicable.
        8. **user_interaction**  Interact with the user (e.g., to ask clarifications, confirm details, or provide updates).
        ---
        The user has provided the following requirement or task:
        {requirement}
        ---
        Your objectives:
        1. **Decompose the Requirement**  
            - Understand the user’s request in depth.  
            - Identify any missing or ambiguous details.
        
        2. **Orchestrate Sub-Agents**  
            - Determine which sub-agents to call and in what order (generally: analyze → plan → codegen → validate → test → docgen → deploy).
            - You may repeat certain sub-agent calls if needed (e.g., if validation fails).
            - If you detect insufficient information or ambiguity, call **user_interaction** to ask clarifying questions.

        3. **Maintain Privacy of Internal Reasoning**  
            - Keep your full chain-of-thought private.  
            - Summarize any reasoning in a concise, user-friendly way.

        4. **Produce the Final Answer**  
            - Once all sub-agent outputs have been integrated and validated, present a final user-friendly solution.
            - This may include code snippets in fenced blocks, usage instructions, or deployment notes.

        5. **Quality and Robustness**  
            - Strive for code that is clean, efficient, and well-organized.
            - Use best practices, design patterns, proper error handling, and security considerations where relevant.
            - Provide references or disclaimers if external libraries or data are used.
        ---
        You can call the following tools:
        {tools}
        ---

        **Interaction Format**:
        - **Always** output your chosen action in the following strict format:
            Action: <tool_name> \nAction Input: <tool_input>
            ```
            Examples:
            - To call the `analyze` sub-agent:
            ```
            Action: analyze
            Action Input: "Begin analyzing the requirement in detail, identify any potential pitfalls..."
            ```
            - To ask clarifying questions to the user:
            ```
            Action: user_interaction
            Action Input: "Could you clarify the preferred programming language?"
            ```

            - **Do not** provide any extra text outside this format whenever you decide which tool to invoke.
            - **Never** reveal your entire chain-of-thought. Summaries are okay but must be concise.
            ---

            **Edge Cases & Additional Guidelines**:
            - If the user’s request appears to violate any policies or ethical guidelines, politely ask for clarification or refuse if it remains non-compliant.
            - If the user wants to skip certain sub-agents or steps, confirm with them that it is intentional.
            - If an error or ambiguity is detected at any stage, revert to **user_interaction** to resolve it.
            ---
            **Now, begin by deciding which tool to call first:**

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
            verbose=True,  # or False in production
            handle_parsing_errors=True,
            callback_manager=[self.tool_tracker]  # Attach callback tracker
        )
        return agent_executor
    
    def _safe_run(self, requirement: str, max_retries=3) -> str:
        """
        Safely invoke the agent chain with basic retry logic.
        """
        for attempt in range(max_retries):
            try:
                print(f"\n[CoreAgent] Attempt {attempt+1}/{max_retries}")
                return self.agent_chain.run(input=requirement, prompt=self.prompt.format(
                    requirement=requirement,
                    tools="\n".join([t.name for t in self.tools])
                ))
            except Exception as e:
                print(f"Attempt {attempt+1} failed with error: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2)

    def run(self, requirement: str) -> str:
        """
        Orchestrate the conversation with the user requirement, calling sub-agents as needed.
        """
        print(f"\nRunning Core Agent for Project {self.project_name}")
        print(f" User's requirement:\n{requirement}\n")
        executed_agents = set()  # Track which agents have already run
        db = self.db
        user_id = self.user_id
        task_id = self.task_id
        project_id = self.project_id
        project_name = self.project_name
        while True:
            try:
                ai_response = self._safe_run(requirement)
                print(f"Agent Output:\n{ai_response}\n")

                agent_name = self.tool_tracker.get_last_tool_name()
                print(f"Last tool invoked: {agent_name}")

                store_agent_confirmation(db, user_id, task_id, project_id, agent_name, ai_response)

                pending_confirmations = get_pending_user_confirmation(db, user_id, task_id, project_id, agent_name)
                while pending_confirmations:
                    print("\n Waiting for user confirmation...\n")
                    time.sleep(30)
                    pending_confirmations = get_pending_user_confirmation(db, user_id, task_id, project_id, agent_name)

                if "Final Answer:" in ai_response:
                    print(" Final answer received. Task completed.")
                    log_agent_execution(
                        db=db,
                        user_id=user_id,
                        project_id=project_id,
                        project_name=project_name,
                        task_id=task_id,
                        agent_name="CoreAgent",
                        status="completed",
                        output=ai_response
                    )
                    db.commit()
                    return ai_response

                # Handle "Ask the user" scenario
                # If the sub-agent's ai_response instructs to ask the user questions:
                if "Ask the user:" in ai_response:
                    questions = self._extract_clarifying_questions(ai_response)
                    if questions:
                        store_ai_questions(db, task_id, user_id, project_id, agent_name, questions)
                        # Return or break to wait for user input, depending on your flow
                        return "Awaiting user answers to clarifying questions."

            except Exception as e:
                log_agent_execution(
                    db=db,
                    user_id=user_id,
                    project_id=project_id,
                    project_name=project_name,
                    task_id=task_id,
                    agent_name="CoreAgent",
                    status="failed",
                    output=str(e)
                )
                print(f" Error during execution: {e}")
                return f" Execution stopped due to error: {e}"

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
            print(f" Error extracting clarifying questions: {e}")
            return None
