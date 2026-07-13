"""reviewiq — shopifyPull Lambda.

Triggered on a schedule by EventBridge. Scans the reviewiq-shopify-tokens table,
KMS-decrypts each store's token, pulls that store's reviews, and writes them to
S3 (raw payload) + the reviewiq-reviews table (source="shopify").

SCOPE: the real Judge.me API call needs a real token/account; the pull is
simulated for now. The AWS mechanics (EventBridge trigger, KMS decrypt, storage)
are real.
"""

import base64
import json
import logging
import os
import uuid
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

kms = boto3.client("kms")
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
tokens_table = dynamodb.Table(os.environ["TOKENS_TABLE"])
reviews_table = dynamodb.Table(os.environ["REVIEWS_TABLE"])
DATA_BUCKET = os.environ["DATA_BUCKET"]


def handler(event, context):
    stores = tokens_table.scan().get("Items", [])
    total = 0
    for store in stores:
        shop = store["store_id"]

        # Decrypt the stored Shopify token (needs kms:Decrypt). Never log the token itself.
        blob = base64.b64decode(store["encrypted_token"])
        token = kms.decrypt(CiphertextBlob=blob)["Plaintext"].decode()
        logger.info(json.dumps({"event": "token_decrypted", "shop": shop}))

        # NOTE: a real integration would call the Judge.me API with `token`.
        # We simulate the pulled reviews for now (no Judge.me account yet).
        pulled = _simulate_pull(shop)

        # Save the raw payload to S3, and each review to DynamoDB.
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        s3.put_object(
            Bucket=DATA_BUCKET,
            Key=f"reviews/{shop}/{today}/shopify-pull.json",
            Body=json.dumps(pulled).encode(),
        )
        for r in pulled:
            reviews_table.put_item(
                Item={
                    "user_id": shop,
                    "review_id": str(uuid.uuid4()),
                    "product_name": r["product_name"],
                    "rating": r["rating"],
                    "review_text": r["review_text"],
                    "date": r["date"],
                    "platform": "shopify",
                    "source": "shopify",
                }
            )
            total += 1

        logger.info(json.dumps({"event": "shopify_pulled", "shop": shop, "count": len(pulled)}))

    return {"stores": len(stores), "reviews_pulled": total}


def _simulate_pull(shop):
    return [
        {"product_name": "Wireless Headphones", "rating": 5, "review_text": "Great, arrived fast!", "date": "2026-07-01"},
        {"product_name": "Phone Case", "rating": 3, "review_text": "Decent but slippery", "date": "2026-07-02"},
    ]
