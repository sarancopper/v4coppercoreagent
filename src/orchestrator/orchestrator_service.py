# v4coppercoreagent/src/orchestrator/orchestrator_service.py

import os
from celery import Celery
from pathlib import Path
from src.db.models import SessionLocal, TaskModel
from src.agent_factory.generator import CodeGeneratorAgent

# If you're using .env for credentials, you could load them here as well.
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

@celery_app.task
def run_agent_task(task_id: int):
    db: Session = SessionLocal()
    task = db.query(TaskModel).get(task_id)
    if not task:
        return f"No Task found with id {task_id}"

    agent = CodeGeneratorAgent()
    result = agent.run({"description": task.description, "payload": task.payload})

    # Update DB
    task.status = "completed"
    db.commit()
    db.close()

    return result
