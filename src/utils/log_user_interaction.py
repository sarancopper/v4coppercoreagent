from sqlalchemy.orm import Session
from src.db.models import TaskQuestionsAnswers

def store_ai_questions(db: Session, task_id: int, user_id: int, project_id: int, agent_name: str, questions: list):
    """
    Store AI-generated batch of questions in the database before waiting for user input.
    """
    question_entry = TaskQuestionsAnswers(
        task_id=task_id,
        user_id=user_id,
        project_id=project_id,
        agent_name=agent_name,
        questions=questions,  # Store multiple questions
        status="pending",
        answers=[]  # Empty until user responds
    )
    db.add(question_entry)
    db.commit()
    return question_entry

def get_unanswered_questions(db: Session, user_id: int, project_id: int):
    """
    Retrieve all unanswered questions for a user in batch format.
    """
    return db.query(TaskQuestionsAnswers).filter(
        TaskQuestionsAnswers.user_id == user_id,
        TaskQuestionsAnswers.project_id == project_id,
        TaskQuestionsAnswers.status == "pending"
    ).all()

def store_user_answers(db: Session, question_id: int, answers: list, answer_by: int):
    """
    Store user's batch answers in the database and update the question status.
    """
    question_entry = db.query(TaskQuestionsAnswers).filter(TaskQuestionsAnswers.id == question_id).first()
    if question_entry:
        question_entry.answers = answers
        question_entry.answer_by = answer_by
        question_entry.status = "answered"
        db.commit()
        return question_entry
    return None

# Approve or Reject AI Step Execution
def update_user_confirmation_status(db: Session, confirmation_id: int, user_id: int, project_id: int, agent_name: str, status: str):
    """
    Updates the user's confirmation status for a specific agent execution step.
    """
    confirmation_entry = (
        db.query(UserConfirmation)
        .filter(UserConfirmation.id == confirmation_id, UserConfirmation.user_id == user_id, 
                UserConfirmation.project_id == project_id, UserConfirmation.agent_name == agent_name)
        .first()
    )
    
    if confirmation_entry:
        confirmation_entry.status = status
        confirmation_entry.updated_at = func.now()
        db.commit()
        return {"status": "updated", "confirmation_id": confirmation_id, "agent": agent_name}
    else:
        return {"error": "Confirmation not found"}

def get_pending_user_confirmation(db: Session, user_id: int, project_id: int, agent_name: str):
    """
    Retrieves pending confirmations for a specific agent in a project.
    """
    return db.query(UserConfirmation).filter(
        UserConfirmation.user_id == user_id,
        UserConfirmation.project_id == project_id,
        UserConfirmation.agent_name == agent_name,
        UserConfirmation.status == "pending"
    ).all()

# Store AI Response & Wait for User Confirmation
def store_agent_confirmation(db: Session, user_id: int, project_id: int, agent_name: str, ai_response: str):
    """
    Store a pending confirmation request from an agent.
    """
    confirmation = UserConfirmation(
        user_id=user_id,
        project_id=project_id,
        agent_name=agent_name,
        ai_response=ai_response,
        status="pending"
    )
    db.add(confirmation)
    db.commit()
