# src/dashboard/frontend/pages/projectdetails.py
import sys
import os
import time
# Get the absolute path of the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
# Ensure the project root is in sys.path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from sqlalchemy.orm import Session
from src.db.models import Project, TaskModel, TaskLog, get_db, TaskQuestionsAnswers
from src.orchestrator.orchestrator_service import run_core_agent_task
from src.utils.log_user_interaction import store_user_answers

AUTO_REFRESH_INTERVAL = 5  

def main():
    project_id = st.query_params['project_id']
    user_id = st.query_params['user_id']
    task_id = st.query_params['task_id']
    project_name = st.query_params['project_name']
    db: Session = next(get_db())
    if project_id:
        st.session_state["selected_project_id"] = int(project_id)
    if project_name:
        project_name = project_name.capitalize()
        st.session_state["selected_project_name"] = project_name

    if "selected_project_id" not in st.session_state:
        st.warning("No project selected. Please go to the Projects page.")
        return

    st.title(f" {project_name} - Details")
    project_id = st.session_state["selected_project_id"]

    # Fetch Project Logs
    logs = db.query(TaskLog).filter(TaskLog.project_id == project_id).order_by(TaskLog.created_at.desc()).all()

    # Fetch Pending Questions
    questions = db.query(TaskQuestionsAnswers).filter(
        TaskQuestionsAnswers.project_id == project_id, 
        TaskQuestionsAnswers.status == "pending"
    ).all()
    # Fetch the project
   # Fetch Project Details
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        st.error("Project not found!")
        return

    st.subheader(f"Project: {project.project_name}")
    st.write(f"Status: {project.status}")

    # Fetch Tasks
    tasks = db.query(TaskModel).filter(TaskModel.project_id == project_id).all()

    # If No Tasks, Show User Input for New Task
    if not tasks:
        st.warning("No tasks found for this project.")
        user_input = st.text_area("Enter a requirement or message for the Core Agent:")

        if st.button("Send"):
            if user_input.strip():
                result = run_core_agent_task.delay(
                    user_id=user_id,
                    task_id=task_id,
                    project_id=project.id,
                    project_name=project.project_name,
                    requirement=user_input
                )
                st.success(f"Task triggered! Task ID: {result.id}")
                st.session_state["task_started"] = True
    else:
        st.subheader("Tasks")
        for task in tasks:
            st.write(f"**{task.description}** - Status: {task.status}")

    # Auto-refresh Logs Every 5 Seconds
    st.subheader("Logs")
    log_placeholder = st.empty()
    auto_refresh = st.checkbox("Auto-refresh logs", value=True)

    while auto_refresh:
        logs = db.query(TaskLog).filter(TaskLog.project_id == project_id).order_by(TaskLog.created_at.desc()).all()
        with log_placeholder.container():
            if logs:
                for log in logs:
                    st.write(f"**[{log.agent_name}]** - {log.status}")
                    st.code(log.output, language="markdown")
            else:
                st.write("No logs found for tasks in this project.")
        time.sleep(5)
        st.rerun()

    # Fetch Pending Questions
    st.subheader("Interact with Core Agent")
    questions = db.query(TaskQuestionsAnswers).filter(
        TaskQuestionsAnswers.project_id == project_id,
        TaskQuestionsAnswers.status == "pending"
    ).all()

    if questions:
        answers = {}
        for q in questions:
            st.write(f"**{q.agent_name}:** {q.question}")
            answers[q.id] = st.text_area(f"Your answer for {q.agent_name}")

        if st.button("Submit Answers"):
            for q_id, answer in answers.items():
                if answer.strip():
                    # Store user answers (Function not included here)
                    st.success(f"Answered question {q_id}")
            st.rerun()  # Refresh page after submission
    else:
        st.write("No pending questions.")

if __name__ == "__main__":
    main()