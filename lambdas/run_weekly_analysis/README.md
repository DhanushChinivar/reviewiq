# runWeeklyAnalysis Lambda (the AI brain)

Reads reviews from `reviewiq-reviews`, sends them to **Amazon Bedrock (Claude
Sonnet 4.6)**, and asks for a structured intelligence report — sentiment,
themes (severity + priority + recommended actions), top praises, anomalies,
per-product breakdown, confidence. Saves the full report to S3 and a summary
row to `reviewiq-reports`.

Built **by hand** (via CLI) in Phase 3. MVP scope: analyses all reviews, one
report per `user_id`. Later: filter to last 7 days, trigger weekly via
EventBridge, compare vs previous week for trends.

## Deploy config (as built)

| Setting | Value |
|---|---|
| Function name | `reviewiq-run-weekly-analysis` |
| Runtime | `python3.13` · arm64 |
| Handler | `lambda_function.handler` |
| Timeout | **120s** (Bedrock calls exceed the 3s default) |
| Memory | 256 MB |
| Env vars | `REVIEWS_TABLE=reviewiq-reviews`, `REPORTS_TABLE=reviewiq-reports`, `DATA_BUCKET=reviewiq-data`, `MODEL_ID=us.anthropic.claude-sonnet-4-6` |

## Bedrock model

- **Claude Sonnet 4.6** via the cross-region inference profile
  `us.anthropic.claude-sonnet-4-6` (bare/foundation-model IDs error — must use
  the profile). Called with the `bedrock-runtime` **Converse** API.
- **Why Sonnet 4.6 not Sonnet 5:** Sonnet 5 isn't available to this (new)
  account yet. Same Sonnet tier + cost. To switch later, just change the
  `MODEL_ID` env var — no code change.
- **No Knowledge Base / OpenSearch** — OpenSearch Serverless has a ~$350/mo
  always-on floor. Product context (if needed) goes into the prompt directly.

## IAM (role `reviewiq-run-weekly-analysis-role`, inline `run-weekly-analysis-permissions`)

See [`iam-policy.json`](./iam-policy.json): `bedrock:InvokeModel` on the Sonnet 4.6
inference profile + its 3 regional foundation-model ARNs (cross-region inference
needs all of them) + `dynamodb:Scan` (reviews) + `dynamodb:PutItem` (reports) +
`s3:PutObject` (data bucket). Plus managed `AWSLambdaBasicExecutionRole`.

## Redeploy the code by hand

```bash
cd lambdas/run_weekly_analysis
zip -q function.zip lambda_function.py
aws lambda update-function-code \
  --function-name reviewiq-run-weekly-analysis \
  --zip-file fileb://function.zip --region us-east-1
```
