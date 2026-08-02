"""reviewiq — generateTrigger Lambda.

POST /reports/generate {"user_id": ...}
  → asynchronously invokes run_weekly_analysis for that user and returns 202
    immediately.

Why a separate trigger: the AI analysis takes 30-60s, but API Gateway hard-caps
a request at 29s. So instead of making the browser wait for the analysis (and
timing out), this returns right away and the analysis runs in the background
(async Lambda invoke). The frontend then polls GET /reports until the new report
appears. Classic decoupling — the same reason SQS sits in the ingest path.
"""

import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

lambda_client = boto3.client("lambda")
ANALYSIS_FUNCTION = os.environ["ANALYSIS_FUNCTION"]

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

    body = json.loads(event.get("body") or "{}")
    user_id = body.get("user_id")
    if not user_id:
        return _resp(400, {"error": "user_id is required"})

    # Fire-and-forget: InvocationType="Event" returns immediately; the analysis
    # Lambda runs on its own (up to its 120s timeout), free of the 29s API cap.
    lambda_client.invoke(
        FunctionName=ANALYSIS_FUNCTION,
        InvocationType="Event",
        Payload=json.dumps({"user_id": user_id}).encode(),
    )
    logger.info(json.dumps({"event": "analysis_triggered", "user_id": user_id}))
    return _resp(202, {"status": "started"})
