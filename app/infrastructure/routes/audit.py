"""Audit trail routes."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from ...application.services import AuditService, AppointmentBookingService
from ...application.exceptions import AppointmentNotFoundError
from ..dependencies import get_audit_service, get_appointment_service, get_current_user, require_barber
from ..schemas import AuditLogResponse, AuditLogListResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("/appointments/{appointment_id}/history", response_model=AuditLogListResponse)
async def get_appointment_history(
    appointment_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service),
    appointment_service: AppointmentBookingService = Depends(get_appointment_service)
):
    """Get audit history for an appointment."""
    try:
        # Verify appointment exists and user has access
        appointment = await appointment_service.get_appointment(appointment_id)
        
        # Only barber, client, or admin can view history
        user_id = UUID(current_user["user_id"])
        if (
            user_id != appointment.barber_id and
            user_id != appointment.client_id and
            current_user["role"] not in ["barber"]
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        history = await audit_service.list_appointment_history(appointment_id, skip, limit)
        return AuditLogListResponse(
            items=[AuditLogResponse.model_validate(h) for h in history],
            total=len(history)
        )
    except AppointmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")


@router.get("/appointments/{appointment_id}/history/{audit_id}", response_model=AuditLogResponse)
async def get_audit_entry(
    appointment_id: UUID,
    audit_id: UUID,
    current_user: dict = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Get specific audit entry."""
    try:
        entry = await audit_service.get_audit_entry(audit_id)
        if str(entry.appointment_id) != str(appointment_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit entry not found")
        return AuditLogResponse.model_validate(entry)
    except AppointmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit entry not found")
