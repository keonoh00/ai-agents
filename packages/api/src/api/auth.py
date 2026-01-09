from typing import Optional

from fastapi import Header, HTTPException, status

from .config import MASTER_API_KEY


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "message": "You must provide an API key using the Authorization: Bearer <key> header.",
                    "type": "invalid_request_error",
                    "param": None,
                    "code": "invalid_api_key",
                }
            },
        )
    return authorization.split(" ", 1)[1].strip()


def require_valid_api_key(authorization: Optional[str] = Header(None)) -> str:
    token = _extract_bearer_token(authorization)
    if token == MASTER_API_KEY:
        return token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "message": "Incorrect API key provided.",
                "type": "invalid_api_key",
                "param": None,
                "code": "invalid_api_key",
            }
        },
    )
