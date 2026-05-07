"""Domain entities representing core business objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4


class UserRole(Enum):
    """User roles in the system."""
    BARBER = "barber"
    CLIENT = "client"


class AppointmentStatus(Enum):
    """Appointment lifecycle statuses."""
    BOOKED = "booked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WeekDay(Enum):
    """Days of the week for availability."""
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


@dataclass
class User:
    """Base user entity."""
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    full_name: str = ""
    phone: str = ""
    hashed_password: str = ""
    role: UserRole = UserRole.CLIENT
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Service:
    """Service offered by barbers."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    duration_minutes: int = 30
    price: float = 0.0
    barber_id: Optional[UUID] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AvailabilitySlot:
    """Barber availability time slot."""
    id: UUID = field(default_factory=uuid4)
    barber_id: UUID = field(default_factory=uuid4)
    day_of_week: WeekDay = WeekDay.MONDAY
    start_time: time = field(default_factory=lambda: time(9, 0))
    end_time: time = field(default_factory=lambda: time(18, 0))
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TimeOff:
    """Barber time-off (vacation, sick days, etc.)."""
    id: UUID = field(default_factory=uuid4)
    barber_id: UUID = field(default_factory=uuid4)
    start_datetime: datetime = field(default_factory=datetime.utcnow)
    end_datetime: datetime = field(default_factory=datetime.utcnow)
    reason: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Appointment:
    """Appointment booking entity."""
    id: UUID = field(default_factory=uuid4)
    barber_id: UUID = field(default_factory=uuid4)
    client_id: UUID = field(default_factory=uuid4)
    service_id: UUID = field(default_factory=uuid4)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime = field(default_factory=datetime.utcnow)
    status: AppointmentStatus = AppointmentStatus.BOOKED
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def is_overlapping(self, other: Appointment) -> bool:
        """Check if this appointment overlaps with another.
        
        Two appointments overlap if one starts before the other ends
        and ends after the other starts.
        """
        return (
            self.barber_id == other.barber_id and
            self.start_time < other.end_time and
            self.end_time > other.start_time and
            self.status != AppointmentStatus.CANCELLED and
            other.status != AppointmentStatus.CANCELLED
        )

    def get_duration(self) -> timedelta:
        """Get the duration of the appointment."""
        return self.end_time - self.start_time

    def can_complete(self) -> bool:
        """Check if appointment can be marked as completed."""
        return self.status == AppointmentStatus.BOOKED

    def can_cancel(self) -> bool:
        """Check if appointment can be cancelled."""
        return self.status == AppointmentStatus.BOOKED


@dataclass
class AuditLog:
    """Audit trail for appointment changes."""
    id: UUID = field(default_factory=uuid4)
    appointment_id: UUID = field(default_factory=uuid4)
    action: str = ""  # e.g., "created", "completed", "cancelled"
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    performed_by: UUID = field(default_factory=uuid4)
    performed_at: datetime = field(default_factory=datetime.utcnow)
    details: str = ""
