import os
from pathlib import Path
from dotenv import load_dotenv
import time

# FastAPI imports
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from src.github_integration.webhook_handler import router as github_webhook_router
from sqlalchemy.exc import OperationalError

# SQLAlchemy models (adjust paths to your project layout)
from src.db.models import SessionLocal, engine  # Example references
from src.db.models import Base  # If you have a Base model for metadata

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
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 5) Basic test endpoint
@app.get("/", response_class=JSONResponse)
def read_root():
    return {"msg": "Hello from v4coppercoreagent!"}

