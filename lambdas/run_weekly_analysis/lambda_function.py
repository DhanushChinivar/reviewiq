"""reviewiq — runWeeklyAnalysis Lambda (the AI brain).

Reads reviews from reviewiq-reviews, sends them to Amazon Bedrock (Claude
Sonnet 4.6), and asks for a structured intelligence report (sentiment, themes,
severity, anomalies, per-product breakdown). Saves the report to S3 and a
summary row to reviewiq-reports.

Runs in two modes:
  * Scheduled (EventBridge)  — event has no httpMethod. Analyses ALL users,
    returns a plain dict. This is the weekly autopilot.
  * On-demand (API Gateway)  — POST /reports/generate with {"user_id": ...}.
    Analyses just that one user's reviews and returns an HTTP response so the
    frontend's "Generate report now" button can show a report immediately
    instead of waiting for the weekly run.

MVP scope: analyses ALL reviews in the table (no 7-day window yet). A later
version filters to the last 7 days and compares against the previous week's
report for trend detection.
"""

import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

bedrock = boto3.client("bedrock-runtime")
dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
lambda_client = boto3.client("lambda")
reviews_table = dynamodb.Table(os.environ["REVIEWS_TABLE"])
reports_table = dynamodb.Table(os.environ["REPORTS_TABLE"])
DATA_BUCKET = os.environ["DATA_BUCKET"]
MODEL_ID = os.environ["MODEL_ID"]
SEND_REPORT_FUNCTION = os.environ.get("SEND_REPORT_FUNCTION")

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}

INSTRUCTIONS = (
    "You are a product-review analyst. Analyze the reviews and return ONLY a JSON "
    "object (no prose, no markdown fences) with this exact shape:\n"
    '{"sentiment_score": <int 0-100>, "week_summary": "<2-3 sentences>", '
    '"themes": [{"theme": "str", "mentions": <int>, "severity": "high|medium|low", '
    '"priority": "red|yellow|green", "recommended_actions": ["str"]}], '
    '"top_praises": [{"theme": "str", "mentions": <int>}], '
    '"anomalies": ["str"], '
    '"products": [{"product_name": "str", "sentiment_score": <int>, "review_count": <int>}], '
    '"confidence_score": <float 0-1>}'
)


def handler(event, context):
    is_http = "httpMethod" in event or bool(event.get("requestContext"))

    # --- On-demand (API Gateway) mode ----------------------------------------
    if is_http:
        if (event.get("httpMethod") or "").upper() == "OPTIONS":  # CORS preflight
            return _http_resp(200, {"ok": True})
        body = json.loads(event.get("body") or "{}")
        target_user = body.get("user_id")
        if not target_user:
            return _http_resp(400, {"error": "user_id is required"})
    # --- Scheduled (EventBridge) mode ----------------------------------------
    else:
        # A direct/manual async invoke may still target one user.
        target_user = event.get("user_id")

    items = reviews_table.scan().get("Items", [])
    by_user = defaultdict(list)
    for it in items:
        by_user[it.get("user_id", "unknown")].append(it)

    # In on-demand mode, only analyse the requesting user.
    if target_user:
        reviews = by_user.get(target_user, [])
        if not reviews:
            msg = {"status": "no_reviews", "reports_created": 0, "user_id": target_user}
            return _http_resp(404, msg) if is_http else msg
        by_user = {target_user: reviews}

    if not by_user:
        msg = {"status": "no_reviews", "reports_created": 0}
        return _http_resp(404, msg) if is_http else msg

    last_report = None
    reports_created = 0
    for user_id, reviews in by_user.items():
        last_report = _generate_for_user(user_id, reviews)
        reports_created += 1

    if is_http:
        return _http_resp(200, {
            "reports_created": reports_created,
            "report_date": last_report["report_date"],
            "sentiment_score": last_report["sentiment_score"],
        })
    return {"reports_created": reports_created}


def _generate_for_user(user_id, reviews):
    """Run Bedrock on one user's reviews; persist report to S3 + DynamoDB; email it."""
    payload = [
        {
            "product": r.get("product_name"),
            "rating": int(r["rating"]) if r.get("rating") is not None else None,
            "text": r.get("review_text"),
            "platform": r.get("platform"),
            "source": r.get("source"),
        }
        for r in reviews
    ]
    prompt = f"{INSTRUCTIONS}\n\nReviews (JSON):\n{json.dumps(payload)}"

    resp = bedrock.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 2000},
    )
    text = "".join(b.get("text", "") for b in resp["output"]["message"]["content"])
    report = _extract_json(text)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    s3_key = f"reports/{user_id}/{today}/report.json"
    s3.put_object(Bucket=DATA_BUCKET, Key=s3_key, Body=json.dumps(report).encode())

    ss = report.get("sentiment_score")
    sentiment = int(ss) if isinstance(ss, (int, float)) else None
    reports_table.put_item(
        Item={
            "user_id": user_id,
            "report_date": today,
            "s3_key": s3_key,
            "sentiment_score": sentiment,
            "summary": report.get("week_summary"),
            "review_count": len(reviews),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    # Chain to sendReport so the report is emailed (fire-and-forget async invoke).
    if SEND_REPORT_FUNCTION:
        lambda_client.invoke(
            FunctionName=SEND_REPORT_FUNCTION,
            InvocationType="Event",
            Payload=json.dumps({"user_id": user_id}).encode(),
        )
    logger.info(json.dumps({"event": "report_created", "user_id": user_id, "reviews": len(reviews)}))
    return {"report_date": today, "sentiment_score": sentiment}


def _http_resp(status, body):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body)}


def _extract_json(text):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {"error": "no_json_in_response", "raw": text[:500]}
    return json.loads(text[start : end + 1])
