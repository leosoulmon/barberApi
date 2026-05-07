"""Authentication routes."""
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ...domain.entities import User, UserRole
from ...application.services import UserService
from ...application.exceptions import InvalidCredentialsError, DuplicateEmailError
from ..dependencies import (
    get_user_service, create_access_token, get_password_hash, verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
)
from ..schemas import Token, UserResponse, UserCreate

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """Register a new user."""
    user = User(
        email=user_create.email,
        full_name=user_create.full_name,
        phone=user_create.phone,
        hashed_password=get_password_hash(user_create.password),
        role=UserRole(user_create.role)
    )
    try:
        created_user = await user_service.create_user(user)
    except DuplicateEmailError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    return UserResponse.model_validate(created_user)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    """Login and get access token."""
    user = await user_service.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get current user information."""
    user = await user_service.get_user(UUID(current_user["user_id"]))
    return UserResponse.model_validate(user)
