from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.db.models import get_db
from src.utils.log_user_interaction import (update_user_confirmation_status, get_pending_user_confirmation)

router = APIRouter()

# API to Get Pending User Confirmations
@app.get("/get-agent-confirmations/{user_id}/{project_id}/{agent_name}")
def get_agent_confirmations(user_id: int, project_id: int, task_id: int, agent_name: str, db: Session = Depends(get_db)):
    """
    Retrieve pending confirmations for a specific agent in a project.
    """
    pending = get_pending_user_confirmation(db, user_id, task_id, project_id, agent_name)
    
    return {
        "pending_confirmations": [
            {"id": c.id, "agent_name": c.agent_name, "ai_response": c.ai_response}
            for c in pending
        ]
    }

# API to Submit User Confirmation (Approve or Reject)
@app.post("/submit-agent-confirmation/")
def submit_agent_confirmation(confirmation_id: int, status: str, db: Session = Depends(get_db)):
    update_user_confirmation_status(db, confirmation_id, status)
    return {"message": f"Agent step {status} successfully."}