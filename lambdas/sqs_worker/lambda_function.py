"""reviewiq — sqs_worker Lambda (consumer).

Triggered by the reviewiq-ingest SQS queue (event source mapping). For each
job message it reads the uploaded CSV from S3, parses the rows, and writes one
review record per row into the reviewiq-reviews DynamoDB table.

Reliability model:
  * Partial batch failure — the event source mapping has "ReportBatchItemFailures"
    enabled, so we return a `batchItemFailures` list. Only the messages that
    actually failed get retried; the ones that succeeded are deleted. (Without
    this, one bad message forces the whole batch of 10 to be reprocessed.)
  * Idempotency — review_id is DETERMINISTIC (job_id + row index), so if a
    message is retried the rows overwrite the same items instead of creating
    duplicates. SQS is at-least-once, so this matters.
  * Row-level tolerance — a single malformed CSV row is skipped and logged; it
    does NOT fail the whole file.
  * Retryable errors only — reading S3 or writing DynamoDB can raise; those
    propagate so the *message* is retried (and eventually DLQ'd after 3 tries).
"""

import csv
import io
import json
import logging
import os
import time

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
reviews_table = dynamodb.Table(os.environ["REVIEWS_TABLE"])
DATA_BUCKET = os.environ["DATA_BUCKET"]


def handler(event, context):
    records = event.get("Records", [])
    start = time.time()
    failures = []
    total_processed = 0

    for record in records:
        message_id = record.get("messageId")
        try:
            total_processed += _process_record(record)
        except Exception as e:  # noqa: BLE001 — any failure = retry THIS message only
            logger.error(json.dumps({
                "event": "message_failed",
                "message_id": message_id,
                "error": str(e)[:500],
            }))
            failures.append({"itemIdentifier": message_id})

    logger.info(json.dumps({
        "event": "batch_complete",
        "messages": len(records),
        "records_processed": total_processed,
        "failed_messages": len(failures),
        "duration_ms": int((time.time() - start) * 1000),
    }))
    # Shape required by ReportBatchItemFailures. Empty list = whole batch succeeded.
    return {"batchItemFailures": failures}


def _process_record(record):
    """Parse one job's CSV into DynamoDB. Raises on retryable failures (S3/DynamoDB)."""
    msg = json.loads(record["body"])
    job_id = msg.get("job_id")
    user_id = msg.get("user_id") or "unknown"
    s3_key = msg["s3_key"]

    # Read the uploaded CSV from S3 (raises → message retried).
    obj = s3.get_object(Bucket=DATA_BUCKET, Key=s3_key)
    content = obj["Body"].read().decode("utf-8")
    filename = obj.get("Metadata", {}).get("original_filename")

    processed = 0
    skipped = 0
    namespace = job_id or s3_key  # basis for the deterministic id
    with reviews_table.batch_writer() as batch:
        for i, row in enumerate(csv.DictReader(io.StringIO(content))):
            try:
                item = _row_to_item(row, user_id, job_id, namespace, i)
            except Exception as e:  # noqa: BLE001 — bad row is data, not retryable: skip it
                skipped += 1
                logger.warning(json.dumps({
                    "event": "row_skipped", "job_id": job_id, "row": i, "error": str(e)[:200],
                }))
                continue
            # Buffered; the batch flush (here or at block exit) may raise on a
            # DynamoDB error, which propagates → the message is retried.
            batch.put_item(Item=item)
            processed += 1

    logger.info(json.dumps({
        "event": "csv_ingested",
        "job_id": job_id,
        "user_id": user_id,
        "filename": filename,
        "s3_key": s3_key,
        "records_processed": processed,
        "records_skipped": skipped,
        "status": "success",
    }))
    return processed


def _row_to_item(row, user_id, job_id, namespace, i):
    return {
        "user_id": user_id,
        # Deterministic → a retry overwrites the same item instead of duplicating.
        "review_id": f"{namespace}#{i}",
        "product_id": row.get("product_id"),
        "product_name": row.get("product_name"),
        "rating": _int_or_none(row.get("rating")),
        "review_text": row.get("review_text"),
        "date": row.get("date"),
        "platform": row.get("platform"),
        "source": "csv",
        "job_id": job_id,
    }


def _int_or_none(v):
    try:
        return int(v) if v not in (None, "") else None
    except (ValueError, TypeError):
        return None
