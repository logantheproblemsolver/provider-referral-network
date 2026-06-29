# verification-svc

Downstream microservice that verifies provider NPIs. Only accepts authenticated requests from resource-api.

## Stack
- Node.js + Express (TypeScript)

## Running locally
```bash
npm install
SERVICE_JWT_SECRET=<secret> npm run dev
```

## Running via Docker
```bash
docker compose up verification-svc
```

## Endpoints
- `GET /health` — health check
- `GET /verify/:npi` — verify an NPI (requires service JWT from resource-api)

## Auth
Expects `Authorization: Bearer <token>` signed with `SERVICE_JWT_SECRET`, `iss=resource-api`, `aud=verification-svc`.
