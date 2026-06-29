# frontend

Minimal React + Vite + TypeScript frontend for the Provider Referral Network.

## Stack
- React 18 + TypeScript
- Vite

## Running locally
```bash
npm install
npm run dev
```
Runs at `http://localhost:5173`.

## Running via Docker
```bash
docker compose up frontend
```

## Environment
Copy `.env.example` to `.env` and set:
- `VITE_API_URL` — resource-api URL (default: `http://localhost:8000`)
- `VITE_KEYCLOAK_BASE` — Keycloak OIDC base URL
- `VITE_KEYCLOAK_CLIENT_ID` — Keycloak client ID
- `VITE_REDIRECT_URI` — OAuth callback URL (default: `http://localhost:5173/callback`)

## Features
- Local login (email + password)
- Keycloak login via Authorization Code + PKCE
- Providers list with create, edit, delete (admin only)
- Referrals list with create and status update
