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

# On-demand (API) calls must return before API Gateway's hard 29s limit, so we
# cap how many reviews go to Bedrock in that mode (most recent first). The
# scheduled job has no such cap. Output is bounded too (top products / themes)
# so the JSON never truncates against maxTokens.
ON_DEMAND_MAX_REVIEWS = 350
MAX_OUTPUT_TOKENS = 4000

INSTRUCTIONS = (
    "You are a product-review analyst. Analyze the reviews and return ONLY a JSON "
    "object (no prose, no markdown fences) with this exact shape:\n"
    '{"sentiment_score": <int 0-100>, "week_summary": "<2-3 sentences>", '
    '"themes": [{"theme": "str", "mentions": <int>, "severity": "high|medium|low", '
    '"priority": "red|yellow|green", "recommended_actions": ["str"]}], '
    '"top_praises": [{"theme": "str", "mentions": <int>}], '
    '"anomalies": ["str"], '
    '"products": [{"product_name": "str", "sentiment_score": <int>, "review_count": <int>}], '
    '"confidence_score": <float 0-1>}\n'
    "Keep the response compact so it fits the token budget: at most 8 themes, at most "
    "5 top_praises, at most 3 anomalies, and in \"products\" include ONLY the 15 "
    "products with the most reviews (skip the rest)."
)


def handler(event, context):
    is_http = "httpMethod" in event or bool(event.get("requestContext"))

    # CORS preflight — answer before doing anything else.
    if is_http and (event.get("httpMethod") or "").upper() == "OPTIONS":
        return _http_resp(200, {"ok": True})

    # Wrap the work so ANY failure in HTTP mode still returns a CORS response.
    # Without this, an unhandled exception yields a bare API Gateway 5xx with no
    # Access-Control-Allow-Origin header — which the browser reports only as the
    # opaque "Failed to fetch".
    try:
        return _run(event, is_http)
    except Exception as e:  # noqa: BLE001 — surface a clean error to the client
        logger.exception("analysis_failed")
        if is_http:
            return _http_resp(500, {"error": "analysis_failed", "detail": str(e)[:300]})
        raise


def _run(event, is_http):
    if is_http:
        body = json.loads(event.get("body") or "{}")
        target_user = body.get("user_id")
        if not target_user:
            return _http_resp(400, {"error": "user_id is required"})
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
        total = len(reviews)
        sample = reviews
        # On-demand: cap the input so the whole call finishes inside API Gateway's
        # 29s window. Take the most recent reviews (dates are ISO strings).
        if is_http and total > ON_DEMAND_MAX_REVIEWS:
            sample = sorted(reviews, key=lambda r: r.get("date") or "", reverse=True)[:ON_DEMAND_MAX_REVIEWS]
        last_report = _generate_for_user(user_id, sample, total=total)
        reports_created += 1

    if is_http:
        return _http_resp(200, {
            "reports_created": reports_created,
            "report_date": last_report["report_date"],
            "sentiment_score": last_report["sentiment_score"],
            "analyzed": last_report["analyzed"],
            "total_reviews": last_report["total"],
        })
    return {"reports_created": reports_created}


def _generate_for_user(user_id, reviews, total=None):
    """Run Bedrock on one user's reviews; persist report to S3 + DynamoDB; email it.

    `reviews` is the (possibly capped) sample actually sent to Bedrock; `total`
    is the full count the user has, for honest reporting in the UI.
    """
    total = total if total is not None else len(reviews)
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
        inferenceConfig={"maxTokens": MAX_OUTPUT_TOKENS},
    )
    text = "".join(b.get("text", "") for b in resp["output"]["message"]["content"])
    report = _extract_json(text)

    # The sort key is a full timestamp (not just a date), so every generation is
    # its own row in history instead of overwriting the day's report. The S3 key
    # is unique per generation too, so each history row points at its own report.
    now = datetime.now(timezone.utc)
    report_ts = now.isoformat()
    key_ts = now.strftime("%Y%m%dT%H%M%S%fZ")
    s3_key = f"reports/{user_id}/{key_ts}.json"
    s3.put_object(Bucket=DATA_BUCKET, Key=s3_key, Body=json.dumps(report).encode())

    ss = report.get("sentiment_score")
    sentiment = int(ss) if isinstance(ss, (int, float)) else None
    reports_table.put_item(
        Item={
            "user_id": user_id,
            "report_date": report_ts,
            "s3_key": s3_key,
            "sentiment_score": sentiment,
            "summary": report.get("week_summary"),
            "review_count": len(reviews),
            "created_at": report_ts,
        }
    )
    # Chain to sendReport so the report is emailed (fire-and-forget async invoke).
    if SEND_REPORT_FUNCTION:
        lambda_client.invoke(
            FunctionName=SEND_REPORT_FUNCTION,
            InvocationType="Event",
            Payload=json.dumps({"user_id": user_id}).encode(),
        )
    logger.info(json.dumps({"event": "report_created", "user_id": user_id, "analyzed": len(reviews), "total": total}))
    return {"report_date": report_ts, "sentiment_score": sentiment, "analyzed": len(reviews), "total": total}


def _http_resp(status, body):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body)}


def _extract_json(text):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {"error": "no_json_in_response", "raw": text[:500]}
    return json.loads(text[start : end + 1])
