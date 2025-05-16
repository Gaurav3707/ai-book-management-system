import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from main import app
from app.models.database import init_db

valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbUdhdXJhdiIsInJvbGUiOiJ1c2VyIiwidXNlcl9pZCI6MSwiZW1haWwiOiJnYXVyYXZAeW9wbWFpbC5jb20iLCJleHAiOjE3NDczNzQ4MzB9.bx7O_zH8ZMYxQlTDY-N4Cn_uiYwlvjdX7Kug9YtNvIU"  # Replace with the actual valid token used in your app


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    import asyncio
    from unittest.mock import AsyncMock

    # Mock the init_db function to avoid asynchronous issues during testing
    mock_init_db = AsyncMock()
    asyncio.run(mock_init_db())
    yield

@pytest.fixture
def client():
    with TestClient(app) as tc:
        yield tc

def test_create_book(client):
    response = client.post(
        "/api/books/",
        json={
            "title": "Test Book",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2023,
            "summary": "A test book summary."
        },
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Book"

def test_list_books(client):
    response = client.get("/api/books/", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_book(client):
    response = client.get("/api/books/1", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert response.json()["id"] == 1

def test_update_book(client):
    response = client.put(
        "/api/books/1",
        json={
            "title": "Updated Test Book",
            "author": "Updated Author",
            "genre": "Non-Fiction",
            "year_published": 2024,
            "summary": "Updated summary."
        },
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Test Book"

def test_delete_book(client):
    response = client.delete("/api/books/1", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 204

def test_add_review(client):
    response = client.post(
        "/api/books/1/reviews",
        json={"review_text": "Great book!", "rating": 5},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 201
    assert response.json()["rating"] == 5

def test_get_reviews(client):
    response = client.get("/api/books/1/reviews", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_book_summary(client):
    response = client.get("/api/books/1/summary", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert "average_rating" in response.json()

def test_generate_summary(client):
    response = client.post(
        "/api/books/generate-summary",
        json={"content": "This is a test content."},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert "summary" in response.json()

def test_generate_summary_by_book_id(client):
    response = client.post(
        "/api/books/generate-summary-by-book-id/1",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert "summary" in response.json()

def test_generate_summary_by_book_name(client):
    response = client.post(
        "/api/books/generate-summary-by-book-name/Test Book",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert "summary" in response.json()
