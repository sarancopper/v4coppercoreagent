# v4coppercoreagent/src/db/models.py
import os
from sqlalchemy import create_engine, Column, Integer, String, URL, DateTime, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote

load_dotenv()

Base = declarative_base()

# Example model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True)
    password = Column(String(128))
    first_name = Column(String(128))
    last_name = Column(String(128))
    status = Column(String(10), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Load environment
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Saran@2023")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "coppercoreagent")

DATABASE_URL = URL.create(
    "mysql+pymysql",
    username=MYSQL_USER,
    password=MYSQL_PASSWORD,
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    database=MYSQL_DB
)
class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # User who initiated the task
    project_id = Column(Integer, nullable=False)  # Associated project
    description = Column(String(256), nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(String(10), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
#DATABASE_URL = f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
print(f"DATABASE_URL {DATABASE_URL}")
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # User who initiated the task
    project_id = Column(Integer, nullable=False)  # Associated project
    project_name = Column(String(200), nullable=False)  # Associated project
    agent_name = Column(String(200), nullable=False)  # The agent executing the task
    status = Column(String(25), nullable=False, default="pending")  # pending, in-progress, completed, failed
    output = Column(Text)  # The agent's execution output
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<TaskLog(agent={self.agent_name}, project={self.project_id}, status={self.status})>"

class Projects(Base):
    __tablename__= "projects"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # User who initiated the task
    project_name = Column(String(200), nullable=False)
    status = Column(String(25), nullable=False, default="active")  # active, inactive
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())

class TaskQuestionsAnswers(Base):
    __tablename__= "task_questions_answers"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, nullable=False)  # Associated Task
    user_id = Column(Integer, nullable=False)  # User who initiated the task
    project_id = Column(Integer, nullable=False)  # Associated project
    agent_name = Column(String(200), nullable=False)  # The agent executing the task
    question = Column(JSON, nullable=False)  # The question asked by AI
    answer = Column(JSON, nullable=True)  # The user's answer (NULL until answered)
    answer_by = Column(Integer, nullable=True)  # The user replyed to question
    status = Column(String(25), nullable=False, default="pending")  # pending, answered
    output = Column(Text)  # The agent's execution output
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    

class UserConfirmation(Base):
    __tablename__ = "user_confirmations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # User who needs to confirm
    project_id = Column(Integer, nullable=False)  # Project this confirmation belongs to
    agent_name = Column(String(200), nullable=False)  # Which agent requires confirmation (Analyze, Plan, etc.)
    ai_response = Column(Text, nullable=False)  # The response from AI that needs confirmation
    status = Column(String(25), nullable=False, default="pending")  # pending, confirmed, declined
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

Projects.tasks = relationship("TaskModel", back_populates="project")
TaskModel.logs = relationship("TaskLog", back_populates="task")
