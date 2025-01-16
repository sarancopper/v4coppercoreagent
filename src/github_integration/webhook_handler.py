# v4coppercoreagent/src/github_integration/webhook_handler.py
import os
import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv
from pathlib import Path

router = APIRouter()
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
# Optional: read a secret from .env for verifying GitHub signatures
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

@router.post("/github-webhook")
async def github_webhook(request: Request):
    """
    Handle POST requests from GitHub. Typically invoked when a push occurs.
    """
    # 1. Read raw body (for signature checking, if needed)
    body = await request.body()

    # 2. Verify signature (if GITHUB_WEBHOOK_SECRET is set)
    if GITHUB_WEBHOOK_SECRET:
        signature = request.headers.get("X-Hub-Signature-256")  # e.g. "sha256=..."
        if not signature:
            raise HTTPException(status_code=400, detail="Missing X-Hub-Signature-256 header")

        sha_name, received_sig = signature.split("=")
        if sha_name != "sha256":
            raise HTTPException(status_code=400, detail="Only sha256 is supported")

        # Compute HMAC for verification
        mac = hmac.new(GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256)
        expected_sig = mac.hexdigest()

        if not hmac.compare_digest(received_sig, expected_sig):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # 3. Parse JSON payload
    payload = await request.json()

    # You can check the event type:
    event_type = request.headers.get("X-GitHub-Event")  # "push", "pull_request", etc.
    if event_type == "push":
        # Extract relevant info from the payload
        repo = payload["repository"]["full_name"]
        commit_id = payload["after"]  # Last commit hash
        branch_ref = payload["ref"]   # e.g. "refs/heads/main"

        # Queue a Celery task for code sync/validation, passing these details
        from orchestrator.orchestrator_service import sync_code_and_validate
        sync_code_and_validate.delay(repo=repo, commit_id=commit_id, branch=branch_ref)

    return {"status": "Webhook received", "event": event_type}
