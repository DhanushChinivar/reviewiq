"""reviewiq — sqs_worker Lambda (consumer).

Triggered by the reviewiq-ingest SQS queue (event source mapping). For each
job message it reads the uploaded CSV from S3, parses the rows, and writes one
review record per row into the reviewiq-reviews DynamoDB table.

Return cleanly → Lambda deletes the messages from the queue automatically.
Raise → messages are retried, and after 3 failures land in the DLQ.
"""

import csv
import io
import json
import logging
import os
import uuid

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
reviews_table = dynamodb.Table(os.environ["REVIEWS_TABLE"])
DATA_BUCKET = os.environ["DATA_BUCKET"]


def handler(event, context):
    ingested = 0
    for record in event["Records"]:
        msg = json.loads(record["body"])
        job_id = msg.get("job_id")
        user_id = msg.get("user_id") or "unknown"
        s3_key = msg["s3_key"]

        # 1. Read the uploaded CSV from S3
        obj = s3.get_object(Bucket=DATA_BUCKET, Key=s3_key)
        content = obj["Body"].read().decode("utf-8")

        # 2. Parse each row into a review record
        for row in csv.DictReader(io.StringIO(content)):
            reviews_table.put_item(
                Item={
                    "user_id": user_id,
                    "review_id": str(uuid.uuid4()),
                    "product_id": row.get("product_id"),
                    "product_name": row.get("product_name"),
                    "rating": int(row["rating"]) if row.get("rating") else None,
                    "review_text": row.get("review_text"),
                    "date": row.get("date"),
                    "platform": row.get("platform"),
                    "source": "csv",
                    "job_id": job_id,
                }
            )
            ingested += 1

        logger.info(json.dumps({"event": "csv_ingested", "job_id": job_id, "reviews": ingested}))

    return {"reviews_ingested": ingested}
