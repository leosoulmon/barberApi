"""Repository implementations for domain protocols."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import User, Service, AvailabilitySlot, TimeOff, Appointment, AuditLog
from .models import (
    UserModel, ServiceModel, AvailabilitySlotModel, TimeOffModel,
    AppointmentModel, AuditLogModel
)
from .mappers import (
    UserMapper, ServiceMapper, AvailabilitySlotMapper,
    TimeOffMapper, AppointmentMapper, AuditLogMapper
)


class SQLUserRepository:
    """SQL implementation of UserRepository protocol."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None
    
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self._session.execute(
            select(UserModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [UserMapper.to_domain(m) for m in models]
    
    async def list_by_role(self, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.role == role).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [UserMapper.to_domain(m) for m in models]
    
    async def create(self, user: User) -> User:
        model = UserMapper.to_model(user)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return UserMapper.to_domain(model)
    
    async def update(self, user: User) -> User:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        model = result.scalar_one()
        
        model.email = user.email
        model.full_name = user.full_name
        model.phone = user.phone
        model.hashed_password = user.hashed_password
        model.role = user.role.value
        model.is_active = user.is_active
        
        await self._session.commit()
        await self._session.refresh(model)
        return UserMapper.to_domain(model)
    
    async def delete(self, user_id: UUID) -> bool:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()
            return True
        return False


class SQLServiceRepository:
    """SQL implementation of ServiceRepository protocol."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, service_id: UUID) -> Optional[Service]:
        result = await self._session.execute(
            select(ServiceModel).where(ServiceModel.id == service_id)
        )
        model = result.scalar_one_or_none()
        return ServiceMapper.to_domain(model) if model else None
    
    async def list_by_barber(self, barber_id: UUID, skip: int = 0, limit: int = 100) -> List[Service]:
        result = await self._session.execute(
            select(ServiceModel)
            .where(ServiceModel.barber_id == barber_id)
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [ServiceMapper.to_domain(m) for m in models]
    
    async def list_active(self, skip: int = 0, limit: int = 100) -> List[Service]:
        result = await self._session.execute(
            select(ServiceModel)
            .where(ServiceModel.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [ServiceMapper.to_domain(m) for m in models]
    
    async def create(self, service: Service) -> Service:
        model = ServiceMapper.to_model(service)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return ServiceMapper.to_domain(model)
    
    async def update(self, service: Service) -> Service:
        result = await self._session.execute(
            select(ServiceModel).where(ServiceModel.id == service.id)
        )
        model = result.scalar_one()
        
        model.name = service.name
        model.description = service.description
        model.duration_minutes = service.duration_minutes
        model.price = service.price
        model.barber_id = service.barber_id
        model.is_active = service.is_active
        
        await self._session.commit()
        await self._session.refresh(model)
        return ServiceMapper.to_domain(model)
    
    async def delete(self, service_id: UUID) -> bool:
        result = await self._session.execute(
            select(ServiceModel).where(ServiceModel.id == service_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()
            return True
        return False


class SQLAvailabilityRepository:
    """SQL implementation of AvailabilityRepository protocol."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, slot_id: UUID) -> Optional[AvailabilitySlot]:
        result = await self._session.execute(
            select(AvailabilitySlotModel).where(AvailabilitySlotModel.id == slot_id)
        )
        model = result.scalar_one_or_none()
        return AvailabilitySlotMapper.to_domain(model) if model else None
    
    async def list_by_barber(self, barber_id: UUID) -> List[AvailabilitySlot]:
        result = await self._session.execute(
            select(AvailabilitySlotModel).where(AvailabilitySlotModel.barber_id == barber_id)
        )
        models = result.scalars().all()
        return [AvailabilitySlotMapper.to_domain(m) for m in models]
    
    async def list_by_barber_and_day(self, barber_id: UUID, day_of_week: int) -> List[AvailabilitySlot]:
        result = await self._session.execute(
            select(AvailabilitySlotModel)
            .where(
                and_(
                    AvailabilitySlotModel.barber_id == barber_id,
                    AvailabilitySlotModel.day_of_week == day_of_week
                )
            )
        )
        models = result.scalars().all()
        return [AvailabilitySlotMapper.to_domain(m) for m in models]
    
    async def create(self, slot: AvailabilitySlot) -> AvailabilitySlot:
        model = AvailabilitySlotMapper.to_model(slot)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return AvailabilitySlotMapper.to_domain(model)
    
    async def update(self, slot: AvailabilitySlot) -> AvailabilitySlot:
        result = await self._session.execute(
            select(AvailabilitySlotModel).where(AvailabilitySlotModel.id == slot.id)
        )
        model = result.scalar_one()
        
        model.day_of_week = slot.day_of_week.value
        model.start_time = slot.start_time
        model.end_time = slot.end_time
        model.is_active = slot.is_active
        
        await self._session.commit()
        await self._session.refresh(model)
        return AvailabilitySlotMapper.to_domain(model)
    
    async def delete(self, slot_id: UUID) -> bool:
        result = await self._session.execute(
            select(AvailabilitySlotModel).where(AvailabilitySlotModel.id == slot_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()
            return True
        return False


class SQLTimeOffRepository:
    """SQL implementation of TimeOffRepository protocol."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, time_off_id: UUID) -> Optional[TimeOff]:
        result = await self._session.execute(
            select(TimeOffModel).where(TimeOffModel.id == time_off_id)
        )
        model = result.scalar_one_or_none()
        return TimeOffMapper.to_domain(model) if model else None
    
    async def list_by_barber(self, barber_id: UUID, start: datetime, end: datetime) -> List[TimeOff]:
        result = await self._session.execute(
            select(TimeOffModel)
            .where(
                and_(
                    TimeOffModel.barber_id == barber_id,
                    TimeOffModel.start_datetime < end,
                    TimeOffModel.end_datetime > start
                )
            )
        )
        models = result.scalars().all()
        return [TimeOffMapper.to_domain(m) for m in models]
    
    async def create(self, time_off: TimeOff) -> TimeOff:
        model = TimeOffMapper.to_model(time_off)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return TimeOffMapper.to_domain(model)
    
    async def update(self, time_off: TimeOff) -> TimeOff:
        result = await self._session.execute(
            select(TimeOffModel).where(TimeOffModel.id == time_off.id)
        )
        model = result.scalar_one()
        
        model.start_datetime = time_off.start_datetime
        model.end_datetime = time_off.end_datetime
        model.reason = time_off.reason
        
        await self._session.commit()
        await self._session.refresh(model)
        return TimeOffMapper.to_domain(model)
    
    async def delete(self, time_off_id: UUID) -> bool:
        result = await self._session.execute(
            select(TimeOffModel).where(TimeOffModel.id == time_off_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()
            return True
        return False


class SQLAppointmentRepository:
    """SQL implementation of AppointmentRepository protocol."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, appointment_id: UUID) -> Optional[Appointment]:
        result = await self._session.execute(
            select(AppointmentModel).where(AppointmentModel.id == appointment_id)
        )
        model = result.scalar_one_or_none()
        return AppointmentMapper.to_domain(model) if model else None
    
    async def list_by_barber(
        self, barber_id: UUID, start: datetime, end: datetime, skip: int = 0, limit: int = 100
    ) -> List[Appointment]:
        result = await self._session.execute(
            select(AppointmentModel)
            .where(
                and_(
                    AppointmentModel.barber_id == barber_id,
                    AppointmentModel.start_time >= start,
                    AppointmentModel.start_time <= end
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(AppointmentModel.start_time)
        )
        models = result.scalars().all()
        return [AppointmentMapper.to_domain(m) for m in models]
    
    async def list_by_client(
        self, client_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Appointment]:
        result = await self._session.execute(
            select(AppointmentModel)
            .where(AppointmentModel.client_id == client_id)
            .offset(skip)
            .limit(limit)
            .order_by(AppointmentModel.start_time.desc())
        )
        models = result.scalars().all()
        return [AppointmentMapper.to_domain(m) for m in models]
    
    async def list_conflicting(
        self, barber_id: UUID, start_time: datetime, end_time: datetime, exclude_id: Optional[UUID] = None
    ) -> List[Appointment]:
        query = select(AppointmentModel).where(
            and_(
                AppointmentModel.barber_id == barber_id,
                AppointmentModel.status != "cancelled",
                AppointmentModel.start_time < end_time,
                AppointmentModel.end_time > start_time
            )
        )
        if exclude_id:
            query = query.where(AppointmentModel.id != exclude_id)
        
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [AppointmentMapper.to_domain(m) for m in models]
    
    async def create(self, appointment: Appointment) -> Appointment:
        model = AppointmentMapper.to_model(appointment)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return AppointmentMapper.to_domain(model)
    
    async def update(self, appointment: Appointment) -> Appointment:
        result = await self._session.execute(
            select(AppointmentModel).where(AppointmentModel.id == appointment.id)
        )
        model = result.scalar_one()
        
        model.barber_id = appointment.barber_id
        model.client_id = appointment.client_id
        model.service_id = appointment.service_id
        model.start_time = appointment.start_time
        model.end_time = appointment.end_time
        model.status = appointment.status.value
        model.notes = appointment.notes
        
        await self._session.commit()
        await self._session.refresh(model)
        return AppointmentMapper.to_domain(model)
    
    async def delete(self, appointment_id: UUID) -> bool:
        result = await self._session.execute(
            select(AppointmentModel).where(AppointmentModel.id == appointment_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()
            return True
        return False


class SQLAuditRepository:
    """SQL implementation of AuditRepository protocol."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, audit_id: UUID) -> Optional[AuditLog]:
        result = await self._session.execute(
            select(AuditLogModel).where(AuditLogModel.id == audit_id)
        )
        model = result.scalar_one_or_none()
        return AuditLogMapper.to_domain(model) if model else None
    
    async def list_by_appointment(self, appointment_id: UUID, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        result = await self._session.execute(
            select(AuditLogModel)
            .where(AuditLogModel.appointment_id == appointment_id)
            .offset(skip)
            .limit(limit)
            .order_by(AuditLogModel.performed_at.desc())
        )
        models = result.scalars().all()
        return [AuditLogMapper.to_domain(m) for m in models]
    
    async def create(self, audit_log: AuditLog) -> AuditLog:
        model = AuditLogMapper.to_model(audit_log)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return AuditLogMapper.to_domain(model)
