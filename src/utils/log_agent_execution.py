from sqlalchemy.orm import (Session, joinedload)
from src.db.models import TaskLog

def log_agent_execution(db: Session, user_id: int, project_id: int, project_name: str, agent_name: str, status: str, output: str):
    """
    Logs agent execution details into the database.
    """
    log_entry = TaskLog(
        user_id=user_id,
        project_id=project_id,
        project_name=project_name,
        agent_name=agent_name,
        status=status,
        output=output
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)  # Ensure object is attached to the session
    return log_entry
