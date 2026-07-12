# ingestReviews Lambda

Producer half of the ingestion pipeline: accepts an upload request and drops a
job on the `reviewiq-ingest` SQS queue, returning a `job_id` immediately.

Built **by hand** (console/CLI) in Phase 2 — this file documents the config so it
is reproducible without a SAM template.

## Deploy config (as built)

| Setting | Value |
|---|---|
| Function name | `reviewiq-ingest-reviews` |
| Runtime | `python3.13` |
| Architecture | `arm64` |
| Handler | `lambda_function.handler` |
| Region | `us-east-1` |
| Env var | `INGEST_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/377228489522/reviewiq-ingest` |

## IAM (execution role `reviewiq-ingest-reviews-role`)

- **Trust policy:** allows `lambda.amazonaws.com` to assume the role.
- **Managed policy:** `AWSLambdaBasicExecutionRole` (CloudWatch Logs).
- **Inline policy:** `AllowSendToIngestQueue` — least-privilege `sqs:SendMessage`
  on the ingest queue only (see [`iam-policy.json`](./iam-policy.json)).

## Redeploy the code by hand

```bash
cd lambdas/ingest_reviews
zip -q function.zip lambda_function.py
aws lambda update-function-code \
  --function-name reviewiq-ingest-reviews \
  --zip-file fileb://function.zip --region us-east-1
```
