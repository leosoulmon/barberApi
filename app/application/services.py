"""Application services implementing use cases."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from ..domain.entities import (
    User, UserRole, Service, Appointment, AppointmentStatus,
    AvailabilitySlot, TimeOff, AuditLog, WeekDay
)
from ..domain.protocols import (
    UserRepository, ServiceRepository, AppointmentRepository,
    AvailabilityRepository, TimeOffRepository, AuditRepository
)
from .exceptions import (
    UserNotFoundError, ServiceNotFoundError, AppointmentNotFoundError,
    AppointmentConflictError, InvalidAppointmentTimeError,
    BarberNotAvailableError, TimeOffConflictError,
    DuplicateEmailError, InvalidCredentialsError
)


class UserService:
    """User management service."""
    
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo
    
    async def get_user(self, user_id: UUID) -> User:
        """Get user by ID."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self._user_repo.get_by_email(email)
    
    async def list_users(self, role: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[User]:
        """List users, optionally filtered by role."""
        if role:
            return await self._user_repo.list_by_role(role, skip, limit)
        return await self._user_repo.list_all(skip, limit)
    
    async def list_barbers(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List all barbers."""
        return await self._user_repo.list_by_role(UserRole.BARBER.value, skip, limit)
    
    async def create_user(self, user: User) -> User:
        """Create a new user."""
        existing = await self._user_repo.get_by_email(user.email)
        if existing:
            raise DuplicateEmailError(f"Email {user.email} already registered")
        return await self._user_repo.create(user)
    
    async def update_user(self, user: User) -> User:
        """Update an existing user."""
        existing = await self._user_repo.get_by_id(user.id)
        if not existing:
            raise UserNotFoundError(f"User {user.id} not found")
        return await self._user_repo.update(user)
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete a user."""
        return await self._user_repo.delete(user_id)


class ServiceCatalogService:
    """Service catalog management service."""
    
    def __init__(self, service_repo: ServiceRepository, user_repo: UserRepository):
        self._service_repo = service_repo
        self._user_repo = user_repo
    
    async def get_service(self, service_id: UUID) -> Service:
        """Get service by ID."""
        service = await self._service_repo.get_by_id(service_id)
        if not service:
            raise ServiceNotFoundError(f"Service {service_id} not found")
        return service
    
    async def list_barber_services(self, barber_id: UUID, skip: int = 0, limit: int = 100) -> List[Service]:
        """List services offered by a barber."""
        return await self._service_repo.list_by_barber(barber_id, skip, limit)
    
    async def list_active_services(self, skip: int = 0, limit: int = 100) -> List[Service]:
        """List all active services."""
        return await self._service_repo.list_active(skip, limit)
    
    async def create_service(self, service: Service) -> Service:
        """Create a new service."""
        return await self._service_repo.create(service)
    
    async def update_service(self, service: Service) -> Service:
        """Update an existing service."""
        existing = await self._service_repo.get_by_id(service.id)
        if not existing:
            raise ServiceNotFoundError(f"Service {service.id} not found")
        return await self._service_repo.update(service)
    
    async def delete_service(self, service_id: UUID) -> bool:
        """Delete a service."""
        return await self._service_repo.delete(service_id)


class AvailabilityService:
    """Barber availability management service."""
    
    def __init__(
        self,
        availability_repo: AvailabilityRepository,
        time_off_repo: TimeOffRepository,
        user_repo: UserRepository
    ):
        self._availability_repo = availability_repo
        self._time_off_repo = time_off_repo
        self._user_repo = user_repo
    
    async def get_availability(self, slot_id: UUID) -> AvailabilitySlot:
        """Get availability slot by ID."""
        slot = await self._availability_repo.get_by_id(slot_id)
        if not slot:
            raise ServiceNotFoundError(f"Availability slot {slot_id} not found")
        return slot
    
    async def list_barber_availability(self, barber_id: UUID) -> List[AvailabilitySlot]:
        """List all availability slots for a barber."""
        return await self._availability_repo.list_by_barber(barber_id)
    
    async def create_availability(self, slot: AvailabilitySlot) -> AvailabilitySlot:
        """Create a new availability slot."""
        return await self._availability_repo.create(slot)
    
    async def update_availability(self, slot: AvailabilitySlot) -> AvailabilitySlot:
        """Update an availability slot."""
        existing = await self._availability_repo.get_by_id(slot.id)
        if not existing:
            raise ServiceNotFoundError(f"Availability slot {slot.id} not found")
        return await self._availability_repo.update(slot)
    
    async def delete_availability(self, slot_id: UUID) -> bool:
        """Delete an availability slot."""
        return await self._availability_repo.delete(slot_id)
    
    async def is_barber_available(
        self, barber_id: UUID, start_time: datetime, end_time: datetime
    ) -> bool:
        """Check if barber is available during time range.
        
        Checks both regular availability slots and time-off entries.
        """
        # Check if within working hours
        day_of_week = WeekDay(start_time.isoweekday())
        availability_slots = await self._availability_repo.list_by_barber_and_day(
            barber_id, day_of_week.value
        )
        
        if not availability_slots:
            return False
        
        # Check if time falls within any availability slot
        time_in_slot = False
        for slot in availability_slots:
            if slot.is_active:
                slot_start = datetime.combine(start_time.date(), slot.start_time)
                slot_end = datetime.combine(start_time.date(), slot.end_time)
                if start_time >= slot_start and end_time <= slot_end:
                    time_in_slot = True
                    break
        
        if not time_in_slot:
            return False
        
        # Check for time-off conflicts
        time_offs = await self._time_off_repo.list_by_barber(
            barber_id, start_time, end_time
        )
        
        for time_off in time_offs:
            if time_off.start_datetime < end_time and time_off.end_datetime > start_time:
                return False
        
        return True


class AppointmentBookingService:
    """Appointment booking service with collision detection."""
    
    def __init__(
        self,
        appointment_repo: AppointmentRepository,
        service_repo: ServiceRepository,
        availability_service: AvailabilityService,
        audit_repo: AuditRepository
    ):
        self._appointment_repo = appointment_repo
        self._service_repo = service_repo
        self._availability_service = availability_service
        self._audit_repo = audit_repo
    
    async def get_appointment(self, appointment_id: UUID) -> Appointment:
        """Get appointment by ID."""
        appointment = await self._appointment_repo.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")
        return appointment
    
    async def list_barber_appointments(
        self, barber_id: UUID, start: datetime, end: datetime, skip: int = 0, limit: int = 100
    ) -> List[Appointment]:
        """List appointments for a barber within date range."""
        return await self._appointment_repo.list_by_barber(barber_id, start, end, skip, limit)
    
    async def list_client_appointments(
        self, client_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Appointment]:
        """List appointments for a client."""
        return await self._appointment_repo.list_by_client(client_id, skip, limit)
    
    async def book_appointment(
        self, appointment: Appointment, requested_by: UUID
    ) -> Appointment:
        """Book a new appointment with validation.
        
        Validates:
        - Service exists and duration matches
        - Barber is available at requested time
        - No conflicts with existing appointments
        - Requested time is not in the past
        """
        # Validate time is not in the past
        if appointment.start_time < datetime.utcnow():
            raise InvalidAppointmentTimeError("Cannot book appointments in the past")
        
        # Get service and validate
        service = await self._service_repo.get_by_id(appointment.service_id)
        if not service:
            raise ServiceNotFoundError(f"Service {appointment.service_id} not found")
        
        # Calculate end time based on service duration
        expected_end = appointment.start_time + timedelta(minutes=service.duration_minutes)
        if appointment.end_time != expected_end:
            appointment.end_time = expected_end
        
        # Check barber availability
        is_available = await self._availability_service.is_barber_available(
            appointment.barber_id, appointment.start_time, appointment.end_time
        )
        if not is_available:
            raise BarberNotAvailableError("Barber is not available at the requested time")
        
        # Check for appointment conflicts
        conflicts = await self._appointment_repo.list_conflicting(
            appointment.barber_id,
            appointment.start_time,
            appointment.end_time
        )
        if conflicts:
            conflict_times = [f"{c.start_time}" for c in conflicts]
            raise AppointmentConflictError(
                f"Time conflicts with existing appointments: {conflict_times}"
            )
        
        # Create appointment
        created = await self._appointment_repo.create(appointment)
        
        # Create audit log
        await self._audit_repo.create(AuditLog(
            appointment_id=created.id,
            action="created",
            new_status=created.status.value,
            performed_by=requested_by,
            details=f"Appointment booked for service {service.name}"
        ))
        
        return created
    
    async def complete_appointment(
        self, appointment_id: UUID, completed_by: UUID
    ) -> Appointment:
        """Mark an appointment as completed."""
        appointment = await self.get_appointment(appointment_id)
        
        if not appointment.can_complete():
            raise InvalidAppointmentTimeError(
                f"Cannot complete appointment with status {appointment.status.value}"
            )
        
        old_status = appointment.status
        appointment.status = AppointmentStatus.COMPLETED
        updated = await self._appointment_repo.update(appointment)
        
        # Create audit log
        await self._audit_repo.create(AuditLog(
            appointment_id=updated.id,
            action="completed",
            previous_status=old_status.value,
            new_status=updated.status.value,
            performed_by=completed_by,
            details="Appointment marked as completed"
        ))
        
        return updated
    
    async def cancel_appointment(
        self, appointment_id: UUID, cancelled_by: UUID, reason: str = ""
    ) -> Appointment:
        """Cancel an appointment."""
        appointment = await self.get_appointment(appointment_id)
        
        if not appointment.can_cancel():
            raise InvalidAppointmentTimeError(
                f"Cannot cancel appointment with status {appointment.status.value}"
            )
        
        old_status = appointment.status
        appointment.status = AppointmentStatus.CANCELLED
        updated = await self._appointment_repo.update(appointment)
        
        # Create audit log
        await self._audit_repo.create(AuditLog(
            appointment_id=updated.id,
            action="cancelled",
            previous_status=old_status.value,
            new_status=updated.status.value,
            performed_by=cancelled_by,
            details=f"Appointment cancelled. Reason: {reason}"
        ))
        
        return updated
    
    async def reschedule_appointment(
        self, appointment_id: UUID, new_start_time: datetime, rescheduled_by: UUID
    ) -> Appointment:
        """Reschedule an appointment to a new time."""
        appointment = await self.get_appointment(appointment_id)
        
        if appointment.status != AppointmentStatus.BOOKED:
            raise InvalidAppointmentTimeError(
                f"Cannot reschedule appointment with status {appointment.status.value}"
            )
        
        # Get service for duration
        service = await self._service_repo.get_by_id(appointment.service_id)
        if not service:
            raise ServiceNotFoundError(f"Service {appointment.service_id} not found")
        
        # Calculate new end time
        new_end_time = new_start_time + timedelta(minutes=service.duration_minutes)
        
        # Validate new time is not in the past
        if new_start_time < datetime.utcnow():
            raise InvalidAppointmentTimeError("Cannot reschedule to a time in the past")
        
        # Check barber availability
        is_available = await self._availability_service.is_barber_available(
            appointment.barber_id, new_start_time, new_end_time
        )
        if not is_available:
            raise BarberNotAvailableError("Barber is not available at the new time")
        
        # Check for conflicts (excluding this appointment)
        conflicts = await self._appointment_repo.list_conflicting(
            appointment.barber_id,
            new_start_time,
            new_end_time,
            exclude_id=appointment.id
        )
        if conflicts:
            raise AppointmentConflictError("New time conflicts with existing appointments")
        
        # Update appointment
        old_start = appointment.start_time
        appointment.start_time = new_start_time
        appointment.end_time = new_end_time
        updated = await self._appointment_repo.update(appointment)
        
        # Create audit log
        await self._audit_repo.create(AuditLog(
            appointment_id=updated.id,
            action="rescheduled",
            performed_by=rescheduled_by,
            details=f"Appointment rescheduled from {old_start} to {new_start_time}"
        ))
        
        return updated


class AuditService:
    """Audit trail service."""
    
    def __init__(self, audit_repo: AuditRepository):
        self._audit_repo = audit_repo
    
    async def get_audit_entry(self, audit_id: UUID) -> AuditLog:
        """Get audit log entry by ID."""
        entry = await self._audit_repo.get_by_id(audit_id)
        if not entry:
            raise AppointmentNotFoundError(f"Audit entry {audit_id} not found")
        return entry
    
    async def list_appointment_history(
        self, appointment_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[AuditLog]:
        """Get audit history for an appointment."""
        return await self._audit_repo.list_by_appointment(appointment_id, skip, limit)
