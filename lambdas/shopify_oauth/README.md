# shopifyOAuth Lambda

Handles `GET /shopify/callback`: takes the OAuth `code`, gets a Shopify access
token, **KMS-encrypts** it, and stores the ciphertext in `reviewiq-shopify-tokens`.
The plaintext token is never stored or logged.

Built **by hand** in Phase 2. **SCOPE:** the Shopify token is currently *simulated*
(`simulated-access-token-for-{code}`) — the real code-for-token exchange needs a
registered Shopify Partner app (external). The KMS + DynamoDB mechanics are real.

## Deploy config (as built)

| Setting | Value |
|---|---|
| Function name | `reviewiq-shopify-oauth` |
| Runtime | `python3.14` · arm64 |
| Handler | `lambda_function.handler` |
| Env vars | `TOKENS_TABLE=reviewiq-shopify-tokens`, `KMS_KEY_ID=alias/reviewiq-shopify-tokens` |
| API route | `GET /shopify/callback` (AWS_PROXY) on `reviewiq-api` |

## KMS

- Customer-managed key alias `alias/reviewiq-shopify-tokens`
  (id `fe81e30b-26a3-4469-a4b1-81ec83c6d680`), symmetric, ENCRYPT_DECRYPT.
- The Lambda gets `kms:Encrypt` via its IAM role; this works because the key's
  default policy delegates access control to account IAM policies.

## IAM (role `reviewiq-shopify-oauth-role-*`, inline `shopify-oauth-permissions`)

See [`iam-policy.json`](./iam-policy.json): `kms:Encrypt` on the key + `dynamodb:PutItem`
on the tokens table. Plus managed `AWSLambdaBasicExecutionRole`.
