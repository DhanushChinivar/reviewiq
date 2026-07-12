"""reviewiq — ingestReviews Lambda (producer).

Receives a review-upload request from API Gateway (POST /reviews/upload),
drops a job onto the reviewiq-ingest SQS queue, and returns a job_id
immediately. The sqs_worker Lambda consumes the queue and does the heavy
CSV/Excel parsing asynchronously — this keeps the upload response fast
(the decoupling pattern SQS is here for).
"""

import json
import logging
import os
import uuid

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

sqs = boto3.client("sqs")
QUEUE_URL = os.environ["INGEST_QUEUE_URL"]


def handler(event, context):
    body = json.loads(event.get("body") or "{}")

    job_id = str(uuid.uuid4())
    message = {
        "job_id": job_id,
        "user_id": body.get("user_id"),
        "s3_key": body.get("s3_key"),  # where the uploaded file sits in S3
    }

    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))
    logger.info(json.dumps({"event": "review_job_queued", "job_id": job_id}))

    return {
        "statusCode": 202,
        "headers": {
            "Content-Type": "application/json",
            # CORS: allow the future Next.js frontend to call this from the browser.
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"job_id": job_id, "status": "queued"}),
    }
