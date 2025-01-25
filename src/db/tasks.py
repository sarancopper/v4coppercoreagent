# src/db/tasks.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskCreate(BaseModel):
    description: str
    payload: Optional[dict] = None

class TaskRead(BaseModel):
    id: int
    description: str
    payload: dict
    response: dict
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
