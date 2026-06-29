'''
This file is for the API creation of the endpoints that involve CRUD operations for Providers
'''

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid
import httpx

from app.database import get_db
from app.models.provider import Provider
from app.models.user import User
from deps import get_current_user, require_admin
from auth import create_service_token
from config import settings

router = APIRouter()

class ProviderCreate(BaseModel):
    npi: str
    name: str
    taxonomy: str
    specialty: str
    accepting_new_patients: bool = True
    region: Optional[str] = None
    state: Optional[str] = None

class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    taxonomy: Optional[str] = None
    specialty: Optional[str] = None
    accepting_new_patients: Optional[bool] = None
    status: Optional[str] = None
    region: Optional[str] = None
    state: Optional[str] = None

class ProviderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    npi: str
    name: str
    taxonomy: str
    specialty: str
    status: str
    accepting_new_patients: bool
    region: Optional[str] = None
    state: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

class PaginatedProviders(BaseModel):
    data: list[ProviderOut]
    pagination: dict

'''
This API is a GET request that just lists all the providers with pagination
'''
@router.get("", response_model=PaginatedProviders)
async def list_providers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    specialty: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Provider)
    count_query = select(func.count()).select_from(Provider)

    if specialty:
        query = query.where(Provider.specialty.ilike(f"%{specialty}%"))
        count_query = count_query.where(Provider.specialty.ilike(f"%{specialty}%"))
    if status:
        query = query.where(Provider.status == status)
        count_query = count_query.where(Provider.status == status)

    total = await db.scalar(count_query)
    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    providers = result.scalars().all()

    return {
        "data": providers,
        "pagination": {"page": page, "limit": limit, "total": total, "hasMore": (offset + limit) < total}
    }

'''
This API is a GET request that allows you to get a single provider by ID
'''
@router.get("/{provider_id}", response_model=ProviderOut)
async def get_provider(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Provider).where(Provider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider

'''
This API is a POST request to create a provider. This requires authentication and an admin role to use. The status defaults to active (the thought process was someone wasn't going to upload an inactive provider), and then just accepts the model values. Something to add here is that this is the passthrough to test the verification service api as well.
'''
@router.post("", status_code=201, response_model=ProviderOut)
async def create_provider(
    body: ProviderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = await db.execute(select(Provider).where(Provider.npi == body.npi))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="NPI already exists")

    token = create_service_token()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.verification_svc_url}/verify/{body.npi}",
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=422, detail="NPI verification failed")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Verification service unavailable")

    provider = Provider(
        **body.model_dump(),
        status="active",
        verified_at=datetime.now(timezone.utc),
        created_by=current_user.id,
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    return provider

'''
This API is a PATCH request that allows you to update just about every value except npi, verified at, id, created_at and created by. It's using the ProviderUpdate class to figure out what is allowed to be updated. This is an authenticated endpoint that requires an admin role.
'''
@router.patch("/{provider_id}", status_code=200,  response_model=ProviderOut)
async def update_provider(
    provider_id: uuid.UUID,
    body: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Provider).where(Provider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(provider, field, value)
    provider.updated_by = current_user.id
    provider.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(provider)
    return provider


'''
This API is a DELETE request to delete a provider by ID. This is an authenticated endpoint that requires an admin role
'''
@router.delete("/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Provider).where(Provider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    await db.delete(provider)
    await db.commit()
