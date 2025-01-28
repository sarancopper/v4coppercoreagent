import os
from pathlib import Path
from dotenv import load_dotenv
import time
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from src.github_integration.webhook_handler import router as github_webhook_router
from sqlalchemy.exc import OperationalError
from src.orchestrator.orchestrator_service import run_agent_task
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

@app.post("/start-agent")
def start_agent(requirement: str):
    """
    Kick off the entire multi-agent pipeline with a user requirement.
    """
    result = run_core_agent_task.delay(requirement)
    return {"status": "Agent started", "task_id": result.id}

class InteractionRequest(BaseModel):
    session_id: str
    questions: str

class AnswerSubmission(BaseModel):
    session_id: str
    answers: str

@app.post("/send-questions")
def send_questions(request: InteractionRequest):
    """
    Store clarifying questions for a session.
    """
    session_id = request.session_id
    questions = request.questions
    pending_questions[session_id] = {"questions": questions, "answers": None}
    return {"message": "Questions sent to user", "session_id": session_id}

@app.post("/submit-answers")
def submit_answers(request: AnswerSubmission):
    """
    Store user answers for a session.
    """
    session_id = request.session_id
    if session_id not in pending_questions:
        raise HTTPException(status_code=404, detail="Session not found")
    pending_questions[session_id]["answers"] = request.answers
    return {"message": "Answers received"}

def get_user_answers(session_id: str):
    """
    Waits for user answers and returns them when available.
    """
    while True:
        if session_id in pending_questions and pending_questions[session_id]["answers"]:
            answers = pending_questions[session_id]["answers"]
            del pending_questions[session_id]
            return answers
