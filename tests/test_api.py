import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
from unittest.mock import patch

# Use a separate test database
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override the real database with the test database
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def reset_database():
    # Wipe and recreate tables before every test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

# --- Helper functions ---

def register_and_login(username="testuser", password="testpass123"):
    client.post("/auth/register", json={
        "username": username,
        "password": password
    })
    response = client.post("/auth/login", json={
        "username": username,
        "password": password
    })
    return response.json()["access_token"]

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

# --- Auth tests ---

def test_register_success():
    response = client.post("/auth/register", json={
        "username": "newuser",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data
    assert "hashed_password" not in data

def test_register_duplicate_username():
    client.post("/auth/register", json={
        "username": "duplicate",
        "password": "password123"
    })
    response = client.post("/auth/register", json={
        "username": "duplicate",
        "password": "different123"
    })
    assert response.status_code == 400

def test_login_success():
    client.post("/auth/register", json={
        "username": "loginuser",
        "password": "password123"
    })
    response = client.post("/auth/login", json={
        "username": "loginuser",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password():
    client.post("/auth/register", json={
        "username": "loginuser",
        "password": "password123"
    })
    response = client.post("/auth/login", json={
        "username": "loginuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

# --- Document tests ---

def test_create_document():
    token = register_and_login()
    response = client.post("/documents", 
        json={"title": "Test Doc", "content": "Test content"},
        headers=auth_headers(token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Doc"
    assert data["content"] == "Test content"

def test_create_document_requires_auth():
    response = client.post("/documents",
        json={"title": "Test Doc", "content": "Test content"}
    )
    assert response.status_code == 401

def test_get_document():
    token = register_and_login()
    create_response = client.post("/documents",
        json={"title": "Test Doc", "content": "Test content"},
        headers=auth_headers(token)
    )
    doc_id = create_response.json()["id"]
    response = client.get(f"/documents/{doc_id}",
        headers=auth_headers(token)
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Test Doc"

def test_cannot_access_other_users_document():
    token1 = register_and_login("user1", "password123")
    token2 = register_and_login("user2", "password456")

    create_response = client.post("/documents",
        json={"title": "Private Doc", "content": "Secret content"},
        headers=auth_headers(token1)
    )
    doc_id = create_response.json()["id"]

    response = client.get(f"/documents/{doc_id}",
        headers=auth_headers(token2)
    )
    assert response.status_code == 404

def test_list_documents_only_returns_own():
    token1 = register_and_login("user1", "password123")
    token2 = register_and_login("user2", "password456")

    client.post("/documents",
        json={"title": "User1 Doc", "content": "Content"},
        headers=auth_headers(token1)
    )
    client.post("/documents",
        json={"title": "User2 Doc", "content": "Content"},
        headers=auth_headers(token2)
    )

    response = client.get("/documents",
        headers=auth_headers(token1)
    )
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["title"] == "User1 Doc"

def test_ask_question_returns_answer():
    token = register_and_login()
    
    # Create a document first
    create_response = client.post("/documents",
        json={
            "title": "Test Doc", 
            "content": "The sky is blue."
        },
        headers=auth_headers(token)
    )
    doc_id = create_response.json()["id"]

    # Mock the Anthropic API call so we don't spend tokens
    with patch("ai.client.messages.create") as mock_create:
        mock_create.return_value.content = [
            type("Block", (), {
                "text": "ANSWER:\nThe sky is blue.\n\nSOURCES:\n\"The sky is blue.\""
            })()
        ]

        response = client.post(f"/documents/{doc_id}/ask",
            json={"question": "What color is the sky?"},
            headers=auth_headers(token)
        )

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What color is the sky?"
    assert "answer" in data

# Test if a document is too big for the server to handle
def test_document_content_too_long_rejected():
    token = register_and_login()
    long_content = "x" * 50001  # one over the limit
    response = client.post("/documents",
        json={"title": "Too Long", "content": long_content},
        headers=auth_headers(token)
    )
    assert response.status_code == 422

# Test if a password is too short to be secure
def test_short_password_rejected():
    response = client.post("/auth/register", json={
        "username": "shortpassuser",
        "password": "short"
    })
    assert response.status_code == 422