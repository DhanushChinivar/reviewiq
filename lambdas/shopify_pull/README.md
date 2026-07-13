# shopifyPull Lambda

Runs on a schedule (EventBridge). Scans connected stores, KMS-decrypts each
token, pulls that store's reviews, and writes them to S3 + `reviewiq-reviews`
(`source="shopify"`).

Built **by hand** in Phase 2. **SCOPE:** the Judge.me API pull is currently
*simulated* (no Judge.me account). EventBridge trigger + KMS decrypt + storage
are real.

## Deploy config (as built)

| Setting | Value |
|---|---|
| Function name | `reviewiq-shopify-pull` |
| Runtime | `python3.13` · arm64 |
| Handler | `lambda_function.handler` |
| Env vars | `TOKENS_TABLE=reviewiq-shopify-tokens`, `REVIEWS_TABLE=reviewiq-reviews`, `DATA_BUCKET=reviewiq-data` |

## Trigger (EventBridge scheduled rule)

- Rule `reviewiq-shopify-pull`, schedule `cron(0 13 ? * SUN *)`
  (Sunday 1pm UTC = Sunday 11pm AEST), state ENABLED, target = this Lambda.
- EventBridge has `lambda:InvokeFunction` permission (statement `events-shopify-pull`).

## IAM (role `reviewiq-shopify-pull-role`, inline `shopify-pull-permissions`)

See [`iam-policy.json`](./iam-policy.json): `dynamodb:Scan` (tokens) + `kms:Decrypt`
(the key) + `dynamodb:PutItem` (reviews) + `s3:PutObject` (data bucket). Plus
managed `AWSLambdaBasicExecutionRole`.

## Redeploy the code by hand

```bash
cd lambdas/shopify_pull
zip -q function.zip lambda_function.py
aws lambda update-function-code \
  --function-name reviewiq-shopify-pull \
  --zip-file fileb://function.zip --region us-east-1
```
