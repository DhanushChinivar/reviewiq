# getReports Lambda

`GET /reports?user_id=...` → returns the user's **latest full report** (from S3)
plus a **history** of report summaries (from `reviewiq-reports`). Powers the
dashboard frontend.

Built **by hand** (via CLI) in Phase 5. Response shape:

```json
{ "user_id": "...", "latest": { ...full report... }, "history": [ {report_date, sentiment_score, summary, review_count}, ... ] }
```

Returns `Access-Control-Allow-Origin: *` so the browser dashboard can call it.

> ⚠️ **MVP auth gap:** `user_id` comes from the query string — insecure. Phase 6
> replaces it with the Clerk JWT (server-derived `user_id`, never client input).

## Deploy config (as built)

| Setting | Value |
|---|---|
| Function name | `reviewiq-get-reports` |
| Runtime | `python3.13` · arm64 |
| Handler | `lambda_function.handler` |
| Timeout | 15s · Memory 256 MB |
| Env vars | `REPORTS_TABLE=reviewiq-reports`, `DATA_BUCKET=reviewiq-data` |
| API route | `GET /reports` (AWS_PROXY) on `reviewiq-api` |

## IAM (role `reviewiq-get-reports-role`, inline `get-reports-permissions`)

See [`iam-policy.json`](./iam-policy.json): `dynamodb:Query` (reports) +
`s3:GetObject` (data bucket). Plus managed `AWSLambdaBasicExecutionRole`.
