# sqs_worker Lambda

Consumer half of the ingestion pipeline. Triggered by the `reviewiq-ingest`
SQS queue (event source mapping): reads the uploaded CSV from S3, parses each
row, and writes one review per row into the `reviewiq-reviews` table.

Built **by hand** (console + CLI) in Phase 2 — this file documents the config so
it is reproducible without a SAM template.

## Deploy config (as built)

| Setting | Value |
|---|---|
| Function name | `reviewiq-sqs-worker` |
| Runtime | `python3.14` |
| Architecture | `arm64` |
| Handler | `lambda_function.handler` |
| Region | `us-east-1` |
| Env vars | `REVIEWS_TABLE=reviewiq-reviews`, `DATA_BUCKET=reviewiq-data` |

## Trigger (event source mapping)

- **Source:** SQS queue `reviewiq-ingest`, **batch size** 10.
- Lambda polls the queue automatically. On a clean return it deletes the
  processed messages; on error they retry and, after `maxReceiveCount` (3),
  move to the `reviewiq-ingest-dlq`.

## IAM (execution role `reviewiq-sqs-worker-role-*`)

- **Managed:** `AWSLambdaBasicExecutionRole` (CloudWatch Logs).
- **Inline:** `sqs-worker-permissions` — least privilege (see [`iam-policy.json`](./iam-policy.json)):
  - `sqs:ReceiveMessage` / `DeleteMessage` / `GetQueueAttributes` on the queue
  - `dynamodb:PutItem` on `reviewiq-reviews`
  - `s3:GetObject` on `reviewiq-data/*`

## Redeploy the code by hand

```bash
cd lambdas/sqs_worker
zip -q function.zip lambda_function.py
aws lambda update-function-code \
  --function-name reviewiq-sqs-worker \
  --zip-file fileb://function.zip --region us-east-1
```

## Not yet done

- Excel (`.xlsx`) parsing — needs `openpyxl` added as a Lambda layer.
