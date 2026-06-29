'''
This is the SQLAlchemy model for the Referrals table

So my modeling decisions as follows:
- The UUID PK is a uuid instead of auto incrementing to make it more secure to have in the APIs and also harder to guess IDs
- referring_provider_id and referred_provider_id both use RESTRICT on delete since having a history of the referrals is meaningful data so deleting a provider that has referrals attached to them should require more effort. Instead of deleting an inactive provider, we could also move their status to inactive so we still have the history.
- patient_ref can be whatever string. This is mainly due to having fake patients, in production I think the Patient ID would be a UUID or a member id that has a set format.
- icd10_code is capped at 10 characters since the maximum length of a valid code is 10 characters
- created_by/updated_by use SET NULL so referral records survive even if a user is deleted. 
- updated_at automatically updates on every SQLAlchemy's onupdate hook so it never has to be manually set
'''
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referring_provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("providers.id", ondelete="RESTRICT"), nullable=False)
    referred_provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("providers.id", ondelete="RESTRICT"), nullable=False)
    patient_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    icd10_code: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))