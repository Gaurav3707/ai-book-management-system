import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_register_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users/register",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 201
        assert response.json()["username"] == "testuser"

@pytest.mark.asyncio
async def test_login_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users/login",
            json={
                "email": "testuser@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_get_user_profile():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Assuming token is retrieved from login
        token = "Bearer <access_token>"
        response = await client.get(
            "/users/profile",
            headers={"Authorization": token}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "testuser@example.com"
