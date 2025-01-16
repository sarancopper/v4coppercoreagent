# v4coppercoreagent/scripts/start_celery_worker.ps1

# Activate virtual environment
. .\.venv\Scripts\activate

# Start Celery worker with your orchestrator service
celery -A src.orchestrator.orchestrator_service.celery_app worker --loglevel=info
