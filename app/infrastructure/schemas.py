"""Pydantic schemas for API request/response validation."""
from __future__ import annotations

from datetime import datetime, time
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


# Base schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(default="", max_length=50)
    role: str = Field(default="client", pattern="^(barber|client)$")
    is_active: bool = True


class ServiceBase(BaseModel):
    """Base service schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    duration_minutes: int = Field(..., ge=5, le=480)
    price: float = Field(..., ge=0)
    is_active: bool = True


class AvailabilitySlotBase(BaseModel):
    """Base availability slot schema."""
    day_of_week: int = Field(..., ge=1, le=7)
    start_time: time
    end_time: time
    is_active: bool = True
    
    @field_validator('end_time')
    @classmethod
    def end_time_after_start(cls, v: time, info) -> time:
        values = info.data
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class TimeOffBase(BaseModel):
    """Base time-off schema."""
    start_datetime: datetime
    end_datetime: datetime
    reason: str = ""
    
    @field_validator('end_datetime')
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        values = info.data
        if 'start_datetime' in values and v <= values['start_datetime']:
            raise ValueError('end_datetime must be after start_datetime')
        return v


class AppointmentBase(BaseModel):
    """Base appointment schema."""
    start_time: datetime
    notes: str = ""


class AuditLogBase(BaseModel):
    """Base audit log schema."""
    action: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    details: str = ""


# Request schemas
class UserCreate(UserBase):
    """Create user request."""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """Update user request."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class ServiceCreate(ServiceBase):
    """Create service request."""
    barber_id: Optional[UUID] = None


class ServiceUpdate(BaseModel):
    """Update service request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=5, le=480)
    price: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class AvailabilitySlotCreate(AvailabilitySlotBase):
    """Create availability slot request."""
    barber_id: UUID


class AvailabilitySlotUpdate(BaseModel):
    """Update availability slot request."""
    day_of_week: Optional[int] = Field(None, ge=1, le=7)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_active: Optional[bool] = None


class TimeOffCreate(TimeOffBase):
    """Create time-off request."""
    barber_id: UUID


class TimeOffUpdate(BaseModel):
    """Update time-off request."""
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    reason: Optional[str] = None


class AppointmentCreateRequest(BaseModel):
    """Create appointment request."""
    barber_id: UUID
    service_id: UUID
    start_time: datetime
    notes: str = ""
    
    @field_validator('start_time')
    @classmethod
    def start_time_not_in_past(cls, v: datetime) -> datetime:
        if v < datetime.utcnow():
            raise ValueError('Cannot book appointments in the past')
        return v


class AppointmentRescheduleRequest(BaseModel):
    """Reschedule appointment request."""
    new_start_time: datetime
    
    @field_validator('new_start_time')
    @classmethod
    def start_time_not_in_past(cls, v: datetime) -> datetime:
        if v < datetime.utcnow():
            raise ValueError('Cannot reschedule to a time in the past')
        return v


class AppointmentCancelRequest(BaseModel):
    """Cancel appointment request."""
    reason: str = ""


# Response schemas
class UserResponse(UserBase):
    """User response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime


class ServiceResponse(ServiceBase):
    """Service response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    barber_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class AvailabilitySlotResponse(AvailabilitySlotBase):
    """Availability slot response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    barber_id: UUID
    created_at: datetime
    updated_at: datetime


class TimeOffResponse(TimeOffBase):
    """Time-off response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    barber_id: UUID
    created_at: datetime


class AppointmentResponse(BaseModel):
    """Appointment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    barber_id: UUID
    client_id: UUID
    service_id: UUID
    start_time: datetime
    end_time: datetime
    status: str
    notes: str
    created_at: datetime
    updated_at: datetime


class AppointmentDetailResponse(AppointmentResponse):
    """Appointment detail response with related data."""
    barber: Optional[UserResponse] = None
    client: Optional[UserResponse] = None
    service: Optional[ServiceResponse] = None


class AuditLogResponse(AuditLogBase):
    """Audit log response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    appointment_id: UUID
    performed_by: UUID
    performed_at: datetime


# Token schemas
class Token(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data payload."""
    user_id: Optional[str] = None


# List response schemas
class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[BaseModel]
    total: int
    skip: int
    limit: int


class UserListResponse(BaseModel):
    """User list response."""
    items: List[UserResponse]
    total: int


class ServiceListResponse(BaseModel):
    """Service list response."""
    items: List[ServiceResponse]
    total: int


class AppointmentListResponse(BaseModel):
    """Appointment list response."""
    items: List[AppointmentResponse]
    total: int


class AuditLogListResponse(BaseModel):
    """Audit log list response."""
    items: List[AuditLogResponse]
    total: int


class AvailabilityListResponse(BaseModel):
    """Availability list response."""
    items: List[AvailabilitySlotResponse]
    total: int


class TimeOffListResponse(BaseModel):
    """Time-off list response."""
    items: List[TimeOffResponse]
    total: int


# Slot availability query
class AvailableSlotsRequest(BaseModel):
    """Request for available slots query."""
    barber_id: UUID
    date: datetime
    service_id: UUID
