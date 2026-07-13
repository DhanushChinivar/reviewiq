"""reviewiq — shopifyOAuth Lambda.

Handles GET /shopify/callback: exchanges the OAuth `code` for a Shopify access
token, KMS-encrypts that token, and stores the ciphertext in the
reviewiq-shopify-tokens table. The plaintext token is never stored or logged.

SCOPE: the real Shopify code-for-token exchange needs a registered Shopify
Partner app; for now the token is simulated. The AWS mechanics (KMS + storage)
are real.
"""

import base64
import json
import logging
import os
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

kms = boto3.client("kms")
dynamodb = boto3.resource("dynamodb")
tokens_table = dynamodb.Table(os.environ["TOKENS_TABLE"])
KMS_KEY_ID = os.environ["KMS_KEY_ID"]


def handler(event, context):
    params = event.get("queryStringParameters") or {}
    shop = params.get("shop")
    code = params.get("code")
    if not shop or not code:
        return _resp(400, {"error": "missing shop or code"})

    # NOTE: a real Shopify app would exchange `code` for a token here.
    # We simulate the access token for now (no Shopify app registered yet).
    access_token = f"simulated-access-token-for-{code}"

    # Encrypt the secret token with KMS before storing it.
    blob = kms.encrypt(KeyId=KMS_KEY_ID, Plaintext=access_token.encode())["CiphertextBlob"]
    encrypted_token = base64.b64encode(blob).decode()

    tokens_table.put_item(
        Item={
            "store_id": shop,
            "shop_domain": shop,
            "encrypted_token": encrypted_token,
            "scopes": "read_products,read_orders",
            "connected_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    logger.info(json.dumps({"event": "shopify_connected", "shop": shop}))
    return _resp(200, {"status": "connected", "shop": shop})


def _resp(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body),
    }
