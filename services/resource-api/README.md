# resource-api

The main API service. Owns providers, referrals, users, authentication, and OIDC integration.

## Stack
- FastAPI (Python 3.11)
- SQLAlchemy async + asyncpg
- Alembic migrations
- PostgreSQL

## Running locally
```bash
pip install -r requirements.txt
PYTHONPATH=. alembic upgrade head
python seed.py
uvicorn main:app --reload --port 8000
```

## Running via Docker
```bash
docker compose up resource-api
```

## Environment variables
- `JWT_SECRET` — signs user JWTs (HS256)
- `DATABASE_URL` — PostgreSQL connection string
- `VERIFICATION_SVC_URL` — internal URL of verification-svc
- `OIDC_URL` — Keycloak discovery URL
- `SERVICE_PRIVATE_KEY_1` — base64-encoded RSA private key for signing service tokens
- `SERVICE_PRIVATE_KEY_2` — optional second key for rotation (leave empty if not rotating)
- `SERVICE_ACTIVE_KID` — `key-1` or `key-2`, controls which key signs new service tokens
- `RESOURCE_API_JWKS_URL` — URL of this service's JWKS endpoint (used by verification-svc)
- `CORS_ORIGINS` — allowed CORS origin (default: `http://localhost:5173`)

## Endpoints
- `POST /auth/register` — register a local user
- `POST /auth/login` — local login, returns JWT
- `POST /auth/oidc` — exchange Keycloak ID token for app JWT
- `GET /auth/me` — get current user info
- `GET /.well-known/jwks.json` — public JWKS endpoint for service-to-service token verification
- `GET /providers` — list providers (paginated, filterable)
- `POST /providers` — create provider (admin only, calls verification-svc)
- `GET /providers/:id` — get provider by ID
- `PATCH /providers/:id` — update provider (admin only)
- `DELETE /providers/:id` — delete provider (admin only, returns 409 if referrals exist)
- `GET /referrals` — list referrals (paginated, filterable by status)
- `POST /referrals` — create referral
- `PATCH /referrals/:id` — update referral status
