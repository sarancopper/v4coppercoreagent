import os
from pathlib import Path
from dotenv import load_dotenv

# FastAPI imports
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# SQLAlchemy models (adjust paths to your project layout)
from db.models import SessionLocal, engine  # Example references
from db.models import Base  # If you have a Base model for metadata

# 1) Load env variables from .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# 2) Create the FastAPI app
app = FastAPI(
    title="Copper Core Agent Platform",
    description="Copper-Core Agent Platform",
    version="0.1.0"
)

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

