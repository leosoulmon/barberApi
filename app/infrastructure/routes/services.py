"""Service catalog routes."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from ...domain.entities import Service
from ...application.services import ServiceCatalogService
from ...application.exceptions import ServiceNotFoundError
from ..dependencies import get_service_catalog_service, get_current_user, require_barber
from ..schemas import (
    ServiceResponse, ServiceCreate, ServiceUpdate, ServiceListResponse
)

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=ServiceListResponse)
async def list_services(
    barber_id: UUID = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service_service: ServiceCatalogService = Depends(get_service_catalog_service)
):
    """List services."""
    if barber_id:
        services = await service_service.list_barber_services(barber_id, skip, limit)
    else:
        services = await service_service.list_active_services(skip, limit)
    
    return ServiceListResponse(
        items=[ServiceResponse.model_validate(s) for s in services],
        total=len(services)
    )


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: UUID,
    service_service: ServiceCatalogService = Depends(get_service_catalog_service)
):
    """Get service by ID."""
    try:
        service = await service_service.get_service(service_id)
        return ServiceResponse.model_validate(service)
    except ServiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_create: ServiceCreate,
    current_user: dict = Depends(require_barber),
    service_service: ServiceCatalogService = Depends(get_service_catalog_service)
):
    """Create a new service (barbers only)."""
    service = Service(
        name=service_create.name,
        description=service_create.description,
        duration_minutes=service_create.duration_minutes,
        price=service_create.price,
        barber_id=service_create.barber_id or UUID(current_user["user_id"]),
        is_active=service_create.is_active
    )
    created = await service_service.create_service(service)
    return ServiceResponse.model_validate(created)


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: UUID,
    service_update: ServiceUpdate,
    current_user: dict = Depends(require_barber),
    service_service: ServiceCatalogService = Depends(get_service_catalog_service)
):
    """Update a service (barbers only)."""
    try:
        service = await service_service.get_service(service_id)
        
        if service_update.name is not None:
            service.name = service_update.name
        if service_update.description is not None:
            service.description = service_update.description
        if service_update.duration_minutes is not None:
            service.duration_minutes = service_update.duration_minutes
        if service_update.price is not None:
            service.price = service_update.price
        if service_update.is_active is not None:
            service.is_active = service_update.is_active
        
        updated = await service_service.update_service(service)
        return ServiceResponse.model_validate(updated)
    except ServiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: UUID,
    current_user: dict = Depends(require_barber),
    service_service: ServiceCatalogService = Depends(get_service_catalog_service)
):
    """Delete a service (barbers only)."""
    success = await service_service.delete_service(service_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return None
