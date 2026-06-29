'''
This file is the SQLAlchemy model for the Users table

So my modeling decisions as follows:
- The UUID PK is a uuid instead of auto incrementing to make it more secure to have in the APIs and also harder to guess IDs
- email is unique so then users can't have multiple accounts
- password_hash stores bcrypt hashed passwords for local auth users while for OIDC users it'll be an empty string
- role will default to user since we don't want the default to be admin for security reasons. We only add an admin through a function on the server if there are no users in the db
- no updated_field since there's currently no way to edit a user for this POC. In a real applicaiton I would add an updated field and allow them to edit their data in the frontend
'''
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
