# AI Product Review Intelligence Agent — Project Plan

> Stack: Python · AWS Lambda · Amazon Bedrock · Next.js · DynamoDB · S3 · SES · EventBridge · API Gateway · CloudFront · OpenSearch Serverless · SQS

---

## Purpose

E-commerce sellers receive hundreds of reviews across platforms every week but have no time to read them all. This agent reads every review automatically, finds patterns using AI, and emails a weekly intelligence report — so sellers know exactly what to fix and what's working, without lifting a finger.

---

## Data Sources — How Reviews Get In

Users connect one or more of the following. All are valid. Reviews from all connected sources are merged before analysis.

```
Option 1: Shopify (recommended)
  └── OAuth connect → Shopify Admin API
      → pulls reviews automatically on schedule
      → no manual work from seller ever again

Option 2: CSV / Excel Upload (fallback)
  └── Seller uploads file manually
      → supports .csv and .xlsx
      → column mapping UI so any format works

Option 3: Both
  └── Shopify pulls automatically
      CSV fills gaps for platforms not on Shopify
```

No seller should have to manually upload a CSV every week forever. Shopify connection is the primary path. CSV is the fallback for sellers not on Shopify or for importing historical data.

---

## The User Journey

**One-time setup:**
- Seller signs up (Clerk auth)
- Connects Shopify store via OAuth OR uploads CSV/Excel
- Uploads product catalogue to Knowledge Base
- Sets email preferences

**Every week automatically:**
- Agent pulls new reviews from Shopify API (if connected)
- Merges with any manually uploaded reviews
- Bedrock analyses sentiment, themes, urgency, trends
- Generates structured intelligence report
- SES emails report every Monday 7am

**Seller receives:**
- Overall sentiment score
- Top complaints with severity + priority scoring
- Top praises
- Week-over-week trend (e.g. battery complaints up 200%)
- AI-suggested actions per theme
- Product breakdown table
- Anomalies detected

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│           Next.js Frontend              │
│  ├── Dashboard (BI-style)               │
│  │   ├── KPI cards                      │
│  │   ├── Weekly sentiment trend         │
│  │   ├── Product comparison table       │
│  │   ├── Complaint heatmap              │
│  │   ├── AI recommendations panel       │
│  │   └── Export options                 │
│  ├── Onboarding (/connect)              │
│  │   ├── Connect Shopify (OAuth)        │
│  │   └── Upload CSV / Excel             │
│  ├── Reports history (/reports)         │
│  └── Settings (/settings)              │
│  Hosted on S3 + CloudFront              │
└──────────────┬──────────────────────────┘
               │ HTTPS (JWT via Clerk)
┌──────────────▼──────────────────────────┐
│         API Gateway (REST)              │
│  ├── POST /reviews/upload               │
│  ├── POST /shopify/connect              │
│  ├── GET  /shopify/callback             │
│  ├── POST /subscribe                    │
│  ├── GET  /reports                      │
│  ├── POST /reports/generate             │
│  └── DELETE /reviews                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Lambda Functions                │
│  ├── ingestReviews (CSV/Excel)          │
│  ├── shopifyOAuth                       │
│  ├── shopifyPullReviews                 │
│  ├── runWeeklyAnalysis                  │
│  ├── sendReport                         │
│  ├── getReports                         │
│  └── manageSubscription                 │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│              SQS Queue                  │
│  └── Decouples upload from processing   │
│      Handles large CSV/Excel async      │
│      Dead-letter queue for failures     │
│      Worker Lambda consumes messages    │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴──────────────┐
       ▼                      ▼
┌──────────────┐    ┌──────────────────────┐
│     S3       │    │      DynamoDB        │
│  ├── reviews │    │  ├── Users           │
│  ├── reports │    │  ├── Stores          │
│  └── docs    │    │  ├── Reviews         │
└──────┬───────┘    │  ├── Reports         │
       │            │  └── ShopifyTokens   │
       │            └──────────────────────┘
┌──────▼──────────────────────────────────┐
│         Amazon Bedrock                  │
│  ├── Knowledge Base                     │
│  │   └── Product catalogue docs        │
│  │       indexed in OpenSearch          │
│  └── Claude (analysis + report)        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Amazon SES                      │
│  └── Weekly HTML report email           │
└─────────────────────────────────────────┘
               ▲
┌──────────────┴──────────────────────────┐
│         EventBridge Scheduler           │
│  ├── Every Monday 7am AEST              │
│  │   → triggers runWeeklyAnalysis       │
│  └── Every Sunday 11pm AEST            │
│      → triggers shopifyPullReviews      │
└─────────────────────────────────────────┘
```

---

## AWS Services

| Service | Role |
|---|---|
| Lambda | Serverless functions — all compute |
| S3 | Raw review storage, report archive, frontend hosting |
| DynamoDB | Users, stores, reviews metadata, Shopify tokens, reports |
| SQS | Async processing queue + dead-letter queue |
| Amazon Bedrock | Claude for analysis + Knowledge Base for RAG |
| OpenSearch Serverless | Vector store for Knowledge Base |
| EventBridge | Weekly analysis trigger + Shopify pull trigger |
| SES | HTML email delivery |
| API Gateway | REST API endpoints |
| CloudFront | CDN for Next.js frontend |
| IAM | Least-privilege roles per Lambda |
| CloudWatch | Structured JSON logs + alarms |
| ACM | SSL certificate (optional custom domain) |

---

## Shopify Integration

### OAuth Flow
```
1. Seller clicks "Connect Shopify"
2. Enters their Shopify store URL
3. Redirected to Shopify OAuth consent screen
4. Shopify redirects back to /shopify/callback
5. Lambda exchanges code for access token
6. Token stored encrypted in DynamoDB ShopifyTokens table
7. Confirmation shown in dashboard
```

### Pulling Reviews
Shopify doesn't have a native review system — reviews come from apps like:
- **Shopify Product Reviews** (free, official)
- **Judge.me**
- **Yotpo**
- **Loox**

For MVP — use **Judge.me API** (most popular, free tier available):
```python
GET https://judge.me/api/v1/reviews
Headers: Authorization: Bearer {token}
Params:  shop_domain={store}, per_page=100, page=1
```

For sellers not using Judge.me — CSV fallback handles their reviews.

### shopifyPullReviews Lambda
- Triggered by EventBridge every Sunday 11pm AEST
- Fetches all stores with connected Shopify from DynamoDB
- For each store: calls Judge.me API, fetches last 7 days of reviews
- Stores reviews in S3 + DynamoDB
- Ready for Monday morning analysis

---

## Lambda Functions

### 1. ingestReviews
- **Triggered by:** API Gateway `POST /reviews/upload`
- **Input:** CSV or Excel file
- **Does:**
  - Validates file format + column mapping
  - Puts message on SQS queue (async)
  - Returns immediately with job ID
- **SQS Worker Lambda:**
  - Parses CSV / Excel (openpyxl for .xlsx)
  - Stores reviews in S3
  - Writes metadata to DynamoDB Reviews table
  - Handles retries via SQS visibility timeout
  - Failed messages go to dead-letter queue

### 2. shopifyOAuth
- **Triggered by:** API Gateway `GET /shopify/callback`
- **Does:**
  - Exchanges OAuth code for access token
  - Encrypts token with AWS KMS
  - Stores in DynamoDB ShopifyTokens table
  - Returns success to frontend

### 3. shopifyPullReviews
- **Triggered by:** EventBridge Sunday 11pm AEST
- **Does:**
  - Fetches all connected Shopify stores from DynamoDB
  - For each store: calls Judge.me API
  - Paginates through all new reviews since last pull
  - Stores in S3 + DynamoDB
  - Logs pull summary to CloudWatch

### 4. runWeeklyAnalysis (core agent)
- **Triggered by:** EventBridge Monday 7am AEST
- **Also triggered by:** API Gateway `POST /reports/generate` (manual)
- **Does:**
  - Fetches all users from DynamoDB
  - For each user:
    - Retrieves last 7 days reviews from S3 (Shopify + CSV merged)
    - Queries Bedrock Knowledge Base for product context
    - Sends structured prompt to Claude
    - Claude returns rich JSON report
    - Compares with last week's report for trend detection
    - Saves report to S3 + DynamoDB
    - Invokes sendReport Lambda

### 5. sendReport
- **Triggered by:** runWeeklyAnalysis or manual trigger
- **Does:**
  - Fetches report from DynamoDB
  - Renders HTML email with priority table + trend data
  - Sends via SES
  - Logs delivery status

### 6. getReports
- **Triggered by:** API Gateway `GET /reports`
- **Auth:** JWT from Clerk — user_id extracted server-side (never from query param)
- **Does:** Returns paginated report history for authenticated user

### 7. manageSubscription
- **Triggered by:** API Gateway `POST /subscribe`
- **Does:** Creates or updates user preferences in DynamoDB

---

## DynamoDB Tables

### Users
```
PK: user_id (String)
Attributes:
  email           String
  created_at      String
  preferences     Map { send_day, send_time, timezone }
  plan            String (free / pro)
```

### Stores
```
PK: user_id (String)
SK: store_id (String)
Attributes:
  store_name      String
  platform        String (shopify / csv)
  connected_at    String
  last_pull_at    String
```

### ShopifyTokens
```
PK: store_id (String)
Attributes:
  encrypted_token   String (KMS encrypted)
  shop_domain       String
  scopes            String
  connected_at      String
```

### Reviews
```
PK: user_id (String)
SK: review_id (String)
Attributes:
  product_id      String
  product_name    String
  rating          Number
  review_text     String
  platform        String
  source          String (shopify / csv)
  date            String
  ingested_at     String
```

### Reports
```
PK: user_id (String)
SK: report_date (String)
Attributes:
  s3_key              String
  sentiment_score     Number
  top_complaints      List
  top_praises         List
  suggestions         List
  anomalies           List
  trend_vs_last_week  Map
  created_at          String
```

---

## Claude Output Schema

Rich structured output — not just basic sentiment:

```json
{
  "sentiment_score": 74,
  "week_summary": "2-3 sentence plain English summary",
  "themes": [
    {
      "theme": "Battery Life",
      "mentions": 43,
      "severity": "high",
      "priority": "red",
      "trend_vs_last_week": "+200%",
      "customer_quotes": ["quote 1", "quote 2"],
      "recommended_actions": [
        "Investigate supplier batch after June 20",
        "Update product page with expected battery duration",
        "Notify support team"
      ]
    }
  ],
  "top_praises": [
    {
      "theme": "Sound Quality",
      "mentions": 38,
      "customer_quotes": ["quote 1"]
    }
  ],
  "anomalies": [
    "Battery complaints spiked 200% vs last week — possible batch issue"
  ],
  "products": [
    {
      "product_name": "Wireless Headphones",
      "sentiment_score": 68,
      "review_count": 52,
      "trend": "declining"
    }
  ],
  "confidence_score": 0.91
}
```

---

## Priority Scoring Table (Email + Dashboard)

| Theme | Mentions | Severity | Priority |
|---|---|---|---|
| Battery Life | 43 | High | 🔴 |
| Packaging | 21 | Medium | 🟡 |
| Shipping Speed | 6 | Low | 🟢 |

---

## Trend Detection

Compare current week vs last week per theme:

```
Battery complaints:
  Week 1 → 5
  Week 2 → 8
  Week 3 → 24   ← +200% anomaly flagged
```

Stored in DynamoDB Reports table under `trend_vs_last_week`.

---

## Non-Functional Requirements

### Performance
- Weekly analysis completes within 5 minutes per user
- CSV ingestion handles files up to 10,000 rows
- API Gateway response < 500ms for read endpoints

### Availability
- 99.9% uptime (Lambda + DynamoDB are serverless — inherently resilient)

### Security
- IAM least-privilege per Lambda
- Shopify tokens encrypted at rest via KMS
- HTTPS enforced via CloudFront
- JWT authentication via Clerk — user_id never accepted from client
- S3 buckets private — no public access

### Scalability
- Handle 10,000+ reviews per week per user
- SQS decouples ingestion from processing
- DynamoDB on-demand capacity — scales automatically

### Reliability
- SQS dead-letter queue for failed ingestion jobs
- Lambda retries on failure (3 attempts)
- CloudWatch alarms on Lambda error rate > 1%

### Monitoring
- Structured JSON logs across all Lambdas
- CloudWatch dashboard: invocation count, error rate, duration
- Alarm: runWeeklyAnalysis duration > 5 min

---

## Functional Requirements

- User authentication (Clerk)
- Multiple stores per user
- Connect Shopify via OAuth
- Upload CSV or Excel (fallback)
- Manual report generation (on-demand)
- Download report as PDF
- Search reports by date range
- Filter by product
- Delete uploaded reviews
- Retry failed imports
- Unsubscribe from emails

---

## S3 Bucket Structure

```
review-intelligence-bucket/
  ├── reviews/
  │   └── {user_id}/
  │       └── {store_id}/
  │           └── {YYYY-MM-DD}/
  │               └── reviews.json
  ├── reports/
  │   └── {user_id}/
  │       └── {YYYY-MM-DD}/
  │           └── report.json
  └── knowledge-base/
      └── {user_id}/
          ├── product-catalogue.pdf
          └── product-descriptions.txt
```

---

## Next.js Frontend Pages

### `/` — Dashboard (BI-style)
- KPI cards: overall sentiment, review count, products analysed, trend
- Weekly sentiment trend line chart
- Complaint priority table with severity colours
- Product comparison table
- AI recommendations panel
- Anomalies flagged this week
- Recent reports list
- Export to PDF button

### `/connect` — Store Onboarding
- Connect Shopify (OAuth button + store URL input)
- Upload CSV / Excel (drag and drop + column mapping)
- Connected stores list with status

### `/reports` — Report History
- Paginated list of past weekly reports
- Click to expand full report
- Download as PDF
- Filter by date range

### `/settings` — Preferences
- Email address + send time preference
- Product catalogue upload (for Knowledge Base)
- Manage connected stores
- Delete account / data

---

## IAM Roles (Least Privilege)

### runWeeklyAnalysis
```json
{
  "Actions": [
    "s3:GetObject", "s3:PutObject",
    "dynamodb:Scan", "dynamodb:PutItem", "dynamodb:GetItem",
    "bedrock:InvokeModel", "bedrock:Retrieve",
    "lambda:InvokeFunction",
    "logs:CreateLogGroup", "logs:PutLogEvents"
  ]
}
```

### ingestReviews
```json
{
  "Actions": [
    "sqs:SendMessage",
    "logs:CreateLogGroup", "logs:PutLogEvents"
  ]
}
```

### SQS Worker Lambda
```json
{
  "Actions": [
    "sqs:ReceiveMessage", "sqs:DeleteMessage",
    "s3:PutObject",
    "dynamodb:PutItem",
    "logs:CreateLogGroup", "logs:PutLogEvents"
  ]
}
```

### shopifyOAuth
```json
{
  "Actions": [
    "dynamodb:PutItem",
    "kms:Encrypt",
    "logs:CreateLogGroup", "logs:PutLogEvents"
  ]
}
```

---

## EventBridge Rules

```
Rule 1: WeeklyAnalysisTrigger
  Schedule: cron(0 21 ? * SUN *)   ← Monday 7am AEST = Sunday 9pm UTC
  Target: runWeeklyAnalysis Lambda

Rule 2: ShopifyPullTrigger
  Schedule: cron(0 13 ? * SUN *)   ← Sunday 11pm AEST = Sunday 1pm UTC
  Target: shopifyPullReviews Lambda
```

---

## Sample CSV Format

```csv
product_id,product_name,rating,review_text,date,platform
P001,Wireless Headphones,5,"Amazing sound quality",2026-06-01,Amazon
P001,Wireless Headphones,2,"Battery dies after 3 hours",2026-06-02,Amazon
P002,Phone Case,4,"Great protection",2026-06-01,Google
P002,Phone Case,1,"Cracked after one drop",2026-06-03,Trustpilot
```

---

## Build Phases

### Phase 1 — AWS Foundation (Week 1)
- [ ] AWS account setup + billing alerts
- [ ] S3 buckets created with correct structure
- [ ] DynamoDB tables created (all 5)
- [ ] SQS queue + dead-letter queue created
- [ ] IAM roles created per Lambda
- [ ] Basic Lambda + API Gateway hello world
- [ ] CloudWatch log groups configured
- [ ] Test with Postman

### Phase 2 — Review Ingestion (Week 2)
- [ ] ingestReviews Lambda (CSV + Excel via openpyxl)
- [ ] SQS worker Lambda (async processing)
- [ ] Shopify OAuth flow (shopifyOAuth Lambda)
- [ ] shopifyPullReviews Lambda (Judge.me API)
- [ ] EventBridge Shopify pull rule
- [ ] Full ingestion tested end-to-end

### Phase 3 — Core AI Pipeline (Week 3)
- [ ] Bedrock model access enabled (Claude 3 Sonnet)
- [ ] Knowledge Base created + S3 data source
- [ ] OpenSearch Serverless configured
- [ ] runWeeklyAnalysis Lambda complete
- [ ] Rich Claude prompt + output schema
- [ ] Trend detection vs previous week
- [ ] Anomaly detection logic
- [ ] Report saved to S3 + DynamoDB

### Phase 4 — Automation + Email (Week 4)
- [ ] SES sender verified
- [ ] sendReport Lambda with HTML priority table
- [ ] EventBridge weekly analysis rule
- [ ] Manual report generation endpoint
- [ ] Full end-to-end pipeline tested
- [ ] CloudWatch alarms configured

### Phase 5 — Frontend (Week 5)
- [ ] Next.js project scaffolded (Clerk auth)
- [ ] Dashboard with KPI cards + charts (Recharts)
- [ ] Shopify connect flow
- [ ] CSV/Excel upload with column mapping
- [ ] Reports history page
- [ ] Settings page
- [ ] S3 + CloudFront deployment
- [ ] API Gateway wired to frontend

### Phase 6 — Polish (Week 6)
- [ ] IAM policies tightened (least privilege)
- [ ] PDF export for reports
- [ ] Search + filter on reports page
- [ ] Delete reviews + retry failed imports
- [ ] Unsubscribe flow
- [ ] Sample data for demo
- [ ] Architecture diagram (Mermaid)
- [ ] README with setup guide
- [ ] Live demo recording

---

## Key Files Reference

| File | Purpose |
|---|---|
| `lambdas/ingest_reviews/lambda_function.py` | CSV/Excel parsing → SQS |
| `lambdas/sqs_worker/lambda_function.py` | Async ingestion worker |
| `lambdas/shopify_oauth/lambda_function.py` | Shopify OAuth token exchange |
| `lambdas/shopify_pull/lambda_function.py` | Judge.me API review fetcher |
| `lambdas/run_weekly_analysis/lambda_function.py` | Core Bedrock agent |
| `lambdas/send_report/lambda_function.py` | SES email delivery |
| `lambdas/get_reports/lambda_function.py` | Report history API |
| `lambdas/manage_subscription/lambda_function.py` | User management |
| `lambdas/shared/bedrock_client.py` | Bedrock helper |
| `lambdas/shared/dynamodb_client.py` | DynamoDB helper |
| `lambdas/shared/s3_client.py` | S3 helper |
| `frontend/app/page.tsx` | Dashboard |
| `frontend/app/connect/page.tsx` | Store onboarding |
| `frontend/app/reports/page.tsx` | Report history |
| `frontend/app/settings/page.tsx` | Preferences |
| `infra/iam/` | IAM policy JSON files |
| `infra/eventbridge/` | EventBridge rule JSON |
| `infra/sqs/` | SQS queue config |
| `sample-data/reviews.csv` | Sample data for demo |
| `docs/architecture.md` | Architecture diagram |
| `README.md` | Setup + deploy guide |

---

## Common Gotchas

| Problem | Fix |
|---|---|
| CloudFront shows XML | Used S3 origin instead of static website endpoint |
| Bedrock access denied | IAM missing `bedrock:InvokeModel` or model not enabled |
| SES sandbox | Verify recipient or request production access |
| EventBridge wrong time | Cron in UTC — convert AEST correctly |
| Lambda timeout | Increase to 60s+ for Bedrock calls |
| CORS errors | Handle OPTIONS in Lambda, not API Gateway |
| Shopify OAuth invalid | Redirect URI must match exactly in Shopify app settings |
| SQS message too large | Store file in S3 first, put S3 key in SQS message |
| openpyxl missing | Add to Lambda layer or zip with deployment package |

---

## Resume Line (After Building)

```
AI Product Review Intelligence Agent — AWS Bedrock
Lambda · S3 · DynamoDB · SQS · Bedrock Knowledge Base ·
OpenSearch · EventBridge · SES · API Gateway · CloudFront

◦ Built fully serverless e-commerce intelligence agent on AWS
  using Amazon Bedrock (Claude) with RAG over product catalogues,
  automatically pulling reviews from Shopify and CSV uploads,
  delivering structured weekly insight reports via SES with
  priority scoring, trend detection, and anomaly alerts.
◦ Architected async ingestion pipeline with SQS decoupling,
  Shopify OAuth integration, and Next.js dashboard deployed
  on S3 + CloudFront across 12+ AWS services.
```

---

## SAA-C03 Exam Coverage

| Domain | Weight | Services Covered |
|---|---|---|
| Design Secure Architectures | 30% | IAM, KMS, S3 policies, HTTPS, Clerk JWT |
| Design Resilient Architectures | 26% | SQS DLQ, Lambda retries, DynamoDB on-demand |
| Design High-Performing Architectures | 24% | CloudFront, SQS async, Lambda concurrency |
| Design Cost-Optimised Architectures | 20% | Serverless (pay per use), S3 lifecycle, on-demand DB |
