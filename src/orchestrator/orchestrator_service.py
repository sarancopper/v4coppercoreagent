# v4coppercoreagent/src/orchestrator/orchestrator_service.py

import os
from celery import Celery
from pathlib import Path
from src.db.models import SessionLocal, TaskModel
from src.agent_factory.generator import CodeGeneratorAgent
from src.agent_factory.core_agent import CoreAgent
from src.utils.log_agent_execution import log_agent_execution
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

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 1})
def run_core_agent_task(self, user_id:int, task_id:int, project_id:int, project_name:str,  requirement: str):
    api_key = os.getenv("OPENAI_API_KEY", "")
    db: Session = SessionLocal()
    task_status = "failed"  # Default to failed unless execution succeeds
    task_output = ""

    try:
        print(f"Starting CoreAgent task for User: {user_id}, Project: {project_id} - {project_name}")

        existing_task = (
            db.query(TaskModel)
            .filter(TaskModel.user_id == user_id, TaskModel.project_id == project_id, TaskModel.status == "pending")
            .first()
        )

        if existing_task:
            print(f" Existing Pending Task Found: Task {existing_task.id}, skipping new task creation.")
            task_id = existing_task.id
        else:
            print(f" No existing task found. Creating new task.")
            new_task = TaskModel(
                user_id=user_id,
                project_id=project_id,
                description=requirement,
                status="pending"
            )
            db.add(new_task)
            db.commit()
            db.refresh(new_task)
            task_id = new_task.id
            print(f" Task Created: {task_id}")

        agent = CoreAgent(db=db, user_id=user_id, task_id=task_id, project_id=project_id, project_name=project_name, requirement=requirement)

        # Run the Core Agent
        result = agent.run(requirement)
        print(f"agent result:\n{result}\n")

        # Determine task status
        if "Final Answer:" in result:
            task_status = "completed"
        elif "Waiting for user input" in result:
            task_status = "waiting_user_input"

        task_output = result

        log_agent_execution(
            db=db,
            user_id=user_id,
            project_id=project_id,
            project_name=project_name,
            task_id=task_id,
            agent_name="CoreAgent",
            status=task_status,
            output=task_output
        )
        db.commit()
    except Exception as e:
        print(f"\n[ERROR] Core Agent Execution Failed for {project_name}: {e}\n")
        task_status = "failed"
        task_output = str(e)
    finally:
        db.close()
    return task_output
