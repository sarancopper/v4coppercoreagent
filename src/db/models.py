# v4coppercoreagent/src/db/models.py
import os
from sqlalchemy import (
    create_engine, Column, Integer, String, URL, DateTime, JSON, ForeignKey, Text
)
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

# Load database environment variables
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

print(f"DATABASE_URL {DATABASE_URL}")
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define all tables
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

class Project(Base):
    __tablename__= "projects"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_name = Column(String(200), nullable=False)
    domain = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    status = Column(String(25), nullable=False, default="active")  
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)  
    description = Column(String(256), nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(String(10), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    project_name = Column(String(200), nullable=False)
    agent_name = Column(String(200), nullable=False)
    status = Column(String(25), nullable=False, default="pending")  
    output = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class TaskQuestionsAnswers(Base):
    __tablename__= "task_questions_answers"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String(200), nullable=False)  
    question = Column(JSON, nullable=False)  
    answer = Column(JSON, nullable=True)  
    answer_by = Column(Integer, nullable=True)  
    status = Column(String(25), nullable=False, default="pending")  
    output = Column(Text)  
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class UserConfirmation(Base):
    __tablename__ = "user_confirmations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String(200), nullable=False)  
    ai_response = Column(Text, nullable=False)  
    status = Column(String(25), nullable=False, default="pending")  
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Now Define Relationships After All Tables Have Been Declared
User.projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
User.tasks = relationship("TaskModel", back_populates="user", cascade="all, delete-orphan")
User.questions = relationship("TaskQuestionsAnswers", back_populates="user", cascade="all, delete-orphan")
User.confirmations = relationship("UserConfirmation", back_populates="user", cascade="all, delete-orphan")

Project.user = relationship("User", back_populates="projects")
Project.tasks = relationship("TaskModel", back_populates="project", cascade="all, delete-orphan")
Project.task_logs = relationship("TaskLog", back_populates="project", cascade="all, delete-orphan")
Project.questions = relationship("TaskQuestionsAnswers", back_populates="project", cascade="all, delete-orphan")
Project.confirmations = relationship("UserConfirmation", back_populates="project", cascade="all, delete-orphan")

TaskModel.user = relationship("User", back_populates="tasks")
TaskModel.project = relationship("Project", back_populates="tasks")
TaskModel.logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
TaskModel.questions = relationship("TaskQuestionsAnswers", back_populates="task", cascade="all, delete-orphan")
TaskModel.confirmations = relationship("UserConfirmation", back_populates="task", cascade="all, delete-orphan")

TaskLog.project = relationship("Project", back_populates="task_logs")
TaskLog.task = relationship("TaskModel", back_populates="logs")

TaskQuestionsAnswers.user = relationship("User", back_populates="questions")
TaskQuestionsAnswers.task = relationship("TaskModel", back_populates="questions")
TaskQuestionsAnswers.project = relationship("Project", back_populates="questions")

UserConfirmation.user = relationship("User", back_populates="confirmations")
UserConfirmation.task = relationship("TaskModel", back_populates="confirmations")
UserConfirmation.project = relationship("Project", back_populates="confirmations")
