"""Appointment booking routes."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime

from ...domain.entities import Appointment, AppointmentStatus
from ...application.services import AppointmentBookingService
from ...application.exceptions import (
    AppointmentNotFoundError, AppointmentConflictError,
    InvalidAppointmentTimeError, BarberNotAvailableError,
    ServiceNotFoundError
)
from ..dependencies import get_appointment_service, get_current_user, require_barber
from ..schemas import (
    AppointmentResponse, AppointmentCreateRequest, AppointmentRescheduleRequest,
    AppointmentCancelRequest, AppointmentListResponse, AppointmentDetailResponse
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.get("", response_model=AppointmentListResponse)
async def list_appointments(
    barber_id: UUID = Query(None),
    client_id: UUID = Query(None),
    start: datetime = Query(None),
    end: datetime = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    appointment_service: AppointmentBookingService = Depends(get_appointment_service)
):
    """List appointments with filters."""
    if barber_id and start and end:
        # Barber schedule view
        appointments = await appointment_service.list_barber_appointments(
            barber_id, start, end, skip, limit
        )
    elif client_id:
        # Client's appointments
        appointments = await appointment_service.list_client_appointments(
            client_id, skip, limit
        )
    elif barber_id:
        # All appointments for a barber (default range)
        if not start:
            start = datetime.utcnow()
        if not end:
            end = datetime.utcnow().replace(year=datetime.utcnow().year + 1)
        appointments = await appointment_service.list_barber_appointments(
            barber_id, start, end, skip, limit
        )
    else:
        # Default: show current user's appointments
        user_id = UUID(current_user["user_id"])
        appointments = await appointment_service.list_client_appointments(
            user_id, skip, limit
        )
    
    return AppointmentListResponse(
        items=[AppointmentResponse.model_validate(a) for a in appointments],
        total=len(appointments)
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: UUID,
    current_user: dict = Depends(get_current_user),
    appointment_service: AppointmentBookingService = Depends(get_appointment_service)
):
    """Get appointment by ID."""
    try:
        appointment = await appointment_service.get_appointment(appointment_id)
        return AppointmentResponse.model_validate(appointment)
    except AppointmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    appointment_request: AppointmentCreateRequest,
    current_user: dict = Depends(get_current_user),
    appointment_service: AppointmentBookingService = Depends(get_appointment_service)
):
    """Book a new appointment."""
    appointment = Appointment(
        barber_id=appointment_request.barber_id,
        client_id=UUID(current_user["user_id"]),
        service_id=appointment_request.service_id,
        start_time=appointment_request.start_time,
        notes=appointment_request.notes,
        status=AppointmentStatus.BOOKED
    )
    
    try:
        created = await appointment_service.book_appointment(
            appointment, UUID(current_user["user_id"])
        )
        return AppointmentResponse.model_validate(created)
    except AppointmentConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidAppointmentTimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BarberNotAvailableError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ServiceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{appointment_id}/complete", response_model=AppointmentResponse)
async def complete_appointment(
    appointment_id: UUID,
    current_user: dict = Depends(require_barber),
    appointment_service: AppointmentBookingService = Depends(get_appointment_service)
):
    """Mark appointment as completed (barbers only)."""
    try:
        completed = await appointment_service.complete_appointment(
            appointment_id, UUID(current_user["user_id"])
        )
        return AppointmentResponse.model_validate(completed)
    except AppointmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    except InvalidAppointmentTimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: UUID,
    cancel_request: AppointmentCancelRequest,
    current_user: dict = Depends(get_current_user),
    appointment_service: AppointmentBookingService = Depends(get_appointment_service)
):
    """Cancel an appointment."""
    try:
        cancelled = await appointment_service.cancel_appointment(
            appointment_id, UUID(current_user["user_id"]), cancel_request.reason
        )
        return AppointmentResponse.model_validate(cancelled)
    except AppointmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    except InvalidAppointmentTimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    appointment_id: UUID,
    reschedule_request: AppointmentRescheduleRequest,
    current_user: dict = Depends(get_current_user),
    appointment_service: AppointmentBookingService = Depends(get_appointment_service)
):
    """Reschedule an appointment."""
    try:
        rescheduled = await appointment_service.reschedule_appointment(
            appointment_id, reschedule_request.new_start_time, UUID(current_user["user_id"])
        )
        return AppointmentResponse.model_validate(rescheduled)
    except AppointmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    except AppointmentConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidAppointmentTimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BarberNotAvailableError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ServiceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
