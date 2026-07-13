"""reviewiq — runWeeklyAnalysis Lambda (the AI brain).

Reads reviews from reviewiq-reviews, sends them to Amazon Bedrock (Claude
Sonnet 4.6), and asks for a structured intelligence report (sentiment, themes,
severity, anomalies, per-product breakdown). Saves the report to S3 and a
summary row to reviewiq-reports.

MVP scope: analyses ALL reviews in the table, one report per user_id. A later
version filters to the last 7 days and is triggered weekly by EventBridge, and
compares against the previous week's report for trend detection.
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
    items = reviews_table.scan().get("Items", [])
    if not items:
        return {"status": "no_reviews", "reports_created": 0}

    by_user = defaultdict(list)
    for it in items:
        by_user[it.get("user_id", "unknown")].append(it)

    reports_created = 0
    for user_id, reviews in by_user.items():
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
        reports_table.put_item(
            Item={
                "user_id": user_id,
                "report_date": today,
                "s3_key": s3_key,
                "sentiment_score": int(ss) if isinstance(ss, (int, float)) else None,
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
        reports_created += 1

    return {"reports_created": reports_created}


def _extract_json(text):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {"error": "no_json_in_response", "raw": text[:500]}
    return json.loads(text[start : end + 1])
