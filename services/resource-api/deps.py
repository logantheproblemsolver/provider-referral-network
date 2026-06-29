'''
This file holds functions that will be used as dependencies on the API
'''
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from config import settings

bearer_scheme = HTTPBearer()

'''
This function will take the access token, and decode the token, then look at the db for the user to get the user information for the APIs

The error code is a 401 here instead of a 403 so the error doesn't accidentally leak whether a user id exists or not
'''
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


'''
This function takes the current user with the get current user function and then checks if that user is an admin or not

The function here sends a 403 and not a 401 because a 401 means not authenticated while a 403 means that the user is authenticated, but not allowed
'''
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return current_user
