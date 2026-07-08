"""reviewiq — hello-world health-check Lambda.

Its only job is to prove the API Gateway -> Lambda path works end to end.
Once this deploys and responds, we build the real functions on the same pattern.
"""

import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def handler(event, context):
    # Structured JSON logging — every real Lambda will follow this pattern so
    # CloudWatch Logs are queryable instead of a wall of print statements.
    logger.info(json.dumps({"event": "hello_invoked", "path": event.get("path")}))

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            # CORS: allow the future Next.js frontend to call this from the browser.
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(
            {
                "message": "reviewiq is alive 🎉",
                "service": "hello",
                "ok": True,
            }
        ),
    }
