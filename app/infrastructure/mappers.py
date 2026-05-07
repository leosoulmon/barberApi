"""Mappers between domain entities and database models."""
from datetime import datetime
from typing import Optional

from ..domain.entities import (
    User, UserRole, Service, AvailabilitySlot, WeekDay,
    TimeOff, Appointment, AppointmentStatus, AuditLog
)
from .models import (
    UserModel, ServiceModel, AvailabilitySlotModel,
    TimeOffModel, AppointmentModel, AuditLogModel
)


class UserMapper:
    """Map between User domain entity and UserModel."""
    
    @staticmethod
    def to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            phone=model.phone,
            hashed_password=model.hashed_password,
            role=UserRole(model.role),
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    @staticmethod
    def to_model(entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            email=entity.email,
            full_name=entity.full_name,
            phone=entity.phone,
            hashed_password=entity.hashed_password,
            role=entity.role.value,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class ServiceMapper:
    """Map between Service domain entity and ServiceModel."""
    
    @staticmethod
    def to_domain(model: ServiceModel) -> Service:
        return Service(
            id=model.id,
            name=model.name,
            description=model.description,
            duration_minutes=model.duration_minutes,
            price=model.price,
            barber_id=model.barber_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    @staticmethod
    def to_model(entity: Service) -> ServiceModel:
        return ServiceModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            duration_minutes=entity.duration_minutes,
            price=entity.price,
            barber_id=entity.barber_id,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class AvailabilitySlotMapper:
    """Map between AvailabilitySlot domain entity and AvailabilitySlotModel."""
    
    @staticmethod
    def to_domain(model: AvailabilitySlotModel) -> AvailabilitySlot:
        return AvailabilitySlot(
            id=model.id,
            barber_id=model.barber_id,
            day_of_week=WeekDay(model.day_of_week),
            start_time=model.start_time,
            end_time=model.end_time,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    @staticmethod
    def to_model(entity: AvailabilitySlot) -> AvailabilitySlotModel:
        return AvailabilitySlotModel(
            id=entity.id,
            barber_id=entity.barber_id,
            day_of_week=entity.day_of_week.value,
            start_time=entity.start_time,
            end_time=entity.end_time,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class TimeOffMapper:
    """Map between TimeOff domain entity and TimeOffModel."""
    
    @staticmethod
    def to_domain(model: TimeOffModel) -> TimeOff:
        return TimeOff(
            id=model.id,
            barber_id=model.barber_id,
            start_datetime=model.start_datetime,
            end_datetime=model.end_datetime,
            reason=model.reason,
            created_at=model.created_at
        )
    
    @staticmethod
    def to_model(entity: TimeOff) -> TimeOffModel:
        return TimeOffModel(
            id=entity.id,
            barber_id=entity.barber_id,
            start_datetime=entity.start_datetime,
            end_datetime=entity.end_datetime,
            reason=entity.reason,
            created_at=entity.created_at
        )


class AppointmentMapper:
    """Map between Appointment domain entity and AppointmentModel."""
    
    @staticmethod
    def to_domain(model: AppointmentModel) -> Appointment:
        return Appointment(
            id=model.id,
            barber_id=model.barber_id,
            client_id=model.client_id,
            service_id=model.service_id,
            start_time=model.start_time,
            end_time=model.end_time,
            status=AppointmentStatus(model.status),
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    @staticmethod
    def to_model(entity: Appointment) -> AppointmentModel:
        return AppointmentModel(
            id=entity.id,
            barber_id=entity.barber_id,
            client_id=entity.client_id,
            service_id=entity.service_id,
            start_time=entity.start_time,
            end_time=entity.end_time,
            status=entity.status.value,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )


class AuditLogMapper:
    """Map between AuditLog domain entity and AuditLogModel."""
    
    @staticmethod
    def to_domain(model: AuditLogModel) -> AuditLog:
        return AuditLog(
            id=model.id,
            appointment_id=model.appointment_id,
            action=model.action,
            previous_status=model.previous_status,
            new_status=model.new_status,
            performed_by=model.performed_by,
            performed_at=model.performed_at,
            details=model.details
        )
    
    @staticmethod
    def to_model(entity: AuditLog) -> AuditLogModel:
        return AuditLogModel(
            id=entity.id,
            appointment_id=entity.appointment_id,
            action=entity.action,
            previous_status=entity.previous_status,
            new_status=entity.new_status,
            performed_by=entity.performed_by,
            performed_at=entity.performed_at,
            details=entity.details
        )
