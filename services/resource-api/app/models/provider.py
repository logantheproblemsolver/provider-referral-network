'''
This is the SQLAlchemy model

So my modeling decisions as follows:
- The UUID PK is a uuid instead of auto incrementing to make it more secure to have in the APIs and also harder to guess IDs
- NPI needs to be unique since in real production a provider should not have a duplicate NPI. It's also immutable since it shoudln't change after creation (per my understanding of the NPI)
- status is defaulted to active mainly because my assumption is that no one is creating an inactive provider
- verified_at is NULLABLE because of the seed data. The seed data didn't run through the verification service due to having "trust" in the file and also I didn't want to update the seed data
- created_by/updated_by use SET NULL so provider records survive even if a user is deleted.
- updated_at automatically updates on every SQLAlchemy's onupdate hook so it never has to be manually set
'''
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    npi: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    taxonomy: Mapped[str] = mapped_column(String(20), nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    accepting_new_patients: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))