import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pytest_asyncio
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from main import app
from app.models.database import get_db  # Import get_db for dependency override
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.book import Base


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

created_book_id = None
valid_token = None

@pytest.mark.asyncio
async def test_user_onboarding(client):
    global valid_token  # Declare the global variable
    response = await client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User registered successfully"

    response = await client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    valid_token = response.json()["access_token"]  # Store the token
#=============================

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
    print(f"Created book ID: {created_book_id}")  # Debug statement

@pytest.mark.asyncio
async def test_list_books(client):
    response = await client.get("/api/books/", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_book(client):
    global created_book_id  # Use the shared variable
    response = await client.get(f"/api/books/{created_book_id}", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert response.json()["id"] == created_book_id

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
    assert created_book_id is not None, "Book ID is not set. Ensure test_create_book runs first."
    response = await client.post(
        f"/api/books/{created_book_id}/reviews",  # Use the created book's ID
        json={"review_text": "Great book!", "rating": 5},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 201
    assert response.json()["rating"] == 5

@pytest.mark.asyncio
async def test_get_reviews(client):
    assert created_book_id is not None, "Book ID is not set. Ensure test_create_book runs first."
    response = await client.get(f"/api/books/{created_book_id}/reviews", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_book_summary(client):
    global created_book_id  # Use the shared variable
    if created_book_id is None:  # Ensure a book exists
        response = await client.post(
            "/api/books/",
            json={
                "title": "Test Book for Summary",
                "author": "Test Author",
                "genre": "Fiction",
                "year_published": 2023,
                "summary": "A test book summary for summary endpoint."
            },
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code == 201
        created_book_id = response.json()["id"]

    response = await client.get(f"/api/books/{created_book_id}/summary", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert "average_rating" in response.json()

@pytest.mark.asyncio
async def test_generate_summary(client):
    test_content="In today’s digital landscape, chatbots are becoming increasingly prevalent, serving as virtual assistants and conversation partners. However, a key challenge lies in crafting chatbots that can understand and respond to user queries in a context-aware manner, simulating natural conversation flow. This article delves into building a context-aware chatbot using LangChain, a powerful open-source framework, and Chat Model, a versatile tool for interacting with various language models."

    response = await client.post(
        "/api/books/generate-summary",
        json={"content": test_content},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert "summary" in response.json()

@pytest.mark.asyncio
async def test_generate_summary_by_book_id(client):
    response = await client.post(
        f"/api/books/generate-summary-by-book-id/{created_book_id}",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert "summary" in response.json()

@pytest.mark.asyncio
async def test_generate_summary_by_book_name(client):
    response = await client.get(
        "/api/books/generate-summary-by-book-name/Harry Potter",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert "summary" in response.json()
