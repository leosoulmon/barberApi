"""Availability and time-off management routes."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime

from ...domain.entities import AvailabilitySlot, WeekDay, TimeOff
from ...application.services import AvailabilityService
from ...application.exceptions import ServiceNotFoundError, BarberNotAvailableError
from ..dependencies import get_availability_service, get_current_user, require_barber
from ..schemas import (
    AvailabilitySlotResponse, AvailabilitySlotCreate, AvailabilitySlotUpdate,
    AvailabilityListResponse, TimeOffResponse, TimeOffCreate, TimeOffUpdate,
    TimeOffListResponse
)

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.get("/barbers/{barber_id}", response_model=AvailabilityListResponse)
async def get_barber_availability(
    barber_id: UUID,
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """Get availability slots for a barber."""
    slots = await availability_service.list_barber_availability(barber_id)
    return AvailabilityListResponse(
        items=[AvailabilitySlotResponse.model_validate(s) for s in slots],
        total=len(slots)
    )


@router.post("/slots", response_model=AvailabilitySlotResponse, status_code=status.HTTP_201_CREATED)
async def create_availability_slot(
    slot_create: AvailabilitySlotCreate,
    current_user: dict = Depends(require_barber),
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """Create an availability slot (barbers only)."""
    slot = AvailabilitySlot(
        barber_id=slot_create.barber_id,
        day_of_week=WeekDay(slot_create.day_of_week),
        start_time=slot_create.start_time,
        end_time=slot_create.end_time,
        is_active=slot_create.is_active
    )
    created = await availability_service.create_availability(slot)
    return AvailabilitySlotResponse.model_validate(created)


@router.put("/slots/{slot_id}", response_model=AvailabilitySlotResponse)
async def update_availability_slot(
    slot_id: UUID,
    slot_update: AvailabilitySlotUpdate,
    current_user: dict = Depends(require_barber),
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """Update an availability slot (barbers only)."""
    try:
        slot = await availability_service.get_availability(slot_id)
        
        if slot_update.day_of_week is not None:
            slot.day_of_week = WeekDay(slot_update.day_of_week)
        if slot_update.start_time is not None:
            slot.start_time = slot_update.start_time
        if slot_update.end_time is not None:
            slot.end_time = slot_update.end_time
        if slot_update.is_active is not None:
            slot.is_active = slot_update.is_active
        
        updated = await availability_service.update_availability(slot)
        return AvailabilitySlotResponse.model_validate(updated)
    except ServiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability slot not found")


@router.delete("/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_availability_slot(
    slot_id: UUID,
    current_user: dict = Depends(require_barber),
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """Delete an availability slot (barbers only)."""
    success = await availability_service.delete_availability(slot_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability slot not found")
    return None


@router.get("/barbers/{barber_id}/check", response_model=dict)
async def check_availability(
    barber_id: UUID,
    start_time: datetime,
    end_time: datetime,
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """Check if barber is available at specific time range."""
    is_available = await availability_service.is_barber_available(
        barber_id, start_time, end_time
    )
    return {"barber_id": str(barber_id), "start_time": start_time, "end_time": end_time, "is_available": is_available}


# Time-off routes
@router.get("/barbers/{barber_id}/time-off", response_model=TimeOffListResponse)
async def list_time_off(
    barber_id: UUID,
    start: datetime = Query(None),
    end: datetime = Query(None),
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """List time-off entries for a barber."""
    if not start:
        start = datetime.utcnow()
    if not end:
        end = datetime.utcnow().replace(year=datetime.utcnow().year + 1)
    
    from ..repositories import SQLTimeOffRepository
    # Need to access time_off_repo through service - adding a method or using internals
    time_offs = await availability_service._time_off_repo.list_by_barber(barber_id, start, end)
    
    return TimeOffListResponse(
        items=[TimeOffResponse.model_validate(t) for t in time_offs],
        total=len(time_offs)
    )


@router.post("/time-off", response_model=TimeOffResponse, status_code=status.HTTP_201_CREATED)
async def create_time_off(
    time_off_create: TimeOffCreate,
    current_user: dict = Depends(require_barber),
    availability_service: AvailabilityService = Depends(get_availability_service)
):
    """Create a time-off entry (barbers only)."""
    time_off = TimeOff(
        barber_id=time_off_create.barber_id,
        start_datetime=time_off_create.start_datetime,
        end_datetime=time_off_create.end_datetime,
        reason=time_off_create.reason
    )
    created = await availability_service._time_off_repo.create(time_off)
    return TimeOffResponse.model_validate(created)
