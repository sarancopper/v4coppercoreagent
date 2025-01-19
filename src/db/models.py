# v4coppercoreagent/src/db/models.py
import os
from sqlalchemy import create_engine, Column, Integer, String, URL
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

Base = declarative_base()

# Example model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True)
    password = Column(String(128))

# Load environment
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "saran@2023")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "v4coppercoreagent")

DATABASE_URL = URL.create(
    "mysql+pymysql",
    username=MYSQL_USER,
    password=MYSQL_PASSWORD,
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    database=MYSQL_DB
)


#DATABASE_URL = f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
print(f"DATABASE_URL {DATABASE_URL}")
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
