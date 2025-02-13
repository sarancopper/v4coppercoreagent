import os
from pathlib import Path
from dotenv import load_dotenv
import time
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from src.github_integration.webhook_handler import router as github_webhook_router
from sqlalchemy.exc import OperationalError
from src.orchestrator.orchestrator_service import run_core_agent_task

from src.db.models import SessionLocal, engine, Base, get_db, TaskModel
from src.db.tasks import TaskCreate, TaskRead

# 1) Load env variables from .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

MAX_TRIES = 10
WAIT_SECONDS = 2

def try_connect(engine):
    attempts = 0
    while attempts < MAX_TRIES:
        try:
            connection = engine.connect()
            connection.close()
            print("Connected to MySQL!")
            return
        except OperationalError:
            attempts += 1
            print(f"Cannot connect, retrying in {WAIT_SECONDS}s... (attempt {attempts}/{MAX_TRIES})")
            time.sleep(WAIT_SECONDS)
    raise Exception("Could not connect to MySQL after several attempts.")

# 2) Create the FastAPI app
app = FastAPI(
    title="Copper Core Agent Platform",
    description="Copper-Core Agent Platform",
    version="0.1.0"
)
app.include_router(github_webhook_router, prefix="/webhook", tags=["GitHub Webhook"])

try_connect(engine)  # Retries up to 10 times
# 3) (Optional) Create the database tables if they don't exist
#    Usually you'd run migrations, but for a minimal test you can do:
Base.metadata.create_all(bind=engine)

# 4) Dependency to get DB session

# 5) Basic test endpoint
@app.get("/", response_class=JSONResponse)
def read_root():
    return {"msg": "Hello from v4coppercoreagent!"}

@app.post("/tasks", response_model=TaskRead)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    # 1) Create the task in DB
    print("new task process starting..... ")
    db_task = TaskModel(
        description=task_in.description,
        payload=task_in.payload,
        status="pending"
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # 2) Enqueue the Celery task
    run_agent_task(db_task.id)

    return db_task

@app.post("/new-core-agent-task", response_model=TaskRead)
async def start_agent(user_id: int, task_id: int, project_id: int, project_name: str, requirement: str, db: Session = Depends(get_db)):
    """
    Kick off the entire multi-agent pipeline with a user requirement.
    """
    print("new core task process starting..... ")
    db_task = TaskModel(
            user_id=user_id,
            task_id=task_id,
            project_id=project_id,
            description=requirement,
            status="pending"
        )        
    try: 
        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        result = run_core_agent_task.delay(user_id=user_id, task_id=task_id, project_id=project_id, project_name=project_name, requirement=requirement)
        
        db_task.status = "completed"
        db.commit()
        db.close()
        return db_task
    except Exception as e:
        db_task.status = "failed"
        db.commit()
        db.close()
        return db_task
