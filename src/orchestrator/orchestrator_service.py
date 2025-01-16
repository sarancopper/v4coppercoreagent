# v4coppercoreagent/src/orchestrator/orchestrator_service.py

import os
from celery import Celery

# If you're using .env for credentials, you could load them here as well.
from dotenv import load_dotenv
load_dotenv()

# REDIS_URL might come from your .env or fallback to localhost:
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create the Celery app
celery_app = Celery(
    "core_agent_orchestrator",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Optional: Celery configuration
celery_app.conf.update(
    result_expires=3600,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Example: a simple test task
@celery_app.task
def add_numbers(x, y):
    return x + y
