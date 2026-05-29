import pytest
from jose import jwt
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM
)

# --- Unit tests for password hashing ---

def test_hash_password_returns_different_string():
    password = "mysecretpassword"
    hashed = hash_password(password)
    assert hashed != password

def test_hash_password_produces_valid_bcrypt_hash():
    hashed = hash_password("testpassword")
    assert hashed.startswith("$2b$")

def test_verify_password_correct():
    password = "correctpassword"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True

def test_verify_password_incorrect():
    hashed = hash_password("correctpassword")
    assert verify_password("wrongpassword", hashed) is False

def test_verify_password_empty_string():
    hashed = hash_password("somepassword")
    assert verify_password("", hashed) is False

# --- Unit tests for token creation ---

def test_create_access_token_contains_user_id():
    token = create_access_token(user_id=42, username="testuser")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "42"

def test_create_access_token_contains_username():
    token = create_access_token(user_id=1, username="tradd")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["username"] == "tradd"

def test_create_access_token_has_expiry():
    token = create_access_token(user_id=1, username="testuser")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert "exp" in payload