'''
This is the main file where the app is created and the routes are laid out
'''
import json
from jwt.algorithms import RSAAlgorithm
from fastapi import FastAPI
from config import settings
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter
from app.routers.auth import router as auth_router
from app.routers.providers import router as providers_router
from app.routers.referrals import router as referrals_router
from keys import all_public_keys

app = FastAPI()

'''
The CORS middleware shows localhost:5173 because this is the frontend url. I have it pulling from the config, with a default of the localhost:5173, mainly so I didn't have to create another .env value. In a real development environment there would be no default
'''
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(auth_router, prefix="/auth")
app.include_router(providers_router, prefix="/providers")
app.include_router(referrals_router, prefix="/referrals", tags=["referrals"])

@app.get("/health")
async def root():
    return {"message": "I'm healthy"}

@app.get("/.well-known/jwks.json")
async def jwks():
    keys = []
    for kid, public_key in all_public_keys().items():
        jwk = json.loads(RSAAlgorithm.to_jwk(public_key))
        jwk["kid"] = kid
        jwk["use"] = "sig"
        keys.append(jwk)
    return {"keys": keys}