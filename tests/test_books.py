import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pytest_asyncio
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from main import app
from app.models.database import init_db, get_db  # Import get_db for dependency override
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.book import Base

valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbUdhdXJhdiIsInJvbGUiOiJ1c2VyIiwidXNlcl9pZCI6MSwiZW1haWwiOiJnYXVyYXZAeW9wbWFpbC5jb20iLCJleHAiOjE3NDczODI2NjF9.9bBj2d9OuHLR0d0OE3dbxK0YcWN_jrH7Etw1lbs2YUU"  # Replace with the actual valid token used in your app

DATABASE_URL = "sqlite+aiosqlite:///:memory:"  # Use an in-memory SQLite database for testing

# Create a test database engine and session
test_engine = create_async_engine(DATABASE_URL, echo=True)
TestSessionLocal = sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_database():
    # Create tables in the test database
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Drop tables after tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session):
    # Override the get_db dependency to use the test database session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

created_book_id = None  # Shared variable to store the created book's ID

@pytest.mark.asyncio
async def test_create_book(client):
    global created_book_id  # Declare the variable as global to modify it
    response = await client.post(
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
    created_book_id = response.json()["id"]  # Store the created book's ID

@pytest.mark.asyncio
async def test_list_books(client):
    response = await client.get("/api/books/", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_book(client):
    response = await client.get("/api/books/1", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert response.json()["id"] == 1

@pytest.mark.asyncio
async def test_update_book(client):
    response = await client.put(
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

@pytest.mark.asyncio
async def test_delete_book(client):
    response = await client.delete("/api/books/1", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_add_review(client):
    global created_book_id  # Use the shared variable
    response = await client.post(
        f"/api/books/{created_book_id}/reviews",  # Use the created book's ID
        json={"review_text": "Great book!", "rating": 5},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 201
    assert response.json()["rating"] == 5

@pytest.mark.asyncio
async def test_get_reviews(client):
    response = await client.get("/api/books/1/reviews", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_book_summary(client):
    response = await client.get("/api/books/1/summary", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert "average_rating" in response.json()

@pytest.mark.asyncio
async def test_generate_summary(client):
    response = await client.post(
        "/api/books/generate-summary",
        json={"content": "This is a test content."},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert "summary" in response.json()

@pytest.mark.asyncio
async def test_generate_summary_by_book_id(client):
    response = await client.post(
        "/api/books/generate-summary-by-book-id/1",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert "summary" in response.json()

@pytest.mark.asyncio
async def test_generate_summary_by_book_name(client):
    response = await client.post(
        "/api/books/generate-summary-by-book-name/Test Book",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert "summary" in response.json()
