"""Integration tests for service catalog CRUD endpoints."""
import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.conftest import make_auth_header


@pytest.mark.asyncio
class TestServiceCatalog:
    """Tests for /api/v1/services endpoints."""

    async def _register_barber(self, client: AsyncClient) -> dict:
        """Register a barber and return auth headers + user data."""
        resp = await client.post("/api/v1/auth/register", json={
            "email": "barber_svc@example.com",
            "full_name": "Barber Svc",
            "role": "barber",
            "password": "securepass123",
        })
        user = resp.json()
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "barber_svc@example.com", "password": "securepass123"},
        )
        token = login_resp.json()["access_token"]
        return {"headers": {"Authorization": f"Bearer {token}"}, "user": user}

    async def test_create_service(self, client: AsyncClient):
        barber = await self._register_barber(client)
        payload = {
            "name": "Haircut",
            "description": "Standard haircut",
            "duration_minutes": 30,
            "price": 25.0,
        }
        resp = await client.post(
            "/api/v1/services", json=payload, headers=barber["headers"]
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Haircut"
        assert data["duration_minutes"] == 30

    async def test_list_services(self, client: AsyncClient):
        barber = await self._register_barber(client)
        await client.post("/api/v1/services", json={
            "name": "Beard Trim",
            "duration_minutes": 15,
            "price": 15.0,
        }, headers=barber["headers"])

        resp = await client.get("/api/v1/services")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_get_service_by_id(self, client: AsyncClient):
        barber = await self._register_barber(client)
        create_resp = await client.post("/api/v1/services", json={
            "name": "Shave",
            "duration_minutes": 20,
            "price": 20.0,
        }, headers=barber["headers"])
        service_id = create_resp.json()["id"]

        resp = await client.get(f"/api/v1/services/{service_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Shave"

    async def test_update_service(self, client: AsyncClient):
        barber = await self._register_barber(client)
        create_resp = await client.post("/api/v1/services", json={
            "name": "Facial",
            "duration_minutes": 45,
            "price": 40.0,
        }, headers=barber["headers"])
        service_id = create_resp.json()["id"]

        resp = await client.put(
            f"/api/v1/services/{service_id}",
            json={"price": 50.0},
            headers=barber["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["price"] == 50.0

    async def test_delete_service(self, client: AsyncClient):
        barber = await self._register_barber(client)
        create_resp = await client.post("/api/v1/services", json={
            "name": "Wax",
            "duration_minutes": 30,
            "price": 35.0,
        }, headers=barber["headers"])
        service_id = create_resp.json()["id"]

        resp = await client.delete(
            f"/api/v1/services/{service_id}", headers=barber["headers"]
        )
        assert resp.status_code == 204

    async def test_client_cannot_create_service(self, client: AsyncClient):
        # Register as client
        await client.post("/api/v1/auth/register", json={
            "email": "client_svc@example.com",
            "full_name": "Client Svc",
            "role": "client",
            "password": "securepass123",
        })
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "client_svc@example.com", "password": "securepass123"},
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post("/api/v1/services", json={
            "name": "Nope",
            "duration_minutes": 30,
            "price": 10.0,
        }, headers=headers)
        assert resp.status_code == 403
