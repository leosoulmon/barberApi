"""Unit tests for domain entities and their business rules."""
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.entities import (
    Appointment, AppointmentStatus, User, UserRole, Service, WeekDay,
)


class TestAppointmentOverlap:
    """Tests for Appointment.is_overlapping business rule."""

    def _make_appointment(
        self, barber_id=None, start_offset_hours=0, duration_minutes=30,
        status=AppointmentStatus.BOOKED
    ) -> Appointment:
        barber = barber_id or uuid4()
        start = datetime(2024, 6, 15, 10, 0) + timedelta(hours=start_offset_hours)
        return Appointment(
            barber_id=barber,
            client_id=uuid4(),
            service_id=uuid4(),
            start_time=start,
            end_time=start + timedelta(minutes=duration_minutes),
            status=status,
        )

    def test_overlapping_same_barber(self):
        """Two appointments for the same barber at the same time overlap."""
        barber = uuid4()
        a = self._make_appointment(barber_id=barber)
        b = self._make_appointment(barber_id=barber)
        assert a.is_overlapping(b) is True

    def test_no_overlap_different_barber(self):
        """Same time but different barbers do not overlap."""
        a = self._make_appointment(barber_id=uuid4())
        b = self._make_appointment(barber_id=uuid4())
        assert a.is_overlapping(b) is False

    def test_no_overlap_sequential(self):
        """Back-to-back appointments do not overlap."""
        barber = uuid4()
        a = self._make_appointment(barber_id=barber, start_offset_hours=0, duration_minutes=30)
        # Starts exactly when 'a' ends
        b = Appointment(
            barber_id=barber,
            client_id=uuid4(),
            service_id=uuid4(),
            start_time=a.end_time,
            end_time=a.end_time + timedelta(minutes=30),
            status=AppointmentStatus.BOOKED,
        )
        assert a.is_overlapping(b) is False

    def test_cancelled_does_not_overlap(self):
        """A cancelled appointment does not create a conflict."""
        barber = uuid4()
        a = self._make_appointment(barber_id=barber, status=AppointmentStatus.CANCELLED)
        b = self._make_appointment(barber_id=barber)
        assert a.is_overlapping(b) is False

    def test_partial_overlap(self):
        """Partially overlapping time windows are detected."""
        barber = uuid4()
        a = self._make_appointment(barber_id=barber, duration_minutes=60)
        # b starts 30 min after a starts (still within a's window)
        b = Appointment(
            barber_id=barber,
            client_id=uuid4(),
            service_id=uuid4(),
            start_time=a.start_time + timedelta(minutes=30),
            end_time=a.start_time + timedelta(minutes=90),
            status=AppointmentStatus.BOOKED,
        )
        assert a.is_overlapping(b) is True


class TestAppointmentLifecycle:
    """Tests for can_complete / can_cancel guards."""

    def test_can_complete_booked(self):
        appt = Appointment(status=AppointmentStatus.BOOKED)
        assert appt.can_complete() is True

    def test_cannot_complete_cancelled(self):
        appt = Appointment(status=AppointmentStatus.CANCELLED)
        assert appt.can_complete() is False

    def test_cannot_complete_completed(self):
        appt = Appointment(status=AppointmentStatus.COMPLETED)
        assert appt.can_complete() is False

    def test_can_cancel_booked(self):
        appt = Appointment(status=AppointmentStatus.BOOKED)
        assert appt.can_cancel() is True

    def test_cannot_cancel_completed(self):
        appt = Appointment(status=AppointmentStatus.COMPLETED)
        assert appt.can_cancel() is False

    def test_cannot_cancel_cancelled(self):
        appt = Appointment(status=AppointmentStatus.CANCELLED)
        assert appt.can_cancel() is False


class TestAppointmentDuration:
    """Tests for get_duration helper."""

    def test_duration(self):
        start = datetime(2024, 6, 15, 10, 0)
        appt = Appointment(
            start_time=start,
            end_time=start + timedelta(minutes=45),
        )
        assert appt.get_duration() == timedelta(minutes=45)


class TestUserEntity:
    """Basic User entity sanity checks."""

    def test_default_role_is_client(self):
        user = User()
        assert user.role == UserRole.CLIENT

    def test_default_active(self):
        user = User()
        assert user.is_active is True


class TestServiceEntity:
    """Basic Service entity checks."""

    def test_default_duration(self):
        svc = Service()
        assert svc.duration_minutes == 30

    def test_default_active(self):
        svc = Service()
        assert svc.is_active is True
