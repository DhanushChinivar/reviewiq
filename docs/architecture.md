# reviewiq — Architecture & Build Journey

> The one-page technical mental model. For the project overview and live demo, see the
> root [`README.md`](../README.md). This document reflects the **as-built** system (created
> by hand on AWS, phase by phase — not via the `template.yaml` SAM stack, which is a reference).

---

## Data flows

**Ingestion (two paths, both land in DynamoDB + S3):**

```
CSV upload:   POST /reviews/upload → ingestReviews → SQS → sqs_worker → parse → S3 + DynamoDB
Shopify:      EventBridge (weekly) → shopifyPull → (Judge.me) → S3 + DynamoDB
Shopify auth: GET /shopify/callback → shopifyOAuth → KMS-encrypt token → DynamoDB
```

The worker writes rows via DynamoDB `BatchWriteItem` (25/call) so a 1000+ row file
finishes well inside the Lambda timeout; the SQS visibility timeout (360s) is set to
6× the worker timeout so a slow batch is never redelivered mid-flight.

**Worker reliability (production hardening):**
- **Partial batch failures** — the event source mapping has `ReportBatchItemFailures`
  enabled and the worker returns a `batchItemFailures` list, so one bad message in a
  batch of 10 is retried *alone* instead of forcing all 10 to reprocess.
- **Idempotent writes** — `review_id` is deterministic (`job_id#row`), so a retry (SQS is
  at-least-once) overwrites the same items instead of creating duplicate rows.
- **Row-level tolerance** — a single malformed CSV row is skipped and logged; only S3/DynamoDB
  errors propagate (and are therefore retried, then DLQ'd after 3 attempts).

**Analysis & delivery — one engine (`runWeeklyAnalysis`), two triggers:**

```
Weekly (automatic):
EventBridge (Mon 7am) → runWeeklyAnalysis (all users)
    → read reviews (DynamoDB)
    → Amazon Bedrock / Claude Sonnet 4.6  → structured JSON report
    → save report (S3 + DynamoDB)
    → invoke sendReport → HTML email via SES → seller inbox

On-demand ("Generate report now" button):
POST /reports/generate → generateTrigger → 202 "started" (returns in ~1.5s)
    → async invoke runWeeklyAnalysis (one user)
    → save report (S3 + DynamoDB)
Dashboard polls GET /reports until the fresh report appears.
```

*Why the trigger + polling:* the Bedrock analysis takes 30–60s but API Gateway hard-caps
a request at 29s. So the trigger returns immediately and the analysis runs as a
fire-and-forget async invoke (no 29s ceiling → it analyses **all** of a user's reviews),
while the browser polls `getReports` for the result — the same decoupling pattern SQS
gives the ingest path.

**Dashboard:**

```
CloudFront (Next.js, Clerk auth) → GET /reports → getReports → DynamoDB + S3 → JSON → charts
```

---

## As-built resource inventory (us-east-1, account 377228489522)

| Type | Resources |
|---|---|
| **Lambda** (Python 3.13, arm64) | `reviewiq-ingest-reviews`, `reviewiq-sqs-worker`, `reviewiq-shopify-oauth`, `reviewiq-shopify-pull`, `reviewiq-run-weekly-analysis`, `reviewiq-generate-trigger`, `reviewiq-send-report`, `reviewiq-get-reports`, `reviewiq-hello` |
| **DynamoDB** (on-demand) | `reviewiq-users`, `-stores`, `-shopify-tokens`, `-reviews`, `-reports` |
| **S3** | `reviewiq-data` (private, versioned, AES256), `reviewiq-frontend-dc` (private, CloudFront-only) |
| **SQS** | `reviewiq-ingest` (visibility 360s = 6× worker timeout, SSE-SQS, `ReportBatchItemFailures`) + `reviewiq-ingest-dlq` (maxReceiveCount 3, 14-day retention) |
| **API Gateway** | `reviewiq-api` — `POST /reviews/upload`, `POST /reports/generate`, `GET /reports`, `GET /shopify/callback`, `GET /hello` |
| **Bedrock** | Claude Sonnet 4.6 via inference profile `us.anthropic.claude-sonnet-4-6` |
| **KMS** | `alias/reviewiq-shopify-tokens` (encrypts Shopify tokens) |
| **SES** | Sandbox; verified sender/recipient identity |
| **EventBridge** | `reviewiq-weekly-analysis` (Mon 7am AEST), `reviewiq-shopify-pull` (Sun 11pm AEST) |
| **CloudFront** | Distribution `E2PAITDDCLJOFA` + OAC + URL-rewrite function → the frontend |
| **IAM** | One least-privilege execution role per Lambda |
| **CloudWatch + SNS** | 4 alarms → SNS `reviewiq-alerts` (email): worker errors, worker duration >50s, ingest backlog, DLQ-not-empty |

---

## Reliability & monitoring

CloudWatch alarms publish to the `reviewiq-alerts` SNS topic (email subscription).
All use `treat-missing-data = notBreaching` so idle periods don't false-alarm.

| Alarm | Metric | Fires when | Why it matters |
|---|---|---|---|
| `reviewiq-worker-errors` | Lambda `Errors` (sqs_worker) | ≥ 1 in 5 min | The consumer is failing |
| `reviewiq-worker-duration-high` | Lambda `Duration` max | > 50s (timeout is 60s) | Approaching timeout → will start DLQ'ing |
| `reviewiq-ingest-backlog` | SQS `ApproximateAgeOfOldestMessage` | > 300s | Worker not keeping up; messages piling up |
| `reviewiq-dlq-not-empty` | SQS `ApproximateNumberOfMessagesVisible` (DLQ) | > 0 | **Poison messages** — something failed 3×; investigate |

---

## Build phases (all foundation → frontend complete)

| Phase | Delivered | Status |
|---|---|---|
| **1 — Foundation** | 5 DynamoDB tables, S3 bucket, SQS + DLQ, hello Lambda + API Gateway | ✅ |
| **2 — Ingestion** | ingestReviews, sqs_worker (CSV parse), shopifyOAuth (KMS), shopifyPull + EventBridge | ✅ |
| **3 — AI pipeline** | runWeeklyAnalysis → Bedrock/Claude → structured report → S3 + DynamoDB | ✅ |
| **4 — Automation + email** | sendReport (SES HTML), EventBridge weekly cron, analysis→email chain | ✅ |
| **5 — Frontend** | Next.js dashboard (Recharts) + Clerk auth on S3 + CloudFront; getReports API | ✅ |
| **6 — Polish** | README, docs refresh, IAM audit, SES production access, extra features | 🔵 in progress |

---

## Key decisions

| Decision | Choice | Why |
|---|---|---|
| **How built** | By hand (console + CLI), phase by phase | Learning / SAA-C03 prep; `template.yaml` kept as reference only |
| **Bedrock model** | Claude Sonnet 4.6 (`us.anthropic.claude-sonnet-4-6`) | Sonnet 5 not yet available to this account; same tier + cost. Switch via `MODEL_ID` env var |
| **Knowledge Base** | **Skipped** — inject context into the prompt | OpenSearch Serverless ~$350/mo always-on floor is the one real cost trap |
| **Frontend hosting** | S3 (private) + CloudFront + OAC | Secure static hosting; bucket never public |
| **Ingestion** | SQS producer→consumer with DLQ; `BatchWriteItem`; partial-batch failures + idempotent keys | Decouple upload from processing; batch writes keep 1000+ row files fast; retries never duplicate or reprocess good messages |
| **On-demand reports** | Trigger Lambda returns `202`, analysis runs async, dashboard polls | Bedrock analysis (30–60s) exceeds API Gateway's 29s cap — so never block the request on it |
| **Secrets** | Shopify tokens KMS-encrypted at rest | Never store/log plaintext credentials |
| **IAM** | Least-privilege role per Lambda | Each function gets only the actions/resources it needs |

## Cost posture

Everything is on-demand / pay-per-use. At demo scale: roughly **$1–5/month** plus per-report
Bedrock cost — *because* OpenSearch Serverless (the KB vector store) was deliberately avoided.
A `$10/mo` billing budget (`reviewiq-monthly-cost`) alerts at 80% / 100% / forecast.
