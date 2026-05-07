"""Integration tests for authentication endpoints."""
import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRegister:
    """Tests for POST /api/v1/auth/register."""

    async def test_register_success(self, client: AsyncClient):
        payload = {
            "email": "new@example.com",
            "full_name": "New User",
            "phone": "123456",
            "role": "client",
            "password": "securepass123",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert data["role"] == "client"
        assert "id" in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {
            "email": "dup@example.com",
            "full_name": "First",
            "password": "securepass123",
        }
        await client.post("/api/v1/auth/register", json=payload)
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    async def test_register_short_password(self, client: AsyncClient):
        payload = {
            "email": "short@example.com",
            "full_name": "Short",
            "password": "12",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        payload = {
            "email": "not-an-email",
            "full_name": "Bad",
            "password": "securepass123",
        }
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    async def test_login_success(self, client: AsyncClient):
        # Register first
        await client.post("/api/v1/auth/register", json={
            "email": "login@example.com",
            "full_name": "Login User",
            "password": "securepass123",
        })
        # Login
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "login@example.com", "password": "securepass123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json={
            "email": "wrong@example.com",
            "full_name": "Wrong Pass",
            "password": "securepass123",
        })
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "wrong@example.com", "password": "wrongpass"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "ghost@example.com", "password": "anything"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestMe:
    """Tests for GET /api/v1/auth/me."""

    async def test_me_authenticated(self, client: AsyncClient):
        # Register and login
        await client.post("/api/v1/auth/register", json={
            "email": "me@example.com",
            "full_name": "Me User",
            "password": "securepass123",
        })
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "me@example.com", "password": "securepass123"},
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "me@example.com"

    async def test_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401
