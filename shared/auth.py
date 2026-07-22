# auth.py
#
# verifies the token

import os
import secrets
from fastapi import Request, Header, HTTPException

from loguru import logger as base_logger

logger = base_logger.bind(module="auth")

API_TOKEN = os.environ.get("API_TOKEN", "")

async def verify_token(request: Request, x_token: str = Header(...)):
    """
    veryfication of a token. executes before entering the endpoint's logic.
    """
    if not secrets.compare_digest(x_token, API_TOKEN):
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(f"auth rejected | ip {client_ip}, path: {request.url.path}")
        raise HTTPException(status_code=403, detail="forbidden")

