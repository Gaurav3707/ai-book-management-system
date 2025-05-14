import pytest
from httpx import AsyncClient
from app.main import app
from app.models.database import async_session
from app.models.book import Book, Review

@pytest.fixture
async def setup_test_db():
    async with async_session() as session:
        # Add test data
        book = Book(title="Test Book", author="Test Author", genre="Fiction", year_published=2021, summary="Test Summary")
        session.add(book)
        await session.commit()
        await session.refresh(book)
        yield book
        # Cleanup
        await session.delete(book)
        await session.commit()

@pytest.mark.asyncio
async def test_create_book():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/books/",
            json={
                "title": "New Book",
                "author": "New Author",
                "genre": "Fiction",
                "year_published": 2022,
                "summary": "New Summary"
            }
        )
        assert response.status_code == 201
        assert response.json()["title"] == "New Book"

@pytest.mark.asyncio
async def test_list_books(setup_test_db):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/books/")
        assert response.status_code == 200
        assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_get_book(setup_test_db):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/books/{setup_test_db.id}")
        assert response.status_code == 200
        assert response.json()["title"] == setup_test_db.title

@pytest.mark.asyncio
async def test_update_book(setup_test_db):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(
            f"/books/{setup_test_db.id}",
            json={
                "title": "Updated Book",
                "author": "Updated Author",
                "genre": "Non-Fiction",
                "year_published": 2023,
                "summary": "Updated Summary"
            }
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Book"

@pytest.mark.asyncio
async def test_delete_book(setup_test_db):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(f"/books/{setup_test_db.id}")
        assert response.status_code == 204

@pytest.mark.asyncio
async def test_add_review(setup_test_db):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            f"/books/{setup_test_db.id}/reviews",
            json={"review_text": "Great book!", "rating": 5}
        )
        assert response.status_code == 201
        assert response.json()["review_text"] == "Great book!"

@pytest.mark.asyncio
async def test_get_reviews(setup_test_db):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/books/{setup_test_db.id}/reviews")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_book_summary(setup_test_db):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/books/{setup_test_db.id}/summary")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_recommendations():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/books/recommendations")
        assert response.status_code == 200
