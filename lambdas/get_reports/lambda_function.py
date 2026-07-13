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
DATA_BUCKET = os.environ["DATA_BUCKET"]


def handler(event, context):
    params = event.get("queryStringParameters") or {}
    user_id = params.get("user_id", "u123")

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
        }
        for r in rows
    ]

    latest = None
    if rows:
        obj = s3.get_object(Bucket=DATA_BUCKET, Key=rows[0]["s3_key"])
        latest = json.loads(obj["Body"].read())

    return _resp(200, {"user_id": user_id, "latest": latest, "history": history})


def _int(v):
    return int(v) if isinstance(v, (int, float, Decimal)) else None


def _resp(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body),
    }
