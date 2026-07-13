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

**Analysis & delivery (weekly, automatic):**

```
EventBridge (Mon 7am) → runWeeklyAnalysis
    → read a week of reviews (DynamoDB)
    → Amazon Bedrock / Claude Sonnet 4.6  → structured JSON report
    → save report (S3 + DynamoDB)
    → invoke sendReport → HTML email via SES → seller inbox
```

**Dashboard:**

```
CloudFront (Next.js, Clerk auth) → GET /reports → getReports → DynamoDB + S3 → JSON → charts
```

---

## As-built resource inventory (us-east-1, account 377228489522)

| Type | Resources |
|---|---|
| **Lambda** (Python 3.13, arm64) | `reviewiq-ingest-reviews`, `reviewiq-sqs-worker`, `reviewiq-shopify-oauth`, `reviewiq-shopify-pull`, `reviewiq-run-weekly-analysis`, `reviewiq-send-report`, `reviewiq-get-reports`, `reviewiq-hello` |
| **DynamoDB** (on-demand) | `reviewiq-users`, `-stores`, `-shopify-tokens`, `-reviews`, `-reports` |
| **S3** | `reviewiq-data` (private, versioned, AES256), `reviewiq-frontend-dc` (private, CloudFront-only) |
| **SQS** | `reviewiq-ingest` + `reviewiq-ingest-dlq` (maxReceiveCount 3) |
| **API Gateway** | `reviewiq-api` — `POST /reviews/upload`, `GET /shopify/callback`, `GET /reports`, `GET /hello` |
| **Bedrock** | Claude Sonnet 4.6 via inference profile `us.anthropic.claude-sonnet-4-6` |
| **KMS** | `alias/reviewiq-shopify-tokens` (encrypts Shopify tokens) |
| **SES** | Sandbox; verified sender/recipient identity |
| **EventBridge** | `reviewiq-weekly-analysis` (Mon 7am AEST), `reviewiq-shopify-pull` (Sun 11pm AEST) |
| **CloudFront** | Distribution `E2PAITDDCLJOFA` + OAC + URL-rewrite function → the frontend |
| **IAM** | One least-privilege execution role per Lambda |

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
| **Ingestion** | SQS producer→consumer with DLQ | Decouple upload from processing; resilient |
| **Secrets** | Shopify tokens KMS-encrypted at rest | Never store/log plaintext credentials |
| **IAM** | Least-privilege role per Lambda | Each function gets only the actions/resources it needs |

## Cost posture

Everything is on-demand / pay-per-use. At demo scale: roughly **$1–5/month** plus per-report
Bedrock cost — *because* OpenSearch Serverless (the KB vector store) was deliberately avoided.
A `$10/mo` billing budget (`reviewiq-monthly-cost`) alerts at 80% / 100% / forecast.
