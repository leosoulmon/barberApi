"""Integration tests for availability and time-off endpoints."""
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAvailability:
    """Tests for /api/v1/availability endpoints."""

    async def _register_barber(self, client: AsyncClient) -> dict:
        email = f"barber_{uuid4().hex[:6]}@test.com"
        resp = await client.post("/api/v1/auth/register", json={
            "email": email,
            "full_name": "Avail Barber",
            "role": "barber",
            "password": "securepass123",
        })
        barber = resp.json()
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "securepass123"},
        )
        token = login_resp.json()["access_token"]
        return {"user": barber, "headers": {"Authorization": f"Bearer {token}"}}

    async def test_create_availability_slot(self, client: AsyncClient):
        ctx = await self._register_barber(client)
        resp = await client.post("/api/v1/availability/slots", json={
            "barber_id": ctx["user"]["id"],
            "day_of_week": 1,
            "start_time": "09:00:00",
            "end_time": "18:00:00",
        }, headers=ctx["headers"])
        assert resp.status_code == 201
        data = resp.json()
        assert data["day_of_week"] == 1

    async def test_list_barber_availability(self, client: AsyncClient):
        ctx = await self._register_barber(client)
        await client.post("/api/v1/availability/slots", json={
            "barber_id": ctx["user"]["id"],
            "day_of_week": 2,
            "start_time": "10:00:00",
            "end_time": "17:00:00",
        }, headers=ctx["headers"])

        resp = await client.get(f"/api/v1/availability/barbers/{ctx['user']['id']}")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_update_availability_slot(self, client: AsyncClient):
        ctx = await self._register_barber(client)
        create_resp = await client.post("/api/v1/availability/slots", json={
            "barber_id": ctx["user"]["id"],
            "day_of_week": 3,
            "start_time": "08:00:00",
            "end_time": "16:00:00",
        }, headers=ctx["headers"])
        slot_id = create_resp.json()["id"]

        resp = await client.put(
            f"/api/v1/availability/slots/{slot_id}",
            json={"start_time": "09:00:00"},
            headers=ctx["headers"],
        )
        assert resp.status_code == 200

    async def test_delete_availability_slot(self, client: AsyncClient):
        ctx = await self._register_barber(client)
        create_resp = await client.post("/api/v1/availability/slots", json={
            "barber_id": ctx["user"]["id"],
            "day_of_week": 4,
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        }, headers=ctx["headers"])
        slot_id = create_resp.json()["id"]

        resp = await client.delete(
            f"/api/v1/availability/slots/{slot_id}",
            headers=ctx["headers"],
        )
        assert resp.status_code == 204

    async def test_create_time_off(self, client: AsyncClient):
        ctx = await self._register_barber(client)
        resp = await client.post("/api/v1/availability/time-off", json={
            "barber_id": ctx["user"]["id"],
            "start_datetime": "2025-07-01T09:00:00",
            "end_datetime": "2025-07-01T18:00:00",
            "reason": "Vacation",
        }, headers=ctx["headers"])
        assert resp.status_code == 201
        assert resp.json()["reason"] == "Vacation"

    async def test_check_availability(self, client: AsyncClient):
        ctx = await self._register_barber(client)
        # Create a Monday slot
        await client.post("/api/v1/availability/slots", json={
            "barber_id": ctx["user"]["id"],
            "day_of_week": 1,
            "start_time": "09:00:00",
            "end_time": "18:00:00",
        }, headers=ctx["headers"])

        resp = await client.get(
            f"/api/v1/availability/barbers/{ctx['user']['id']}/check",
            params={
                "start_time": "2025-06-16T10:00:00",
                "end_time": "2025-06-16T10:30:00",
            },
        )
        assert resp.status_code == 200
        assert "is_available" in resp.json()

    async def test_end_time_before_start_rejected(self, client: AsyncClient):
        ctx = await self._register_barber(client)
        resp = await client.post("/api/v1/availability/slots", json={
            "barber_id": ctx["user"]["id"],
            "day_of_week": 1,
            "start_time": "18:00:00",
            "end_time": "09:00:00",
        }, headers=ctx["headers"])
        assert resp.status_code == 422
