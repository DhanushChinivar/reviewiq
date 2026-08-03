"""reviewiq — getReports Lambda.

GET /reports?user_id=...  → returns the user's latest full report (from S3) plus
a history of report summaries (from reviewiq-reports). Powers the dashboard.

NOTE (MVP): user_id comes from the query string. This is insecure — Phase 6
replaces it with the Clerk JWT (user_id must never come from client input in
production). Fine for the auth-less MVP.
"""

import json
import logging
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
reports_table = dynamodb.Table(os.environ["REPORTS_TABLE"])
jobs_table = dynamodb.Table(os.environ["JOBS_TABLE"])
DATA_BUCKET = os.environ["DATA_BUCKET"]


def handler(event, context):
    # Identity comes from the verified Clerk JWT (the authorizer), NEVER the URL.
    authz = (event.get("requestContext") or {}).get("authorizer") or {}
    user_id = authz.get("user_id")
    if not user_id:
        return _resp(401, {"error": "unauthorized"})

    params = event.get("queryStringParameters") or {}
    report_key = params.get("report")  # optional: a specific report_date to view
    job_id = params.get("job")          # optional: poll a generation job's status

    resp = reports_table.query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,  # newest report_date first
    )
    rows = resp.get("Items", [])

    history = [
        {
            "report_date": r.get("report_date"),
            "sentiment_score": _int(r.get("sentiment_score")),
            "summary": r.get("summary"),
            "review_count": _int(r.get("review_count")),
            "created_at": r.get("created_at"),  # lets the frontend detect a freshly-generated report
        }
        for r in rows
    ]

    # Pick which report to return the full body for: the requested one, else newest.
    row = None
    if report_key:
        row = next((r for r in rows if r.get("report_date") == report_key), None)
    if row is None and rows:
        row = rows[0]

    latest = None
    if row:
        obj = s3.get_object(Bucket=DATA_BUCKET, Key=row["s3_key"])
        latest = json.loads(obj["Body"].read())

    # Optional: report the status of an in-flight generation job so the frontend
    # can show RUNNING / SUCCEEDED / FAILED (a real failure notice, not a hang).
    job = None
    if job_id:
        j = jobs_table.get_item(Key={"job_id": job_id}).get("Item")
        if j and j.get("user_id") == user_id:  # only your own jobs
            job = {"status": j.get("status"), "error": j.get("error")}

    return _resp(200, {
        "user_id": user_id,
        "latest": latest,
        "history": history,
        "selected": row.get("report_date") if row else None,
        "job": job,
    })


def _int(v):
    return int(v) if isinstance(v, (int, float, Decimal)) else None


def _resp(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body),
    }
