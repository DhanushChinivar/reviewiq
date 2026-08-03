# Known Improvements & Issues

A living backlog of things that are **not yet done, deliberately deferred, or worth
hardening** in reviewiq. Nothing here is broken for the current demo scale — these are
the honest "next steps" and known limitations.

**Priority:** 🔴 High · 🟡 Medium · 🟢 Low   **Effort:** S (hours) · M (a day) · L (multi-day)

---

## Blocked / awaiting external action

| Item | Notes |
|---|---|
| **SES production access** | Request submitted — status `PENDING` AWS review (~24h). Until approved, email only sends to SES-*verified* addresses (sandbox). Not code — awaiting Amazon. 🔴 |

---

## Security

- **Email is captured from the client, not the verified token.** 🟡 S
  The frontend sends the Clerk email; the backend stores it keyed by the token-verified
  `user_id`. Low risk (a user can only set their *own* report recipient), but the correct
  fix is a **Clerk JWT template** that adds an `email` claim, so the authorizer captures a
  *verified* email server-side. Then drop the client-supplied email.

---

## Reliability & Operations

- **SES bounce / complaint handling is not wired.** 🔴 S
  The SES production request states we handle bounces/complaints — but there is no SES
  **event destination → SNS** yet. Wire this before real volume; repeated bounces hurt
  sending reputation and can get sending paused.
- **No on-failure destination for the async analysis.** 🟡 S
  `run_weekly_analysis` is invoked async by `generateTrigger`. The *user* sees failures via
  the job-status record, but *ops* gets no alert. Add a Lambda **on-failure destination**
  (SNS) — the async analog of the SQS DLQ, mirroring the `reviewiq-dlq-not-empty` alarm.
- **`getReports` query is single-page.** 🟢 S
  No `LastEvaluatedKey` loop. Report *summary* rows are tiny and few per user (~never hits
  1 MB), so this is theoretical — but it's the same class of bug we fixed in the analysis
  reads. Paginate for completeness.
- **Thin alarm coverage.** 🟢 S
  Alarms exist for the worker + queues. Consider adding alarms on `run_weekly_analysis`
  errors/duration, the authorizer errors, and API Gateway 4xx/5xx.

---

## Scale & Performance

- **Bedrock context ceiling (massive datasets).** 🟡 L
  Even with paginated reads, sending tens of thousands of raw reviews to Claude exceeds the
  model's context window. **Pre-aggregate** before the LLM (per-product counts, avg rating,
  a few sample review texts) and send the *summary* instead of raw rows. This is the real
  fix for "huge upload" — the current cap/prompt is a stopgap.

---

## Product / Feature completeness

- **Weekly analysis has no time window or trend comparison.** 🟡 M
  It analyses *all* reviews every run (per the MVP docstring). A real weekly report should
  filter to the **last 7 days** and compare against the **previous week** for trend/anomaly
  detection.
- **Shopify OAuth + Judge.me pull are simulated.** 🟢 L
  No registered Shopify app yet; the token exchange and review pull are stubbed. The AWS
  mechanics (KMS token encryption, EventBridge pull schedule, storage) are real.
- **Users who only upload (never generate) have no captured email.** 🟢 S
  Mostly covered now (capture on upload *and* generate), but a user who connected via a
  path that doesn't capture email would fall back to the default recipient. A Clerk webhook
  (`user.created`) populating `reviewiq-users` would make this airtight.

---

## Tech debt / Cleanup

- **Dead code: `ON_DEMAND_MAX_REVIEWS` cap.** 🟢 S
  In `run_weekly_analysis`, this cap only applied to the old *synchronous* on-demand path.
  On-demand is now async (no 29s limit), so the cap is unreachable. Remove it.
- **Dead code: `OPTIONS` handling inside Lambdas.** 🟢 S
  `ingest_reviews` / `generate_trigger` still branch on `httpMethod == OPTIONS`, but CORS
  preflight is now handled by API Gateway MOCK integrations. Harmless, but removable.
- **Test / demo data in DynamoDB.** 🟢 S
  `u123` and `test-store.myshopify.com` reviews still exist and get processed by the weekly
  cron (extra Bedrock calls + emails). Also the "real" account is loaded with IKEA *test*
  reviews. Clean up before any real launch.
- **EventBridge cron is UTC-only (timezone drift).** 🟢 S
  `cron(0 21 ? * SUN *)` = Mon 7am Sydney *only in standard time*; it won't follow daylight
  saving. Fix = migrate the rule to **EventBridge Scheduler**, which supports timezones.

---

## Docs & Infrastructure-as-Code

- **Docs are behind the implementation.** 🟡 S
  `docs/architecture.md` and `README.md` don't yet reflect: the **Clerk JWT authorizer**,
  the **`reviewiq-jobs`** table + job-status flow, per-user **email routing** + `reviewiq-users`,
  the **Scan→Query + pagination** fix, or the reliability model. Refresh so the repo matches reality.
- **Newer resources exist only in AWS, not in IaC.** 🟡 L
  The authorizer Lambda, `reviewiq-jobs`, CloudWatch alarms, SNS topic, authorizer wiring,
  and gateway-response CORS were created by hand via CLI. They are **not** in the SAM
  `template.yaml`. Reproducibility gap — a fresh deploy wouldn't recreate them. Reconcile
  the template with the as-built system (or accept it's a hand-managed learning project).

---

## Cost posture (for reference — no action needed)

Everything added this session (authorizer Lambda, `reviewiq-jobs`, alarms, SNS) is
on-demand / pay-per-use — pennies at demo scale. The one real cost trap (OpenSearch
Serverless, ~$350/mo) remains deliberately avoided. Bedrock is the main variable cost
(~$0.15–0.50 per report). A `$10/mo` budget alarm is in place.
