from langchain.agents import Tool
from sqlalchemy.orm import Session
from src.db.models import SessionLocal
from src.utils.log_user_interaction import store_ai_questions

def user_interaction_tool_func(task_id: int, user_id: int, project_id: int, agent_name: str, questions: list) -> str:
    """
    Store AI-generated batch of questions and wait for user responses before proceeding.
    """
    db: Session = SessionLocal()

    # Store AI-generated batch of questions in the database
    store_ai_questions(db, task_id, user_id, project_id, agent_name, questions)
    
    return f"Questions logged in DB. Waiting for user response..."
    
UserInteractionTool = Tool(
    name="user_interaction",
    func=user_interaction_tool_func,
    description="Logs AI-generated batch of questions and waits for user responses."
)


# The current implementation of `user_interaction_tool_func` is functional for a **console-based** application, but it’s not suitable for **web-based APIs** or user interfaces because it relies on **`input()`**, which is a blocking operation.

# For a web-based app, you need to:
# 1. **Send the questions to the web interface** through an API or other mechanism.
# 2. **Pause the execution** until the user responds.
# 3. **Resume execution** with the user's answers.

# Here’s how to adapt your `user_interaction_tool_func` for a web-based workflow:

# ---

# ## Updated `user_interaction_tool_func` for Web Integration

# The `user_interaction_tool_func` should:
# 1. Store the questions in a database or send them to the web client via an API.
# 2. Pause execution and wait for the user's response.
# 3. Retrieve the user's response from the database or API and return it to the agent.

# ### Example Implementation

# ```python
# from langchain.agents import Tool

# # Simulate storage for pending user interactions
# pending_questions = {}

# def user_interaction_tool_func(questions: str, session_id: str) -> str:
#     """
#     Sends clarifying questions to the web interface and waits for user input.
#     """
#     print(f"\nThe agent has the following clarifying questions for session {session_id}:\n{questions}")

#     # Simulate storing the questions for the session
#     pending_questions[session_id] = questions

#     # Simulate waiting for user input via the web interface
#     print(f"Waiting for user response for session {session_id}...")

#     # Replace with logic to poll or fetch user responses from the web interface
#     while True:
#         if session_id in pending_questions and isinstance(pending_questions[session_id], str):
#             user_input = pending_questions[session_id]
#             del pending_questions[session_id]  # Clear the entry after retrieving input
#             return user_input

# # Define the UserInteractionTool
# UserInteractionTool = Tool(
#     name="user_interaction",
#     func=user_interaction_tool_func,
#     description="Asks the user clarifying questions and collects responses. Requires a session ID."
# )
# ```

# ---

# ## Key Changes

# 1. **Session Management**:  
#    Each interaction is tied to a `session_id` to distinguish between different user sessions. The `session_id` can be the API request's identifier or user token.

# 2. **Store Pending Questions**:  
#    The questions are temporarily stored in a `pending_questions` dictionary (or database) with the `session_id` as the key:
#    ```python
#    pending_questions[session_id] = questions
#    ```

# 3. **Wait for User Response**:  
#    The function continuously checks for a response from the web interface:
#    ```python
#    while True:
#        if session_id in pending_questions and isinstance(pending_questions[session_id], str):
#            user_input = pending_questions[session_id]
#            del pending_questions[session_id]
#            return user_input
#    ```

# 4. **Replace `input()`**:  
#    Instead of using `input()`, the function relies on external input (e.g., from an API or polling mechanism).

# ---

# ## How to Integrate with a Web App

# ### API Workflow for User Interaction

# 1. **Send Questions to the Web App**  
#    When the agent calls `user_interaction_tool_func`, the questions are stored or sent to the web app's API (e.g., via a database or in-memory store).

# 2. **Expose an API for User Responses**  
#    Create an API endpoint where the web client sends the user's answers. For example:
#    ```python
#    @app.post("/submit-answers")
#    def submit_answers(session_id: str, answers: str):
#        pending_questions[session_id] = answers
#        return {"message": "Answers received"}
#    ```

# 3. **Fetch User Responses**  
#    The `user_interaction_tool_func` retrieves the answers from `pending_questions` and passes them back to the agent.

# ---

# ### Example API Setup

# Here’s how to implement the workflow in FastAPI:

# ```python
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel

# app = FastAPI()

# # Store pending questions and responses
# pending_questions = {}

# class InteractionRequest(BaseModel):
#     session_id: str
#     questions: str

# class AnswerSubmission(BaseModel):
#     session_id: str
#     answers: str

# @app.post("/send-questions")
# def send_questions(request: InteractionRequest):
#     """
#     Store clarifying questions for a session.
#     """
#     session_id = request.session_id
#     questions = request.questions
#     pending_questions[session_id] = {"questions": questions, "answers": None}
#     return {"message": "Questions sent to user", "session_id": session_id}

# @app.post("/submit-answers")
# def submit_answers(request: AnswerSubmission):
#     """
#     Store user answers for a session.
#     """
#     session_id = request.session_id
#     if session_id not in pending_questions:
#         raise HTTPException(status_code=404, detail="Session not found")
#     pending_questions[session_id]["answers"] = request.answers
#     return {"message": "Answers received"}

# def get_user_answers(session_id: str):
#     """
#     Waits for user answers and returns them when available.
#     """
#     while True:
#         if session_id in pending_questions and pending_questions[session_id]["answers"]:
#             answers = pending_questions[session_id]["answers"]
#             del pending_questions[session_id]
#             return answers
# ```

# ---

# ### Updated `user_interaction_tool_func` for FastAPI

# Modify the `user_interaction_tool_func` to work with the FastAPI endpoints:

# ```python
# import requests
# import time

# def user_interaction_tool_func(questions: str, session_id: str) -> str:
#     """
#     Sends clarifying questions to the web interface and waits for user input.
#     """
#     # Send questions to the web app API
#     api_url = "http://localhost:8000/send-questions"
#     response = requests.post(api_url, json={"session_id": session_id, "questions": questions})
#     if response.status_code != 200:
#         raise Exception(f"Failed to send questions: {response.text}")

#     # Wait for user answers from the web app API
#     print(f"Waiting for user answers for session {session_id}...")
#     while True:
#         response = requests.get(f"http://localhost:8000/submit-answers/{session_id}")
#         if response.status_code == 200:
#             return response.json()["answers"]
#         time.sleep(2)  # Poll every 2 seconds
# ```

# ---

# ## Expected Workflow

# 1. The `user_interaction_tool_func` sends the questions to the `/send-questions` API.
# 2. The user submits answers via the web client to the `/submit-answers` API.
# 3. The `user_interaction_tool_func` retrieves the answers and passes them back to the agent.

# ---

# This implementation ensures seamless integration between your agent's `user_interaction` tool and the web interface, enabling dynamic and real-time user interaction.