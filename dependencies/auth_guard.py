from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.environment import JWT_ALGORITHM, JWT_SECRET_KEY


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class TokenUser:
    user_id: int
    email: str


def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> TokenUser:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is not configured")

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise unauthorized from exc
    except jwt.InvalidTokenError as exc:
        raise unauthorized from exc

    token_type = payload.get("type")
    if token_type != "access":
        raise unauthorized

    subject = payload.get("sub")
    email = payload.get("email")

    if subject is None or email is None:
        raise unauthorized

    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise unauthorized from exc

    return TokenUser(user_id=user_id, email=email)
