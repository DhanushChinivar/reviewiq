"""reviewiq — generateTrigger Lambda.

POST /reports/generate {"user_id": ...}
  → creates a job record (status=RUNNING), asynchronously invokes
    run_weekly_analysis for that user, and returns 202 with the job_id.

Why a separate trigger: the AI analysis takes 30-60s, but API Gateway hard-caps
a request at 29s. So instead of making the browser wait for the analysis (and
timing out), this returns right away and the analysis runs in the background
(async Lambda invoke). The frontend then polls GET /reports?job=<job_id> for the
job status — so a background FAILURE surfaces as a real error, not a silent hang.
"""

import json
import logging
import os
import time
import uuid

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

lambda_client = boto3.client("lambda")
dynamodb = boto3.resource("dynamodb")
ANALYSIS_FUNCTION = os.environ["ANALYSIS_FUNCTION"]
jobs_table = dynamodb.Table(os.environ["JOBS_TABLE"])
users_table = dynamodb.Table(os.environ["USERS_TABLE"])


def _capture_email(user_id, email):
    """Remember the user's email so weekly/on-demand reports reach them, not the default."""
    if not email:
        return
    try:
        users_table.put_item(Item={"user_id": user_id, "email": email})
    except Exception:  # noqa: BLE001 — email capture is best-effort, never block the request
        logger.exception("user_email_capture_failed")

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def _resp(status, body):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body)}


def handler(event, context):
    if (event.get("httpMethod") or "").upper() == "OPTIONS":  # CORS preflight
        return _resp(200, {"ok": True})

    # Identity comes from the verified Clerk JWT (the authorizer), NEVER the body.
    authz = (event.get("requestContext") or {}).get("authorizer") or {}
    user_id = authz.get("user_id")
    if not user_id:
        return _resp(401, {"error": "unauthorized"})

    body = json.loads(event.get("body") or "{}")
    _capture_email(user_id, body.get("email"))

    # Record the job as RUNNING before we kick off the work, so the frontend can
    # poll its status. Auto-expires after 24h via TTL.
    job_id = str(uuid.uuid4())
    now = int(time.time())
    jobs_table.put_item(Item={
        "job_id": job_id,
        "user_id": user_id,
        "status": "RUNNING",
        "created_at": now,
        "expires_at": now + 86400,
    })

    # Fire-and-forget: InvocationType="Event" returns immediately; the analysis
    # Lambda runs on its own (up to its 120s timeout), free of the 29s API cap.
    lambda_client.invoke(
        FunctionName=ANALYSIS_FUNCTION,
        InvocationType="Event",
        Payload=json.dumps({"user_id": user_id, "job_id": job_id}).encode(),
    )
    logger.info(json.dumps({"event": "analysis_triggered", "user_id": user_id, "job_id": job_id}))
    return _resp(202, {"status": "started", "job_id": job_id})
