# CLAUDE.md — reviewiq

AI Product Review Intelligence Agent. Fully serverless AWS app that ingests e-commerce
reviews (Shopify + CSV/Excel), analyses them with Amazon Bedrock (Claude), and emails a
weekly intelligence report. Full spec: `docs/PROJECT_PLAN.md`.

## Owner context
- Owner is **new to AWS** — first cloud project. Explain AWS concepts as we go; do not
  assume familiarity with IAM, Lambda packaging, Bedrock enablement, etc.
- Prefer **step-by-step**. Manual AWS-console steps (account, billing alerts, Bedrock
  model access, SES verification) are the owner's to do — give exact click paths, then
  verify with the AWS CLI.
- Building this doubles as **SAA-C03** exam study — call out the exam-relevant reasoning
  behind architecture choices where natural.

## Repo layout (target)
```
reviewiq/
  lambdas/
    shared/            # bedrock_client, dynamodb_client, s3_client — imported by all fns
    ingest_reviews/    # POST /reviews/upload → SQS
    sqs_worker/        # async CSV/Excel parse → S3 + DynamoDB
    shopify_oauth/     # GET /shopify/callback → KMS-encrypt token → DynamoDB
    shopify_pull/      # EventBridge → Judge.me API → S3 + DynamoDB
    run_weekly_analysis/ # core agent: reviews → Bedrock → report
    send_report/       # DynamoDB report → SES HTML email
    get_reports/       # GET /reports (Clerk JWT)
    manage_subscription/ # POST /subscribe
  infra/               # IaC (see decision below) — IAM, SQS, EventBridge, tables, buckets
  frontend/            # Next.js (App Router) + Clerk + Recharts, → S3 + CloudFront
  sample-data/         # reviews.csv for demo
  docs/                # PROJECT_PLAN.md, architecture.md
  tests/               # unit tests per lambda (moto for AWS mocks)
```

## Modules (build order = plan phases)
1. **Foundation** — AWS account, billing alerts, buckets, 5 DynamoDB tables, SQS+DLQ,
   IAM roles, hello-world Lambda + API Gateway, CloudWatch.
2. **Ingestion** — ingest_reviews, sqs_worker, shopify_oauth, shopify_pull, EventBridge pull rule.
3. **AI pipeline** — Bedrock model access, Knowledge Base + OpenSearch Serverless,
   run_weekly_analysis, trend + anomaly detection.
4. **Automation + email** — SES, send_report, EventBridge weekly rule, manual generate endpoint, alarms.
5. **Frontend** — Next.js pages, deploy to S3 + CloudFront, wire to API Gateway.
6. **Polish** — tighten IAM, PDF export, search/filter, unsubscribe, README, demo.

## Decisions (locked 2026-07-08)
- **IaC tool**: **AWS SAM** — one YAML template, `sam local` for local test, `sam deploy` to ship.
- **Pace**: **mix** — teach + hands-on for AWS/infra steps (the SAA-C03 learning); Claude
  auto-writes repetitive Lambda/frontend code, owner reviews.
- **Account state**: AWS account exists but **nothing configured** — no billing alerts, no
  IAM users, no CLI. Foundation step 0 = safety rails (budget + billing alarm), non-root
  IAM admin user, then install + configure AWS CLI and SAM CLI.
- **Local tooling**: Python 3.13, Node v20, **AWS CLI 2.35 + SAM CLI 1.163 installed** (Homebrew,
  2026-07-08). `aws configure` not yet run — no credentials on this machine yet.
  Note: `brew install` needed `HOMEBREW_NO_REQUIRE_TAP_TRUST=1` due to an untrusted `mongodb/brew` tap.
- **Cost decision**: OpenSearch Serverless (Bedrock KB vector store) has a ~$350/mo always-on minimum —
  the one real cost trap. MVP plan: skip the KB and inject the product catalogue into the Claude prompt;
  add the KB later or spin it up only for demos. Bedrock model: use `anthropic.claude-sonnet-4-6`
  (not the plan's "Claude 3 Sonnet") — ~$0.15–0.25/report. Everything else is ~$1–5/mo at demo scale.

## Open decisions (resolve during Phase 1)
- **Region**: pick one with Bedrock + Claude access (e.g. `us-east-1`). AEST scheduling is
  just UTC cron math — region need not be Sydney.
- **Bedrock model**: plan says "Claude 3 Sonnet" — use the **latest available Claude on
  Bedrock** instead; confirm the exact model ID via the API/Bedrock console before wiring.
  (Check the `claude-api` skill for current model IDs.)

## Progress log
- **2026-07-08 — Phase 1 Step 0 DONE.** IAM admin user `reviewiq-admin1` created (not root);
  AWS CLI configured for region `us-east-1`, output json (creds in `~/.aws`, account 3772…9522);
  billing budget `reviewiq-monthly-cost` ($10/mo, email alerts 80/100/forecast).
- **2026-07-08 — First deploy live.** SAM stack `reviewiq` deployed (hello-world Lambda +
  API Gateway). Health check returns 200 at `.../Prod/hello`. `samconfig.toml` saved, so future
  deploys are just `sam deploy`. Next: add the 5 DynamoDB tables + S3 bucket + SQS/DLQ to template.yaml.
- **2026-07-08 — PHASE 1 COMPLETE.** Stack `reviewiq` (UPDATE_COMPLETE) now has: 5 DynamoDB tables
  (`reviewiq-users/-stores/-shopify-tokens/-reviews/-reports`, all PAY_PER_REQUEST), S3 data bucket
  `reviewiq-databucket-xsytttdtxkh7` (private, AES256, versioned), SQS `reviewiq-ingest` + DLQ
  `reviewiq-ingest-dlq` (maxReceiveCount 3), hello Lambda + API Gateway. All verified live via CLI.
  Deploys run by Claude via configured CLI (owner opted "you run it"). Per-Lambda IAM: SAM auto-creates
  execution roles; custom least-privilege deferred to Phase 6. Not committed to git yet.
  **Next: Phase 2 — review ingestion (ingestReviews → SQS → worker; Shopify OAuth; Judge.me pull).**

## Conventions
- Python 3.13 Lambdas on **arm64** (matches the owner's Apple Silicon Mac; cheaper/faster on Lambda),
  `boto3`, structured JSON logging (`logging` + json formatter).
- Each lambda: `lambda_function.py` with `handler(event, context)`; deps in `requirements.txt`.
- `shared/` packaged as a Lambda layer (or vendored) — never duplicate client code.
- Secrets/tokens: KMS-encrypted at rest, never logged. user_id always from Clerk JWT, never client input.
- Tests use `moto` to mock AWS; no real AWS calls in unit tests.

## Working agreement
- Confirm each AWS resource actually exists (CLI `describe`/`list`) before moving on — don't assume.
- Watch cost: everything on-demand/serverless; set billing alerts first. OpenSearch
  Serverless has a minimum OCU cost — flag it before enabling.
