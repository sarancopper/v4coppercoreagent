# src/dashboard/frontend/pages/projectdetails.py
import sys
import os

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
    st.title("Project Details & Core Agent Interaction")

    db: Session = next(get_db())

    # Retrieve the selected project ID from session, if any
    project_id = st.session_state.get("selected_project_id", None)
    if not project_id:
        st.write("No project selected. Go to the Projects page first.")
        return

    # Fetch Project Logs
    logs = db.query(TaskLog).filter(TaskLog.project_id == project_id).order_by(TaskLog.created_at.desc()).all()

    # Fetch Pending Questions
    questions = db.query(TaskQuestionsAnswers).filter(
        TaskQuestionsAnswers.project_id == project_id, 
        TaskQuestionsAnswers.status == "pending"
    ).all()
    # Fetch the project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        st.write("Project not found in DB.")
        return

    st.subheader(f"Project: {project.project_name}")
    st.write(f"Domain: {project.domain}")
    st.write(f"Description: {project.description}")

    # Display tasks
    st.subheader("Tasks")
    tasks = db.query(TaskModel).filter(TaskModel.project_id == project.id).all()
    if tasks:
        task_data = []
        for t in tasks:
            task_data.append({
                "Task ID": t.id,
                "Description": t.description,
                "Status": t.status,
                "Created": t.created_at
            })
        st.table(task_data)
    else:
        st.write("No tasks found for this project.")

    # Display logs
    st.subheader("Logs")
    logs = (
        db.query(TaskLog)
        .join(TaskModel, TaskModel.id == TaskLog.task_id)
        .filter(TaskModel.project_id == project.id)
        .all()
    )
    if logs:
        log_data = []
        for log in logs:
            log_data.append({
                "Log ID": log.id,
                "Task ID": log.task_id,
                "Agent": log.agent_name,
                "Status": log.status,
                "Output": log.output[:100] + "..." if log.output else "",
                "Created": log.created_at
            })
        st.table(log_data)
    else:
        st.write("No logs found for tasks in this project.")

    st.subheader("Interact with Core Agent")
    user_input = st.text_area("Enter a requirement or message for the Core Agent:")
    if st.button("Send to Core Agent"):
        # Example: call your Celery or orchestrator to run the agent
        # For demonstration, let's do a mock call
        result = run_core_agent_task.delay(user_id=1, project_id=project.id, project_name=project.project_name, requirement=user_input)
        st.write("Task triggered. Check logs for updates.")
        
        # Mock immediate response
        st.write(f"**CoreAgent** processed: `{user_input}`")

if __name__ == "__main__":
    main()
