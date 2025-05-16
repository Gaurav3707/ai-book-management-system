
# import os, sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import pytest
# from httpx import AsyncClient
# from main import app
# from app.models.database import init_db

# @pytest.fixture(scope="module", autouse=True)
# async def setup_database():
#     await init_db()
#     yield

# @pytest.fixture
# async def client():
#     async with AsyncClient(app=app, base_url="http://testserver") as ac:
#         yield ac

# @pytest.mark.asyncio
# async def test_register_user(client):
#     response = await client.post(
#         "/auth/register",
#         json={
#             "username": "testuser",
#             "email": "testuser@example.com",
#             "password": "password123"
#         }
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "User registered successfully"

# @pytest.mark.asyncio
# async def test_login_user(client):
#     response = await client.post(
#         "/auth/login",
#         json={
#             "username": "testuser",
#             "password": "password123"
#         }
#     )
#     assert response.status_code == 200
#     assert "access_token" in response.json()

# @pytest.mark.asyncio
# async def test_get_profile(client):
#     response = await client.get("/auth/profile", headers={"Authorization": "Bearer test_token"})
#     assert response.status_code == 200
#     assert "username" in response.json()
