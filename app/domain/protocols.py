"""Repository protocols (interfaces) using typing.Protocol.

These define the contract for data persistence without committing to a specific database.
"""
from __future__ import annotations

from typing import List, Optional, Protocol
from uuid import UUID
from datetime import datetime

from .entities import (
    User, Service, AvailabilitySlot, TimeOff, Appointment, AuditLog
)


class UserRepository(Protocol):
    """Protocol for user persistence operations."""
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        ...
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        ...
    
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users with pagination."""
        ...
    
    async def list_by_role(self, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """List users by role."""
        ...
    
    async def create(self, user: User) -> User:
        """Create a new user."""
        ...
    
    async def update(self, user: User) -> User:
        """Update an existing user."""
        ...
    
    async def delete(self, user_id: UUID) -> bool:
        """Delete a user."""
        ...


class ServiceRepository(Protocol):
    """Protocol for service persistence operations."""
    
    async def get_by_id(self, service_id: UUID) -> Optional[Service]:
        """Get service by ID."""
        ...
    
    async def list_by_barber(self, barber_id: UUID, skip: int = 0, limit: int = 100) -> List[Service]:
        """List services offered by a barber."""
        ...
    
    async def list_active(self, skip: int = 0, limit: int = 100) -> List[Service]:
        """List all active services."""
        ...
    
    async def create(self, service: Service) -> Service:
        """Create a new service."""
        ...
    
    async def update(self, service: Service) -> Service:
        """Update an existing service."""
        ...
    
    async def delete(self, service_id: UUID) -> bool:
        """Delete a service."""
        ...


class AvailabilityRepository(Protocol):
    """Protocol for availability slot persistence operations."""
    
    async def get_by_id(self, slot_id: UUID) -> Optional[AvailabilitySlot]:
        """Get availability slot by ID."""
        ...
    
    async def list_by_barber(self, barber_id: UUID) -> List[AvailabilitySlot]:
        """List all availability slots for a barber."""
        ...
    
    async def list_by_barber_and_day(self, barber_id: UUID, day_of_week: int) -> List[AvailabilitySlot]:
        """List availability slots for a barber on a specific day."""
        ...
    
    async def create(self, slot: AvailabilitySlot) -> AvailabilitySlot:
        """Create a new availability slot."""
        ...
    
    async def update(self, slot: AvailabilitySlot) -> AvailabilitySlot:
        """Update an existing availability slot."""
        ...
    
    async def delete(self, slot_id: UUID) -> bool:
        """Delete an availability slot."""
        ...


class TimeOffRepository(Protocol):
    """Protocol for time-off persistence operations."""
    
    async def get_by_id(self, time_off_id: UUID) -> Optional[TimeOff]:
        """Get time-off by ID."""
        ...
    
    async def list_by_barber(self, barber_id: UUID, start: datetime, end: datetime) -> List[TimeOff]:
        """List time-off for a barber within a date range."""
        ...
    
    async def create(self, time_off: TimeOff) -> TimeOff:
        """Create a new time-off entry."""
        ...
    
    async def update(self, time_off: TimeOff) -> TimeOff:
        """Update an existing time-off entry."""
        ...
    
    async def delete(self, time_off_id: UUID) -> bool:
        """Delete a time-off entry."""
        ...


class AppointmentRepository(Protocol):
    """Protocol for appointment persistence operations."""
    
    async def get_by_id(self, appointment_id: UUID) -> Optional[Appointment]:
        """Get appointment by ID."""
        ...
    
    async def list_by_barber(
        self, barber_id: UUID, start: datetime, end: datetime, skip: int = 0, limit: int = 100
    ) -> List[Appointment]:
        """List appointments for a barber within a date range."""
        ...
    
    async def list_by_client(
        self, client_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Appointment]:
        """List appointments for a client."""
        ...
    
    async def list_conflicting(
        self, barber_id: UUID, start_time: datetime, end_time: datetime, exclude_id: Optional[UUID] = None
    ) -> List[Appointment]:
        """List appointments that conflict with given time range."""
        ...
    
    async def create(self, appointment: Appointment) -> Appointment:
        """Create a new appointment."""
        ...
    
    async def update(self, appointment: Appointment) -> Appointment:
        """Update an existing appointment."""
        ...
    
    async def delete(self, appointment_id: UUID) -> bool:
        """Delete an appointment."""
        ...


class AuditRepository(Protocol):
    """Protocol for audit log persistence operations."""
    
    async def get_by_id(self, audit_id: UUID) -> Optional[AuditLog]:
        """Get audit log entry by ID."""
        ...
    
    async def list_by_appointment(self, appointment_id: UUID, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """List audit logs for an appointment."""
        ...
    
    async def create(self, audit_log: AuditLog) -> AuditLog:
        """Create a new audit log entry."""
        ...
