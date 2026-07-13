# sendReport Lambda

Fetches a user's latest report (summary from `reviewiq-reports` + full JSON from
S3), renders an HTML intelligence email, and sends it via **Amazon SES**.

Built **by hand** (via CLI) in Phase 4. Triggered by runWeeklyAnalysis or
manually; event may include `{"user_id": "...", "recipient": "..."}`.

## SES note (important)

- SES account is in **sandbox mode** — you can only send **to/from verified
  identities**. `dhanushchinivar@gmail.com` is verified and used as both sender
  and recipient for now.
- To email real users, request **SES production access** (Phase 6 / launch task).

## Deploy config (as built)

| Setting | Value |
|---|---|
| Function name | `reviewiq-send-report` |
| Runtime | `python3.13` · arm64 |
| Handler | `lambda_function.handler` |
| Timeout | 30s · Memory 256 MB |
| Env vars | `REPORTS_TABLE=reviewiq-reports`, `DATA_BUCKET=reviewiq-data`, `SENDER_EMAIL=dhanushchinivar@gmail.com`, `DEFAULT_RECIPIENT=dhanushchinivar@gmail.com` |

## IAM (role `reviewiq-send-report-role`, inline `send-report-permissions`)

See [`iam-policy.json`](./iam-policy.json): `ses:SendEmail` on the verified
identity ARN + `dynamodb:Query` (reports) + `s3:GetObject` (data bucket). Plus
managed `AWSLambdaBasicExecutionRole`.

## Redeploy the code by hand

```bash
cd lambdas/send_report
zip -q function.zip lambda_function.py
aws lambda update-function-code \
  --function-name reviewiq-send-report \
  --zip-file fileb://function.zip --region us-east-1
```
