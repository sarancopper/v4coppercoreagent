from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.db.models import get_db
from src.utils.log_user_interaction import get_unanswered_questions

router = APIRouter()
@app.get("/get-ai-questions/{user_id}/{project_id}")
def get_ai_questions(user_id: int, project_id: int, db: Session = Depends(get_db)):
    unanswered = get_unanswered_questions(db, user_id, project_id)
    return {"pending_questions": [{"id": q.id, "questions": q.questions} for q in unanswered]}

# API to Submit Bulk User Answers
@app.post("/submit-ai-answers/")
def submit_ai_answers(user_id: int, project_id: int, answers: list, db: Session = Depends(get_db)):
    for answer in answers:
        store_user_answers(db, answer["id"], answer["responses"])
    return {"message": "User answers stored successfully."}