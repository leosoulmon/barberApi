"""Integration tests for appointment booking endpoints."""
from datetime import datetime, timedelta, time
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAppointmentBooking:
    """Tests for /api/v1/appointments endpoints."""

    async def _setup_barber_with_availability(self, client: AsyncClient) -> dict:
        """Register barber, create service, and set availability. Returns context dict."""
        # Register barber
        resp = await client.post("/api/v1/auth/register", json={
            "email": f"barber_{uuid4().hex[:6]}@test.com",
            "full_name": "Test Barber",
            "role": "barber",
            "password": "securepass123",
        })
        barber = resp.json()
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": barber["email"], "password": "securepass123"},
        )
        barber_token = login_resp.json()["access_token"]
        barber_headers = {"Authorization": f"Bearer {barber_token}"}

        # Create service
        svc_resp = await client.post("/api/v1/services", json={
            "name": "Haircut",
            "duration_minutes": 30,
            "price": 25.0,
        }, headers=barber_headers)
        service = svc_resp.json()

        # Create availability (Monday through Saturday, 9-18)
        for day in range(1, 7):
            await client.post("/api/v1/availability/slots", json={
                "barber_id": barber["id"],
                "day_of_week": day,
                "start_time": "09:00:00",
                "end_time": "18:00:00",
            }, headers=barber_headers)

        return {
            "barber": barber,
            "barber_headers": barber_headers,
            "service": service,
        }

    async def _register_client(self, client: AsyncClient) -> dict:
        """Register a client and return headers."""
        email = f"client_{uuid4().hex[:6]}@test.com"
        resp = await client.post("/api/v1/auth/register", json={
            "email": email,
            "full_name": "Test Client",
            "role": "client",
            "password": "securepass123",
        })
        cl = resp.json()
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "securepass123"},
        )
        token = login_resp.json()["access_token"]
        return {"user": cl, "headers": {"Authorization": f"Bearer {token}"}}

    def _next_weekday(self, hour: int = 10) -> str:
        """Get a future Monday at the given hour as ISO string."""
        now = datetime.utcnow()
        # Find next Monday
        days_ahead = 7 - now.weekday()  # 0=Monday
        if days_ahead <= 0:
            days_ahead += 7
        target = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
        return target.isoformat()

    async def test_book_appointment_success(self, client: AsyncClient):
        ctx = await self._setup_barber_with_availability(client)
        cl = await self._register_client(client)

        start_time = self._next_weekday(10)
        resp = await client.post("/api/v1/appointments", json={
            "barber_id": ctx["barber"]["id"],
            "service_id": ctx["service"]["id"],
            "start_time": start_time,
        }, headers=cl["headers"])
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "booked"
        assert data["barber_id"] == ctx["barber"]["id"]

    async def test_book_past_appointment_rejected(self, client: AsyncClient):
        ctx = await self._setup_barber_with_availability(client)
        cl = await self._register_client(client)

        past_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        resp = await client.post("/api/v1/appointments", json={
            "barber_id": ctx["barber"]["id"],
            "service_id": ctx["service"]["id"],
            "start_time": past_time,
        }, headers=cl["headers"])
        assert resp.status_code == 422 or resp.status_code == 400

    async def test_double_booking_rejected(self, client: AsyncClient):
        ctx = await self._setup_barber_with_availability(client)
        cl = await self._register_client(client)
        start_time = self._next_weekday(11)

        # First booking
        resp1 = await client.post("/api/v1/appointments", json={
            "barber_id": ctx["barber"]["id"],
            "service_id": ctx["service"]["id"],
            "start_time": start_time,
        }, headers=cl["headers"])
        assert resp1.status_code == 201

        # Second booking at same time
        resp2 = await client.post("/api/v1/appointments", json={
            "barber_id": ctx["barber"]["id"],
            "service_id": ctx["service"]["id"],
            "start_time": start_time,
        }, headers=cl["headers"])
        assert resp2.status_code == 409

    async def test_cancel_appointment(self, client: AsyncClient):
        ctx = await self._setup_barber_with_availability(client)
        cl = await self._register_client(client)
        start_time = self._next_weekday(12)

        create_resp = await client.post("/api/v1/appointments", json={
            "barber_id": ctx["barber"]["id"],
            "service_id": ctx["service"]["id"],
            "start_time": start_time,
        }, headers=cl["headers"])
        appt_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/appointments/{appt_id}/cancel",
            json={"reason": "changed my mind"},
            headers=cl["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    async def test_complete_appointment(self, client: AsyncClient):
        ctx = await self._setup_barber_with_availability(client)
        cl = await self._register_client(client)
        start_time = self._next_weekday(13)

        create_resp = await client.post("/api/v1/appointments", json={
            "barber_id": ctx["barber"]["id"],
            "service_id": ctx["service"]["id"],
            "start_time": start_time,
        }, headers=cl["headers"])
        appt_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/appointments/{appt_id}/complete",
            headers=ctx["barber_headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    async def test_reschedule_appointment(self, client: AsyncClient):
        ctx = await self._setup_barber_with_availability(client)
        cl = await self._register_client(client)
        start_time = self._next_weekday(14)

        create_resp = await client.post("/api/v1/appointments", json={
            "barber_id": ctx["barber"]["id"],
            "service_id": ctx["service"]["id"],
            "start_time": start_time,
        }, headers=cl["headers"])
        appt_id = create_resp.json()["id"]

        new_time = self._next_weekday(15)
        resp = await client.post(
            f"/api/v1/appointments/{appt_id}/reschedule",
            json={"new_start_time": new_time},
            headers=cl["headers"],
        )
        assert resp.status_code == 200

    async def test_list_appointments_authenticated(self, client: AsyncClient):
        ctx = await self._setup_barber_with_availability(client)
        cl = await self._register_client(client)

        resp = await client.get("/api/v1/appointments", headers=cl["headers"])
        assert resp.status_code == 200
        assert "items" in resp.json()

    async def test_unauthenticated_booking_rejected(self, client: AsyncClient):
        resp = await client.post("/api/v1/appointments", json={
            "barber_id": str(uuid4()),
            "service_id": str(uuid4()),
            "start_time": self._next_weekday(10),
        })
        assert resp.status_code == 401
