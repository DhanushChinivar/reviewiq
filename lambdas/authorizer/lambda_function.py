"""reviewiq — API Gateway Lambda authorizer (Clerk JWT).

Attached to the protected REST methods (GET /reports, POST /reviews/upload,
POST /reports/generate). For each request it:
  1. reads the `Authorization: Bearer <jwt>` header,
  2. verifies the Clerk session JWT — signature (RS256 against Clerk's JWKS),
     issuer, and expiry,
  3. returns an Allow policy with the verified user id in `context.user_id`.

The backend Lambdas then read `event.requestContext.authorizer.user_id` — a
value the client CANNOT forge — instead of trusting a user_id in the URL/body.
That closes the IDOR: you can only ever read/write your own data.

Invalid or missing token → raise "Unauthorized" → API Gateway returns 401.
"""

import json
import os

import jwt
from jwt import PyJWKClient

JWKS_URL = os.environ["JWKS_URL"]
ISSUER = os.environ["ISSUER"]

# Cached across warm invocations (fetches Clerk's public keys once).
_jwk_client = PyJWKClient(JWKS_URL)


def handler(event, context):
    token = _extract_token(event)
    if not token:
        raise Exception("Unauthorized")

    try:
        signing_key = _jwk_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=ISSUER,
            options={"verify_aud": False},  # Clerk session tokens have no aud
        )
    except Exception as e:  # noqa: BLE001 — any verification failure = 401
        print(json.dumps({"event": "auth_denied", "reason": str(e)[:200]}))
        raise Exception("Unauthorized")

    user_id = claims.get("sub")
    if not user_id:
        raise Exception("Unauthorized")

    return _allow(user_id, event["methodArn"])


def _extract_token(event):
    headers = event.get("headers") or {}
    auth = headers.get("Authorization") or headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return auth.strip() or None


def _allow(user_id, method_arn):
    # Wildcard resource so one cached Allow covers every method (authorizer
    # result caching keys on the token). arn:...:<apiId>/<stage>/<METHOD>/<path>
    prefix, tail = method_arn.rsplit(":", 1)
    api_id = tail.split("/")[0]
    resource = f"{prefix}:{api_id}/*/*/*"
    return {
        "principalId": user_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": "Allow",
                "Resource": resource,
            }],
        },
        "context": {"user_id": user_id},
    }
