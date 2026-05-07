"""FastAPI dependencies for dependency injection."""
import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import User, UserRole
from ..application.services import (
    UserService, ServiceCatalogService, AvailabilityService, AppointmentBookingService, AuditService
)
from .database import get_session
from .repositories import (
    SQLUserRepository, SQLServiceRepository, SQLAvailabilityRepository,
    SQLTimeOffRepository, SQLAppointmentRepository, SQLAuditRepository
)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        if user_id is None:
            raise credentials_exception
        return {"user_id": user_id, "email": email, "role": role}
    except JWTError:
        raise credentials_exception


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Ensure current user is active."""
    return current_user


def require_barber(current_user: dict = Depends(get_current_user)) -> dict:
    """Require user to be a barber."""
    if current_user.get("role") != UserRole.BARBER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Barber role required"
        )
    return current_user


def require_client(current_user: dict = Depends(get_current_user)) -> dict:
    """Require user to be a client."""
    if current_user.get("role") != UserRole.CLIENT.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client role required"
        )
    return current_user


# Repository dependencies
async def get_user_repository(session: AsyncSession = Depends(get_session)):
    """Get user repository."""
    return SQLUserRepository(session)


async def get_service_repository(session: AsyncSession = Depends(get_session)):
    """Get service repository."""
    return SQLServiceRepository(session)


async def get_availability_repository(session: AsyncSession = Depends(get_session)):
    """Get availability repository."""
    return SQLAvailabilityRepository(session)


async def get_time_off_repository(session: AsyncSession = Depends(get_session)):
    """Get time-off repository."""
    return SQLTimeOffRepository(session)


async def get_appointment_repository(session: AsyncSession = Depends(get_session)):
    """Get appointment repository."""
    return SQLAppointmentRepository(session)


async def get_audit_repository(session: AsyncSession = Depends(get_session)):
    """Get audit repository."""
    return SQLAuditRepository(session)


# Service dependencies
async def get_user_service(
    user_repo=Depends(get_user_repository)
) -> UserService:
    """Get user service."""
    return UserService(user_repo)


async def get_service_catalog_service(
    service_repo=Depends(get_service_repository),
    user_repo=Depends(get_user_repository)
) -> ServiceCatalogService:
    """Get service catalog service."""
    return ServiceCatalogService(service_repo, user_repo)


async def get_availability_service(
    availability_repo=Depends(get_availability_repository),
    time_off_repo=Depends(get_time_off_repository),
    user_repo=Depends(get_user_repository)
) -> AvailabilityService:
    """Get availability service."""
    return AvailabilityService(availability_repo, time_off_repo, user_repo)


async def get_appointment_service(
    appointment_repo=Depends(get_appointment_repository),
    service_repo=Depends(get_service_repository),
    availability_service=Depends(get_availability_service),
    audit_repo=Depends(get_audit_repository)
) -> AppointmentBookingService:
    """Get appointment booking service."""
    return AppointmentBookingService(
        appointment_repo, service_repo, availability_service, audit_repo
    )


async def get_audit_service(
    audit_repo=Depends(get_audit_repository)
) -> AuditService:
    """Get audit service."""
    return AuditService(audit_repo)
