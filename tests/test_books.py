import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pytest_asyncio
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from main import app
from app.config.database import get_db  # Import get_db for dependency override
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

# Define book details for creating a book
create_book_data = {
    "title": "Harry Potter",
    "author": "JK Rowling",
    "genre": "Fiction",
    "year_published": 1998,
    "summary": "A test book summary."
}

# Define book details for updating a book
update_book_data = {
    "title": "Harry Potter and the Goblet of Fire",
    "author": "Updated Author",
    "genre": "Non-Fiction",
    "year_published": 1998,
    "summary": "Updated summary."
}

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
    assert "access_token" in response.json()["data"]
    valid_token = response.json()["data"]["access_token"]  # Store the token
#=============================

@pytest.mark.asyncio
async def test_create_book(client):
    global created_book_id  # Declare the variable as global to modify it
    response = await client.post(
        "/api/books/",
        json=create_book_data,
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 201
    assert response.json()['data']["title"] == create_book_data["title"]
    created_book_id = response.json()['data']["id"]  # Store the created book's ID

@pytest.mark.asyncio
async def test_list_books(client):
    response = await client.get("/api/books/", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert isinstance(response.json()['data'], list)

@pytest.mark.asyncio
async def test_get_book(client):
    global created_book_id  # Use the shared variable
    response = await client.get(f"/api/books/{created_book_id}", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert response.json()['data']["id"] == created_book_id

@pytest.mark.asyncio
async def test_update_book(client):
    response = await client.put(
        "/api/books/1",
        json=update_book_data,
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert response.json()['data']["title"] == update_book_data["title"]


@pytest.mark.asyncio
async def test_add_review(client):
    assert created_book_id is not None, "Book ID is not set. Ensure test_create_book runs first."
    response = await client.post(
        f"/api/books/{created_book_id}/reviews",  # Use the created book's ID
        json={"review_text": "Great book!", "rating": 5},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 201
    assert response.json()['data']["rating"] == 5

@pytest.mark.asyncio
async def test_get_reviews(client):
    assert created_book_id is not None, "Book ID is not set. Ensure test_create_book runs first."
    response = await client.get(f"/api/books/{created_book_id}/reviews", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert isinstance(response.json()['data'], list)

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
        created_book_id = response.json()['data']["id"]

    response = await client.get(f"/api/books/{created_book_id}/summary", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert "average_rating" in response.json()['data']

@pytest.mark.asyncio
async def test_generate_summary(client):
    test_content="In today’s digital landscape, chatbots are becoming increasingly prevalent, serving as virtual assistants and conversation partners. However, a key challenge lies in crafting chatbots that can understand and respond to user queries in a context-aware manner, simulating natural conversation flow. This article delves into building a context-aware chatbot using LangChain, a powerful open-source framework, and Chat Model, a versatile tool for interacting with various language models."

    response = await client.post(
        "/api/books/generate-summary",
        json={"content": test_content},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert "summary" in response.json()['data']
    assert response.json()['data']["summary"] != None

@pytest.mark.asyncio
async def test_generate_summary_by_book_id(client):
    response = await client.post(
        f"/api/books/generate-summary-by-book-id/{created_book_id}",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert "summary" in response.json()['data']
    assert response.json()['data']["summary"] != None

@pytest.mark.asyncio
async def test_generate_summary_by_book_name(client):
    response = await client.get(
        "/api/books/generate-summary-by-book-name/Harry Potter",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert "summary" in response.json()['data']
    print(response.json())
    print("=============3434===============")
    assert response.json()['data']["summary"] != None


@pytest.mark.asyncio
async def test_get_recommendations(client):
    response = await client.get("/api/books/recommendations", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert isinstance(response.json()['data'], dict)
    assert "recommendations" in response.json()['data']
    assert len(response.json()['data']["recommendations"]) > 0


# ===================== EDGE CASES =====================
from app.utils.messages import bookMessages

@pytest.mark.asyncio
async def test_create_book_duplicate(client):
    response = await client.post(
        "/api/books/",
        json=update_book_data,
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.json()['message'] == bookMessages.DUPLICATE_BOOK

@pytest.mark.asyncio
async def test_create_book_invalid_input(client):
    response = await client.post(
        "/api/books/",
        json={
            "genre": "Fiction",
            "year_published": 1998,
            "summary": "A test book summary."
        },
        headers={"Authorization": f"Bearer {valid_token}"}
        
    )
    
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_book_invalid_id(client):
    response = await client.get("/api/books/9999", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.json()['message'] == bookMessages.BOOK_NOT_FOUND

@pytest.mark.asyncio
async def test_update_book_invalid_id(client):
    response = await client.put(
        "/api/books/9999",
        json=update_book_data,
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    print(response.json())
    print("=================================2323")
    assert response.json()['message'] == bookMessages.BOOK_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_book_invalid_id(client):
    response = await client.delete("/api/books/9999", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.json()['message'] == bookMessages.BOOK_NOT_FOUND

@pytest.mark.asyncio
async def test_add_review_invalid_input(client):
    response = await client.post(
        f"/api/books/{created_book_id}/reviews",
        json={"review_text": "Great book!", "rating": 6},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.json()['message'] == bookMessages.INVALID_REVIEW_INPUT

@pytest.mark.asyncio
async def test_add_review_invalid_book_id(client):
    response = await client.post(
        "/api/books/9999/reviews",
        json={"review_text": "Great book!", "rating": 5},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.json()['message'] == bookMessages.BOOK_NOT_FOUND

@pytest.mark.asyncio
async def test_generate_summary_by_book_id_invalid_id(client):
    response = await client.post(
        "/api/books/generate-summary-by-book-id/9999",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.json()['message'] == bookMessages.BOOK_NOT_FOUND

# Intentionally keeping delete book test at last to ensure the book exists
@pytest.mark.asyncio
async def test_delete_book(client):
    global created_book_id
    response = await client.delete(f"/api/books/{created_book_id}", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200