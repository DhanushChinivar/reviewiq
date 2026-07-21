"""reviewiq — ingestReviews Lambda (producer).

Receives a review upload from API Gateway (POST /reviews/upload), writes the
CSV to S3, then drops a job onto the reviewiq-ingest SQS queue and returns a
job_id immediately. The sqs_worker Lambda consumes the queue and parses the
CSV into DynamoDB asynchronously — keeping the upload response fast (the
decoupling pattern SQS is here for).

Request body (JSON):
    { "user_id": "<clerk id>", "filename": "reviews.csv", "csv": "<csv text>" }

The frontend converts .xlsx to CSV in the browser, so this Lambda and the
worker only ever deal with CSV text.
"""

import json
import logging
import os
import uuid

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

sqs = boto3.client("sqs")
s3 = boto3.client("s3")
QUEUE_URL = os.environ["INGEST_QUEUE_URL"]
DATA_BUCKET = os.environ["DATA_BUCKET"]

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def _resp(status, payload):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(payload)}


def handler(event, context):
    # CORS preflight (browsers send OPTIONS before a JSON POST from another origin)
    if (event.get("httpMethod") or "").upper() == "OPTIONS":
        return _resp(200, {"ok": True})

    body = json.loads(event.get("body") or "{}")
    user_id = body.get("user_id")
    csv_text = body.get("csv")
    filename = body.get("filename") or "upload.csv"

    if not user_id or not csv_text:
        return _resp(400, {"error": "user_id and csv are required"})

    job_id = str(uuid.uuid4())
    s3_key = f"uploads/{user_id}/{job_id}.csv"

    # 1. Store the raw CSV in S3 (the worker reads it back from here)
    s3.put_object(
        Bucket=DATA_BUCKET,
        Key=s3_key,
        Body=csv_text.encode("utf-8"),
        ContentType="text/csv",
        Metadata={"original_filename": filename[:200]},
    )

    # 2. Hand the job off to SQS — the worker parses it into DynamoDB
    message = {"job_id": job_id, "user_id": user_id, "s3_key": s3_key}
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))
    logger.info(json.dumps({"event": "review_job_queued", "job_id": job_id, "s3_key": s3_key}))

    return _resp(202, {"job_id": job_id, "status": "queued"})
