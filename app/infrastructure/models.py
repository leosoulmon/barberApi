"""SQLModel database models mapping to domain entities."""
from datetime import datetime, time
from typing import TYPE_CHECKING, Optional, List
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import String, Float, DateTime, Time, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.sqlite import JSON

if TYPE_CHECKING:
    pass


class UserModel(SQLModel, table=True):
    """User database model."""
    __tablename__ = "users"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(sa_column=Column(String(255), unique=True, index=True, nullable=False))
    full_name: str = Field(sa_column=Column(String(255), nullable=False))
    phone: str = Field(sa_column=Column(String(50), default=""))
    hashed_password: str = Field(sa_column=Column(String(255), nullable=False))
    role: str = Field(sa_column=Column(String(20), nullable=False, default="client"))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow))
    updated_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))
    
    # Relationships
    services: List["ServiceModel"] = Relationship(back_populates="barber")  # type: ignore[assignment]
    availability_slots: List["AvailabilitySlotModel"] = Relationship(back_populates="barber")  # type: ignore[assignment]
    time_offs: List["TimeOffModel"] = Relationship(back_populates="barber")  # type: ignore[assignment]
    barber_appointments: List["AppointmentModel"] = Relationship(  # type: ignore[assignment]
        back_populates="barber",
        sa_relationship_kwargs={"foreign_keys": "AppointmentModel.barber_id"}
    )
    client_appointments: List["AppointmentModel"] = Relationship(  # type: ignore[assignment]
        back_populates="client",
        sa_relationship_kwargs={"foreign_keys": "AppointmentModel.client_id"}
    )


class ServiceModel(SQLModel, table=True):
    """Service database model."""
    __tablename__ = "services"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str = Field(sa_column=Column(Text, default=""))
    duration_minutes: int = Field(default=30)
    price: float = Field(sa_column=Column(Float, default=0.0))
    barber_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow))
    updated_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))
    
    # Relationships
    barber: Optional[UserModel] = Relationship(back_populates="services")
    appointments: List["AppointmentModel"] = Relationship(back_populates="service")


class AvailabilitySlotModel(SQLModel, table=True):
    """Availability slot database model."""
    __tablename__ = "availability_slots"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    barber_id: UUID = Field(foreign_key="users.id")
    day_of_week: int = Field(default=1)  # 1=Monday, 7=Sunday
    start_time: time = Field(sa_column=Column(Time, nullable=False))
    end_time: time = Field(sa_column=Column(Time, nullable=False))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow))
    updated_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))
    
    # Relationships
    barber: UserModel = Relationship(back_populates="availability_slots")


class TimeOffModel(SQLModel, table=True):
    """Time-off database model."""
    __tablename__ = "time_offs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    barber_id: UUID = Field(foreign_key="users.id")
    start_datetime: datetime = Field(sa_column=Column(DateTime, nullable=False))
    end_datetime: datetime = Field(sa_column=Column(DateTime, nullable=False))
    reason: str = Field(sa_column=Column(Text, default=""))
    created_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow))
    
    # Relationships
    barber: UserModel = Relationship(back_populates="time_offs")


class AppointmentModel(SQLModel, table=True):
    """Appointment database model."""
    __tablename__ = "appointments"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    barber_id: UUID = Field(foreign_key="users.id")
    client_id: UUID = Field(foreign_key="users.id")
    service_id: UUID = Field(foreign_key="services.id")
    start_time: datetime = Field(sa_column=Column(DateTime, nullable=False, index=True))
    end_time: datetime = Field(sa_column=Column(DateTime, nullable=False))
    status: str = Field(sa_column=Column(String(20), default="booked"))
    notes: str = Field(sa_column=Column(Text, default=""))
    created_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow))
    updated_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow))
    
    # Relationships
    barber: UserModel = Relationship(
        back_populates="barber_appointments",
        sa_relationship_kwargs={"foreign_keys": "AppointmentModel.barber_id"}
    )
    client: UserModel = Relationship(
        back_populates="client_appointments",
        sa_relationship_kwargs={"foreign_keys": "AppointmentModel.client_id"}
    )
    service: ServiceModel = Relationship(back_populates="appointments")
    audit_logs: List["AuditLogModel"] = Relationship(back_populates="appointment")


class AuditLogModel(SQLModel, table=True):
    """Audit log database model."""
    __tablename__ = "audit_logs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    appointment_id: UUID = Field(foreign_key="appointments.id")
    action: str = Field(sa_column=Column(String(50), nullable=False))
    previous_status: Optional[str] = Field(default=None)
    new_status: Optional[str] = Field(default=None)
    performed_by: UUID = Field(foreign_key="users.id")
    performed_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow))
    details: str = Field(sa_column=Column(Text, default=""))
    
    # Relationships
    appointment: AppointmentModel = Relationship(back_populates="audit_logs")
