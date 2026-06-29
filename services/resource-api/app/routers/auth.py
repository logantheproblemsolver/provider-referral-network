'''
This file is for the routers that relate to authentication/user management APIs.
'''
import bcrypt
import httpx
import jwt
import uuid
from jwt import PyJWKClient
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr, ConfigDict
from app.database import get_db
from app.models.user import User
from auth import create_access_token
from config import settings
from deps import get_current_user
from limiter import limiter
from fastapi import Request

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class OIDCLogin(BaseModel):
    id_token: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: str

class RegisterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: str
    role: str

'''
This API is a GET request that just gets user information to the frontend so we know if the user is an admin or not
'''
@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
    }

'''
This API is a POST request that is used to register a user manually with a manual login and not an OIDC login. Something to note, for this POC I have made it to where the first user to register (or login with OIDC) are the admin. Something I thought about doing was making the roles based on the OIDC, but the issue was that I wanted to keep the user management on the server side and not depend on the OIDC which is why there's also a login portion as well.
'''
@router.post("/register", status_code=201, response_model=RegisterOut)
@limiter.limit("5/minute")
async def register(
    request: Request, 
    body: RegisterRequest, 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    count = await db.scalar(select(func.count()).select_from(User))
    role = "admin" if count == 0 else "user"

    user = User(email=body.email, password_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode(), role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"user_id": user.id, "email": user.email, "role": user.role}


'''
This API is a POST request used to login users that aren't logging in through OIDC. I kept this option to have a login system and show simple identity management through two different ways
'''
@router.post("/login", response_model=TokenOut)
@limiter.limit("5/minute")
async def login(
    request: Request, 
    body: LoginRequest, 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not bcrypt.checkpw(body.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

'''
This API is a POST request to send the OIDC ID token to the resource api application so then we can create our own access token and also see what user just signed in. This gets the JWKS from the keycloak to validate the JWT and also the verify_aud is false due to this being a POC. In production I would verify the audience which for keycloak is the client id.
'''
@router.post("/oidc", response_model=TokenOut)
@limiter.limit("5/minute")
async def oidc_login(
    request: Request,
    body: OIDCLogin,
    db: AsyncSession = Depends(get_db),
):
    try:
        async with httpx.AsyncClient() as client:
            discovery = await client.get(settings.oidc_url)
            discovery.raise_for_status()
            jwks_uri = discovery.json()["jwks_uri"]
        jwks_client = PyJWKClient(jwks_uri)
        signing_key = jwks_client.get_signing_key_from_jwt(body.id_token)
        claims = jwt.decode(
            body.id_token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Identity provider unavailable")
    except (jwt.InvalidTokenError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid ID token")
    email = claims.get("email")
    if not email:
        raise HTTPException(status_code=422, detail="ID token missing email claim")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        count = await db.scalar(select(func.count()).select_from(User))
        user = User(
          email=email,
          password_hash="",
          role="admin" if count == 0 else "user",
      )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


