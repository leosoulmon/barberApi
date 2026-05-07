"""User management routes."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from ...domain.entities import User, UserRole
from ...application.services import UserService
from ...application.exceptions import UserNotFoundError, DuplicateEmailError
from ..dependencies import (
    get_user_service, get_current_user, require_barber, get_password_hash
)
from ..schemas import (
    UserResponse, UserCreate, UserUpdate, UserListResponse
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    role: str = Query(None, pattern="^(barber|client)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(require_barber),
    user_service: UserService = Depends(get_user_service)
):
    """List users (barbers only)."""
    users = await user_service.list_users(role=role, skip=skip, limit=limit)
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=len(users)
    )


@router.get("/barbers", response_model=UserListResponse)
async def list_barbers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_service: UserService = Depends(get_user_service)
):
    """List all barbers (public endpoint)."""
    barbers = await user_service.list_barbers(skip=skip, limit=limit)
    return UserListResponse(
        items=[UserResponse.model_validate(b) for b in barbers],
        total=len(barbers)
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID."""
    try:
        user = await user_service.get_user(user_id)
        return UserResponse.model_validate(user)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update user."""
    try:
        # Only allow updating own profile or barbers updating any user
        if str(user_id) != current_user["user_id"] and current_user["role"] != UserRole.BARBER.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        user = await user_service.get_user(user_id)
        
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.phone is not None:
            user.phone = user_update.phone
        if user_update.is_active is not None:
            # Only barbers can change active status
            if current_user["role"] != UserRole.BARBER.value:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
            user.is_active = user_update.is_active
        
        updated = await user_service.update_user(user)
        return UserResponse.model_validate(updated)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: dict = Depends(require_barber),
    user_service: UserService = Depends(get_user_service)
):
    """Delete user (barbers only)."""
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None
