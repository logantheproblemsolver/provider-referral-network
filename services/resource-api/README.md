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

## Endpoints
- `POST /auth/register` — register a local user
- `POST /auth/login` — local login, returns JWT
- `POST /auth/oidc` — exchange Keycloak ID token for app JWT
- `GET /auth/me` — get current user info
- `GET /providers` — list providers (paginated, filterable)
- `POST /providers` — create provider (admin only, calls verification-svc)
- `GET /providers/:id` — get provider by ID
- `PATCH /providers/:id` — update provider (admin only)
- `DELETE /providers/:id` — delete provider (admin only)
- `GET /referrals` — list referrals (paginated, filterable by status)
- `POST /referrals` — create referral
- `PATCH /referrals/:id` — update referral status
