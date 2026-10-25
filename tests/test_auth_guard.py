import pytest
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from config.environment import JWT_SECRET_KEY, JWT_ALGORITHM
from dependencies.auth_guard import get_current_user_from_token, TokenUser

def make_token(user_id=1, email="test@heartsense.com", token_type="access", expired=False, secret=JWT_SECRET_KEY):
    exp_delta = timedelta(seconds=-60 if expired else 3600)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": token_type,
        "exp": datetime.now(timezone.utc) + exp_delta
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)

def test_auth_guard_accepts_valid_token():
    token = make_token(user_id=10, email="user10@heartsense.com")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = get_current_user_from_token(creds)
    assert isinstance(user, TokenUser)
    assert user.user_id == 10
    assert user.email == "user10@heartsense.com"

def test_auth_guard_rejects_missing_credentials():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_token(None)
    assert exc_info.value.status_code == 401

def test_auth_guard_rejects_expired_token():
    token = make_token(expired=True)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_token(creds)
    assert exc_info.value.status_code == 401

def test_auth_guard_rejects_wrong_secret():
    token = make_token(secret="wrong-secret-key-that-does-not-match-32b")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_token(creds)
    assert exc_info.value.status_code == 401

def test_auth_guard_rejects_refresh_token_type():
    token = make_token(token_type="refresh")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_token(creds)
    assert exc_info.value.status_code == 401

def test_auth_guard_rejects_tampered_payload():
    token = make_token()
    tampered = token[:-4] + "abcd"
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=tampered)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_token(creds)
    assert exc_info.value.status_code == 401
