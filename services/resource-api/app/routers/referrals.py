'''
This API file is for the referral management system. All referral endpoints require authentication and either user or admin role can access any of the APIs.
'''

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid
from datetime import datetime, timezone

from app.database import get_db
from app.models.referral import Referral
from app.models.provider import Provider
from app.models.user import User
from deps import get_current_user

router = APIRouter()

VALID_STATUSES = {"pending", "accepted", "rejected"}

class ReferralCreate(BaseModel):
    referring_provider_id: uuid.UUID
    referred_provider_id: uuid.UUID
    patient_ref: str
    icd10_code: str
    notes: Optional[str] = None

class ReferralStatusUpdate(BaseModel):
    status: str

class ReferralOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    referring_provider_id: uuid.UUID
    referred_provider_id: uuid.UUID
    patient_ref: str
    icd10_code: str
    status: str
    notes: Optional[str] = None
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

class PaginatedReferrals(BaseModel):
    data: list[ReferralOut]
    pagination: dict


'''
This API is a GET request that gets all referrals that have been created. The API supports pagination and also filtering by status
'''
@router.get("", response_model=PaginatedReferrals)
async def list_referrals(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Referral)
    count_query = select(func.count()).select_from(Referral)

    if status:
        query = query.where(Referral.status == status)
        count_query = count_query.where(Referral.status == status)

    total = await db.scalar(count_query)
    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    referrals = result.scalars().all()

    return {
        "data": referrals,
        "pagination": {"page": page, "limit": limit, "total": total, "hasMore": (offset + limit) < total},
    }

'''
This API is a POST request that is used to create referrals, and the body of the request is based off of the ReferralCreate class. Both providers are are validated before creating the referral.
'''
@router.post("", status_code=201, response_model=ReferralOut)
async def create_referral(
    body: ReferralCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for provider_id in (body.referring_provider_id, body.referred_provider_id):
        result = await db.execute(select(Provider).where(Provider.id == provider_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

    referral = Referral(
        **body.model_dump(),
        status="pending",
        created_by=current_user.id,
    )
    db.add(referral)
    await db.commit()
    await db.refresh(referral)
    return referral

'''
This API is a PATCH request that updates referrals by ID. Currently the only field that can be updated is the status field. It also makes sure that the status that's being updated is currently a valid status before we save to the DB. In production I'd probably update it to also do patients, but until Patients are real it wasn't worth building a patient verifier and creating fake PHI data for this coding challenge (I could if you'd like though)
'''
@router.patch("/{referral_id}", response_model=ReferralOut)
async def update_referral_status(
    referral_id: uuid.UUID,
    body: ReferralStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {sorted(VALID_STATUSES)}")

    result = await db.execute(select(Referral).where(Referral.id == referral_id))
    referral = result.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    referral.status = body.status
    referral.updated_by = current_user.id
    referral.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(referral)
    return referral
