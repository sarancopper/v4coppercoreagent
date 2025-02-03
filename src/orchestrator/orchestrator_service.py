# v4coppercoreagent/src/orchestrator/orchestrator_service.py

import os
from celery import Celery
from pathlib import Path
from src.db.models import SessionLocal, TaskModel
from src.agent_factory.generator import CodeGeneratorAgent
from src.agent_factory.core_agent import CoreAgent
from src.utils.log_agent_execution import log_agent_execution
from src.utils.log_user_interaction import (get_pending_user_confirmation, get_unanswered_questions)

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# REDIS_URL might come from your .env or fallback to localhost:
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create the Celery app
celery_app = Celery(
    "core_agent_orchestrator",
    broker=REDIS_URL,
    backend=REDIS_URL,
    broker_connection_retry_on_startup=True,
)

# Optional: Celery configuration
celery_app.conf.update(
    result_expires=3600,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Example: a simple test task
@celery_app.task
def add_numbers(x, y):
    return x + y

@celery_app.task
def sync_code_and_validate(repo: str, commit_id: str, branch: str):
    """
    Pull the latest code from GitHub and run validation.
    For example, run a Docker sandbox or local command to verify tests.
    """
    # 1. Clone or pull the code locally (for demonstration):
    #    In real usage, you might do a "git pull" or clone to a temp directory
    repo_url = f"https://github.com/{repo}.git"
    print(f"[Celery Task] Syncing {repo_url} at commit {commit_id} (branch {branch})")

    # 2. Pull/Checkout code (pseudo example):
    #    - Use subprocess or GitPython library
    #    - Then call the sandbox manager
    # E.g. subprocess.run(["git", "clone", "--single-branch", "--branch", branch, repo_url, "/tmp/mycode"], check=True)

    # 3. Run sandbox validation
    # from sandbox_manager.manager import run_sandbox_validation
    # run_sandbox_validation("/tmp/mycode")

    # 4. Log or return results
    print(f"[Celery Task] Validation complete for {repo} commit {commit_id}.")
    return {"repo": repo, "commit": commit_id, "branch": branch, "status": "validated"}

# @celery_app.task
# def run_agent_task(task_id: int):
#     db: Session = SessionLocal()
#     task = db.query(TaskModel).get(task_id)
#     if not task:
#         return f"No Task found with id {task_id}"

#     agent = CodeGeneratorAgent()
#     result = agent.run({"description": task.description, "payload": task.payload})

#     # Update DB
#     task.status = "completed"
#     db.commit()
#     db.close()

#     return result

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def run_core_agent_task(self, user_id:int, project_id:int, project_name:str, requirement: str):
    api_key = os.getenv("OPENAI_API_KEY", "")
    db: Session = SessionLocal()
    try:
        agent = CoreAgent(openai_api_key=api_key)
        print(f"Starting CoreAgent task for User: {user_id}, Project: {project_id} - {project_name}")

        result = agent.run(db, user_id, project_id, project_name, requirement)
        print(f"agent result:\n{result}\n")

       # Check if AI is waiting for user confirmation before proceeding
        pending_confirmations = get_pending_user_confirmation(db, user_id, project_id)
        while pending_confirmations:
            print(f"\n[WAITING] User confirmation required for Project {project_name}...\n")
            time.sleep(5)  # Polling every 5 seconds
            pending_confirmations = get_pending_user_confirmation(db, user_id, project_id)

        # Stop execution if AI reaches a final answer
        if "Final Answer:" in result:
            print(f"\n[COMPLETE] Core Agent Execution Completed for {project_name}\n")
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

        # Check if there are unanswered user questions
        unanswered_questions = get_unanswered_questions(db, user_id, project_id)
        while unanswered_questions:
            print(f"\n[WAITING] Awaiting user answers for clarifying questions...\n")
            time.sleep(5)  # Polling every 5 seconds
            unanswered_questions = get_unanswered_questions(db, user_id, project_id)

        print(f"\n[PROCEED] All user interactions handled. Resuming execution for {project_name}...\n")

        # Log task as successful
        log_agent_execution(
            db=db,
            user_id=user_id,
            project_id=project_id,
            project_name=project_name,
            agent_name="CoreAgent",
            status="completed",
            output=result
        )

        db.commit()
        return result
    except Exception as e:
        print(f"\n[ERROR] Core Agent Execution Failed for {project_name}: {e}\n")
        db.rollback()

        log_agent_execution(
            db=db,
            user_id=user_id,
            project_id=project_id,
            project_name=project_name,
            agent_name="CoreAgent",
            status="failed",
            output=str(e)
        )

        return f"Execution stopped due to error: {e}"

# @app.task(bind=True)
# def celery_shutdown(self):
#    app.control.revoke(self.id) # prevent this task from being executed again
#    app.control.shutdown() # send shutdown signal to all workers
