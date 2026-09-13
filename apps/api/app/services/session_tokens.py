import uuid
from datetime import UTC, datetime, timedelta

import jwt

SIGNING_ALGORITHM = "HS256"


def sign_session_token(user_id: uuid.UUID, secret: str, ttl_days: int) -> str:
    issued_at = datetime.now(UTC)
    claims = {"sub": str(user_id), "iat": issued_at, "exp": issued_at + timedelta(days=ttl_days)}
    return jwt.encode(claims, secret, algorithm=SIGNING_ALGORITHM)


def read_session_user_id(token: str, secret: str) -> uuid.UUID | None:
    try:
        claims = jwt.decode(token, secret, algorithms=[SIGNING_ALGORITHM])
        return uuid.UUID(str(claims["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
