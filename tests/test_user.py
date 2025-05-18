import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.config.database import get_db
import pytest_asyncio
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from httpx import AsyncClient
from main import app
from httpx._transports.asgi import ASGITransport
from app.config.database import init_db
from app.models.book import Base
from app.utils.logger import get_logger

logger = get_logger(__name__)

@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    await init_db()
    yield

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac
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

@pytest.mark.asyncio
async def test_register_user(client):
    logger.info("Testing user registration.")
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

@pytest.mark.asyncio
async def test_login_user(client):
    logger.info("Testing user login.")
    global access_token  # Declare the global variable
    response = await client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]
    access_token = response.json()["data"]["access_token"]  # Store the token

@pytest.mark.asyncio
async def test_get_profile(client):
    logger.info("Testing get profile.")
    global access_token  # Use the global variable
    response = await client.get("/auth/profile", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert "username" in response.json()["data"]
