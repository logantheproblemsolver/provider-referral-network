# verification-svc

Downstream microservice that verifies provider NPIs. Only accepts authenticated requests from resource-api.

## Stack
- Node.js + Express (TypeScript)

## Running locally
```bash
npm install
RESOURCE_API_JWKS_URL=http://localhost:8000/.well-known/jwks.json npm run dev
```

## Running via Docker
```bash
docker compose up verification-svc
```

## Endpoints
- `GET /health` — health check
- `GET /verify/:npi` — verify an NPI (requires service JWT from resource-api)

## Auth
Expects `Authorization: Bearer <token>` signed with resource-api's RS256 private key, `iss=resource-api`, `aud=verification-svc`. The middleware fetches resource-api's public keys from `RESOURCE_API_JWKS_URL`, matches by `kid`, and validates the signature. Keys are cached for 10 minutes and refreshed automatically on unknown `kid`.
