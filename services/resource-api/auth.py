'''
This file is for helper functions to create two different types of JWTs

Access Token: Used by the user to interact with the Provider APIs and Referral APIs

Service Token: Used by the verification service when verifying an NPI on Provider Creation
'''

import jwt
from datetime import datetime, timezone, timedelta
from config import settings

'''
This function creates a simple access token in JWT format for a user
'''
def create_access_token(data: dict) -> str:
    payload = {
        **data,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=3600),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

'''
This function created a service token to access the verification service APIs in JWT format. It's signed with a SERVICE_JWT_SECRET (separate from the other JWT secret), and includes the iss and aud since those are two values that the verification service validates. Also the token expires after 5 minutes so they are short lived.
'''
def create_service_token() -> str:
    payload = {
        "iss": "resource-api",
        "aud": "verification-svc",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    return jwt.encode(payload, settings.service_jwt_secret, algorithm="HS256")