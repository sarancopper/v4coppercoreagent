Below is a **technical document** describing the purpose, structure, and workflow of the `CoreAgent` class. You can use this as reference material for anyone looking to understand how the **Core Agent** works in your system.

## 1. Overview

The **CoreAgent** is the central orchestrator in the multi-agent system. Its primary responsibility is to:
1. Receive and process a **user requirement** (e.g., "Build me a website").
2. Dynamically call sub-agents (tools) in the correct order (Analyze → Plan → CodeGen → Validate → Test → Deploy → etc.).
3. Manage user confirmations and clarifications whenever required.
4. Log all relevant execution data (e.g., successes, failures, AI responses, user clarifications) in a database.

By combining multiple specialized agents (tools), the **CoreAgent** ensures that a user’s project or requirement goes through a structured pipeline, from initial analysis to final deployment.

## 2. Key Components

### 2.1. Constructor

```python
def __init__(self, openai_api_key: str):
    self.llm = ChatOpenAI(model_name='gpt-4o', ...)
    self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    self.tool_tracker = ToolExecutionTracker()
    self.tools = [AnalyzeTool, PlanTool, CodeGenTool, ValidateTool, TestTool, DeployTool, UserInteractionTool]
    self.prompt = PromptTemplate.from_template("... (Prompt Content) ...")
    self.agent_chain = self._build_agent_chain()
```

1. **LLM Initialization** (`self.llm`): Uses a chat model (`ChatOpenAI`) to interpret instructions and produce text responses.
2. **Conversation Memory** (`self.memory`): Stores conversation context for referencing previous interactions.
3. **Tool Execution Tracker** (`self.tool_tracker`): A callback that records the last tool invoked, allowing the system to know which sub-agent was called.
4. **Tools List** (`self.tools`): A list of sub-agents or “tools” that the CoreAgent can call to perform specialized tasks:
   - `AnalyzeTool`: Summarizes and clarifies the user requirement.
   - `PlanTool`: Creates a step-by-step plan.
   - `CodeGenTool`: Generates or updates code files.
   - `ValidateTool`: Checks correctness or formatting.
   - `TestTool`: Runs tests or QA checks.
   - `DeployTool`: Handles deployment tasks.
   - `UserInteractionTool`: Asks the user clarifying questions.
5. **PromptTemplate** (`self.prompt`): Defines how the system prompt is constructed, telling the AI how to behave (e.g., keep chain-of-thought private, always respond in a particular format).
6. **Agent Chain** (`self.agent_chain`): A combined chain (the “agent”) that can call the LLM and any of the specified tools.

### 2.2. `_build_agent_chain()`

```python
def _build_agent_chain(self):
    agent_executor = initialize_agent(
        tools=self.tools,
        llm=self.llm,
        agent="zero-shot-react-description",
        verbose=True,
        handle_parsing_errors=True,
        callback_manager=[self.tool_tracker]
    )
    return agent_executor
```

- **initialize_agent(...)**: Creates an agent that uses:
  - The LLM (`self.llm`) as its language engine.
  - The set of Tools (`self.tools`) for specialized tasks.
  - A ReAct-based approach (`"zero-shot-react-description"`) to decide which tool to call at runtime.
  - **callback_manager** referencing `self.tool_tracker`, allowing us to track each tool invocation.

### 2.3. `safe_run(...)`

```python
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def safe_run(self, agent_chain, input_data):
    return agent_chain.run(input=input_data)
```

- Uses **tenacity** library for retry logic.
- If the agent chain fails or throws an exception, it will automatically retry up to 3 times, waiting 2 seconds between attempts.
- Passes the user’s `input_data` into the agent chain’s `.run(...)` method.

### 2.4. `run(...)`

```python
def run(self, db, user_id: int, project_id: int, project_name: str, requirement: str) -> str:
    ...
```

**Purpose**  
The main entry point for the **CoreAgent**. This is called by the Celery task (or any orchestrator) to execute the entire multi-agent pipeline.  

**Key Steps**  
1. **Log User Requirement**: Prints the user’s requirement for debugging.  
2. **Invoke the Agent**: Calls `safe_run(...)` to run the agent chain with the user’s requirement.  
3. **Identify Last Tool**: Uses `self.tool_tracker.get_last_tool_name()` to figure out which sub-agent was just executed.  
4. **Store Agent Confirmation**: Saves the agent’s response in the database, requiring a user to confirm or reject the next step.  
5. **Wait for Confirmation**: Repeatedly checks `get_pending_user_confirmation(...)` until the user has confirmed or the system times out.  
6. **Check for Final Answer**: If the response includes `"Final Answer:"`, logs completion and returns.  
7. **Ask the User for Clarifications**: If the response says `"Ask the user"`, we extract clarifying questions and store them.  
8. **Wait for Bulk Answers**: If there are unanswered questions, we keep polling until user answers them in some external UI.  
9. **Exception Handling**: On any exception, logs the failure in the database, prints the error, and stops the process.

**Example Flow**  
- The user wants to “Create a personal finance web app.”  
- The **CoreAgent** calls `AnalyzeTool` → user clarifications → `PlanTool` → code generation → etc.  
- At each step, the **CoreAgent** logs the sub-agent’s response and waits for the user to confirm or provide answers.  
- Continues until the final response is `"Final Answer: <some solution>"`.

### 2.5. `extract_clarifying_questions(...)`

```python
def extract_clarifying_questions(self, result: str) -> str:
    ...
```

- Searches the AI’s text output for a substring `"Ask the user the following questions:"`.
- If found, returns the substring from that point onward as the clarifying questions text.
- Used by the **CoreAgent** to store these questions in the database and prompt the user for answers.

## 3. Data Logging & User Interaction

1. **log_agent_execution**: Persists logs in a `task_logs` or similar table, storing:
   - user_id, project_id, project_name, agent_name
   - success/failure status
   - textual output from the agent
2. **store_agent_confirmation** / **get_pending_user_confirmation**:  
   - Creates a pending confirmation record in the DB for the user to accept or reject the agent’s next step.
   - The CoreAgent polls for a user’s response before continuing.
3. **store_ai_questions** / **get_unanswered_questions**:  
   - If the AI says “Ask the user,” the CoreAgent extracts the questions and stores them in a `TaskQuestionsAnswers` table.
   - The user’s UI eventually answers them, at which point the system sets the status to answered and allows the pipeline to continue.

## 4. Lifecycle & Execution

A typical run cycle for the **CoreAgent**:

1. **Initialization**:  
   - CoreAgent is constructed with an `openai_api_key`.  
   - Tools and memory are set up.  

2. **User or Celery Task calls `run(...)`**:  
   - The requirement is passed in, along with DB session, user_id, project_id, etc.

3. **Agent Execution**:  
   - The agent reads the requirement and decides which tool to call.  
   - If the tool is e.g. `AnalyzeTool`, it returns an analysis.  
   - The system logs the sub-agent’s response and checks if user confirmation is needed.

4. **User Confirmations**:  
   - The pipeline stops to wait for a “confirmed” or “rejected” status from the user.  
   - If confirmed, the agent proceeds; if rejected, the pipeline ends with a “stopped by user” status.

5. **User Clarifications**:  
   - If the agent requests clarifications, the pipeline stores them, then waits for user answers.

6. **Final Answer**:  
   - Eventually, the agent outputs `"Final Answer: ..."` which signals the entire pipeline is complete.  
   - The system logs a final success status and returns.

## 5. Additional Notes

- **Thread Safety & DB Transactions**:  
  - Because the pipeline is asynchronous (often in Celery tasks), each run must manage its own DB session.  
  - The code in `run(...)` can rollback or commit as needed.
  
- **ToolExecutionTracker**:  
  - A callback that captures the name of the last tool used. This helps with logging or displaying which sub-agent is active.

- **Extensibility**:  
  - Additional sub-agents can be easily appended to the `self.tools` list (e.g., a “DocumentationTool”).
  - Additional logic can be added to handle specialized agent outputs or new user-interaction flows.

## 6. Conclusion

**CoreAgent** is the heart of the multi-agent pipeline, orchestrating each sub-agent, managing user confirmations, and ensuring the entire process is logged and consistent. By combining the specialized tools and a well-defined prompt, it creates a flexible workflow capable of handling a variety of development tasks from initial analysis to final deployment.