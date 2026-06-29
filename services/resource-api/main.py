'''
This is the main file where the app is created and the routes are laid out
'''
from fastapi import FastAPI
from config import settings
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers.providers import router as providers_router
from app.routers.referrals import router as referrals_router


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
app.include_router(auth_router, prefix="/auth")
app.include_router(providers_router, prefix="/providers")
app.include_router(referrals_router, prefix="/referrals", tags=["referrals"])

@app.get("/")
async def root():
    return {"message": "Hello World"}

