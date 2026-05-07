"""Unit tests for application services using mocked repositories."""
from datetime import datetime, time, timedelta
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from app.domain.entities import (
    Appointment, AppointmentStatus, AvailabilitySlot, AuditLog,
    Service, TimeOff, User, UserRole, WeekDay,
)
from app.application.services import (
    UserService, ServiceCatalogService, AvailabilityService, AppointmentBookingService,
)
from app.application.exceptions import (
    UserNotFoundError, DuplicateEmailError, ServiceNotFoundError,
    AppointmentConflictError, BarberNotAvailableError, InvalidAppointmentTimeError,
)


# ────────────────────────────────────────────────────────────────────────────
# UserService
# ────────────────────────────────────────────────────────────────────────────

class TestUserService:
    """Tests for UserService."""

    def _make_service(self) -> tuple[UserService, AsyncMock]:
        repo = AsyncMock()
        return UserService(repo), repo

    @pytest.mark.asyncio
    async def test_get_user_found(self):
        svc, repo = self._make_service()
        user = User(id=uuid4(), email="a@b.com", full_name="Test")
        repo.get_by_id.return_value = user

        result = await svc.get_user(user.id)
        assert result.email == "a@b.com"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self):
        svc, repo = self._make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await svc.get_user(uuid4())

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self):
        svc, repo = self._make_service()
        repo.get_by_email.return_value = User(email="dup@test.com")

        with pytest.raises(DuplicateEmailError):
            await svc.create_user(User(email="dup@test.com", full_name="X"))

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        svc, repo = self._make_service()
        repo.get_by_email.return_value = None
        user = User(email="new@test.com", full_name="New User")
        repo.create.return_value = user

        result = await svc.create_user(user)
        assert result.email == "new@test.com"
        repo.create.assert_awaited_once_with(user)


# ────────────────────────────────────────────────────────────────────────────
# AppointmentBookingService
# ────────────────────────────────────────────────────────────────────────────

class TestAppointmentBookingService:
    """Tests for AppointmentBookingService booking logic."""

    def _make_service(self):
        appointment_repo = AsyncMock()
        service_repo = AsyncMock()
        availability_svc = AsyncMock()
        audit_repo = AsyncMock()
        svc = AppointmentBookingService(
            appointment_repo, service_repo, availability_svc, audit_repo
        )
        return svc, appointment_repo, service_repo, availability_svc, audit_repo

    @pytest.mark.asyncio
    async def test_book_in_past_raises(self):
        svc, appt_repo, svc_repo, avail_svc, audit_repo = self._make_service()
        appointment = Appointment(
            start_time=datetime(2020, 1, 1, 10, 0),
            status=AppointmentStatus.BOOKED,
        )

        with pytest.raises(InvalidAppointmentTimeError):
            await svc.book_appointment(appointment, uuid4())

    @pytest.mark.asyncio
    async def test_book_service_not_found(self):
        svc, appt_repo, svc_repo, avail_svc, audit_repo = self._make_service()
        svc_repo.get_by_id.return_value = None
        appointment = Appointment(
            start_time=datetime.utcnow() + timedelta(days=1),
            status=AppointmentStatus.BOOKED,
        )

        with pytest.raises(ServiceNotFoundError):
            await svc.book_appointment(appointment, uuid4())

    @pytest.mark.asyncio
    async def test_book_barber_unavailable(self):
        svc, appt_repo, svc_repo, avail_svc, audit_repo = self._make_service()
        service = Service(duration_minutes=30)
        svc_repo.get_by_id.return_value = service
        avail_svc.is_barber_available.return_value = False

        appointment = Appointment(
            start_time=datetime.utcnow() + timedelta(days=1),
            status=AppointmentStatus.BOOKED,
        )

        with pytest.raises(BarberNotAvailableError):
            await svc.book_appointment(appointment, uuid4())

    @pytest.mark.asyncio
    async def test_book_conflict(self):
        svc, appt_repo, svc_repo, avail_svc, audit_repo = self._make_service()
        service = Service(duration_minutes=30)
        svc_repo.get_by_id.return_value = service
        avail_svc.is_barber_available.return_value = True
        appt_repo.list_conflicting.return_value = [Appointment()]

        appointment = Appointment(
            start_time=datetime.utcnow() + timedelta(days=1),
            status=AppointmentStatus.BOOKED,
        )

        with pytest.raises(AppointmentConflictError):
            await svc.book_appointment(appointment, uuid4())

    @pytest.mark.asyncio
    async def test_book_success(self):
        svc, appt_repo, svc_repo, avail_svc, audit_repo = self._make_service()
        service = Service(name="Haircut", duration_minutes=30)
        svc_repo.get_by_id.return_value = service
        avail_svc.is_barber_available.return_value = True
        appt_repo.list_conflicting.return_value = []

        start = datetime.utcnow() + timedelta(days=1)
        appointment = Appointment(
            barber_id=uuid4(),
            client_id=uuid4(),
            service_id=service.id,
            start_time=start,
            status=AppointmentStatus.BOOKED,
        )
        appt_repo.create.return_value = appointment
        audit_repo.create.return_value = AuditLog()

        result = await svc.book_appointment(appointment, uuid4())
        assert result.status == AppointmentStatus.BOOKED
        appt_repo.create.assert_awaited_once()
        audit_repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cancel_success(self):
        svc, appt_repo, svc_repo, avail_svc, audit_repo = self._make_service()
        appointment = Appointment(id=uuid4(), status=AppointmentStatus.BOOKED)
        appt_repo.get_by_id.return_value = appointment
        appt_repo.update.return_value = Appointment(
            id=appointment.id, status=AppointmentStatus.CANCELLED
        )
        audit_repo.create.return_value = AuditLog()

        result = await svc.cancel_appointment(appointment.id, uuid4(), "changed mind")
        assert result.status == AppointmentStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_complete_success(self):
        svc, appt_repo, svc_repo, avail_svc, audit_repo = self._make_service()
        appointment = Appointment(id=uuid4(), status=AppointmentStatus.BOOKED)
        appt_repo.get_by_id.return_value = appointment
        appt_repo.update.return_value = Appointment(
            id=appointment.id, status=AppointmentStatus.COMPLETED
        )
        audit_repo.create.return_value = AuditLog()

        result = await svc.complete_appointment(appointment.id, uuid4())
        assert result.status == AppointmentStatus.COMPLETED


# ────────────────────────────────────────────────────────────────────────────
# AvailabilityService
# ────────────────────────────────────────────────────────────────────────────

class TestAvailabilityService:
    """Tests for AvailabilityService.is_barber_available."""

    def _make_service(self):
        avail_repo = AsyncMock()
        time_off_repo = AsyncMock()
        user_repo = AsyncMock()
        svc = AvailabilityService(avail_repo, time_off_repo, user_repo)
        return svc, avail_repo, time_off_repo

    @pytest.mark.asyncio
    async def test_no_slots_means_unavailable(self):
        svc, avail_repo, time_off_repo = self._make_service()
        avail_repo.list_by_barber_and_day.return_value = []

        start = datetime(2024, 6, 17, 10, 0)  # Monday
        result = await svc.is_barber_available(uuid4(), start, start + timedelta(minutes=30))
        assert result is False

    @pytest.mark.asyncio
    async def test_available_within_slot(self):
        svc, avail_repo, time_off_repo = self._make_service()
        slot = AvailabilitySlot(
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=True,
        )
        avail_repo.list_by_barber_and_day.return_value = [slot]
        time_off_repo.list_by_barber.return_value = []

        start = datetime(2024, 6, 17, 10, 0)  # Monday
        result = await svc.is_barber_available(uuid4(), start, start + timedelta(minutes=30))
        assert result is True

    @pytest.mark.asyncio
    async def test_unavailable_due_to_time_off(self):
        svc, avail_repo, time_off_repo = self._make_service()
        slot = AvailabilitySlot(
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=True,
        )
        avail_repo.list_by_barber_and_day.return_value = [slot]
        time_off = TimeOff(
            start_datetime=datetime(2024, 6, 17, 8, 0),
            end_datetime=datetime(2024, 6, 17, 12, 0),
        )
        time_off_repo.list_by_barber.return_value = [time_off]

        start = datetime(2024, 6, 17, 10, 0)
        result = await svc.is_barber_available(uuid4(), start, start + timedelta(minutes=30))
        assert result is False

    @pytest.mark.asyncio
    async def test_unavailable_outside_slot_hours(self):
        svc, avail_repo, time_off_repo = self._make_service()
        slot = AvailabilitySlot(
            day_of_week=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(12, 0),
            is_active=True,
        )
        avail_repo.list_by_barber_and_day.return_value = [slot]
        time_off_repo.list_by_barber.return_value = []

        start = datetime(2024, 6, 17, 14, 0)  # After slot ends
        result = await svc.is_barber_available(uuid4(), start, start + timedelta(minutes=30))
        assert result is False
