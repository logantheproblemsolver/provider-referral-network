# Solution: Provider Referral Network

## How to Run

### Prerequisites
- Docker and Docker Compose
- A Keycloak realm configured (see Keycloak Setup below)

### 1. Environment Setup
```bash
cp .env.example .env
```
Edit `.env` and set:
- `JWT_SECRET`: at least 32 characters
- `OIDC_URL`: Keycloak discovery URL (e.g. `http://keycloak:8080/realms/referral-network/.well-known/openid-configuration`)
- `SERVICE_PRIVATE_KEY_1`: base64-encoded RSA private key — generate with `openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 | base64 | tr -d '\n'`
- `SERVICE_PRIVATE_KEY_2`: optional second key for rotation (leave empty if not rotating)
- `SERVICE_ACTIVE_KID`: `key-1` or `key-2` — controls which key signs new service tokens
- `RESOURCE_API_JWKS_URL`: `http://resource-api:8000/.well-known/jwks.json`

### 2. Start All Services
```bash
docker compose up
```

This starts:
- `postgres` on port 5432
- `keycloak` on port 8080
- `resource-api` on port 8000
- `verification-svc` on port 9000
- `frontend` on port 5173

### 3. Run Migrations and Seed
Once the containers are up, run migrations and seed data from inside the resource-api container:
```bash
docker compose exec resource-api sh -c "PYTHONPATH=. alembic upgrade head && python seed.py"
```

### 4. Keycloak Setup
1. Go to `http://localhost:8080` → Admin Console (admin/admin)
2. Create a realm named `referral-network`
3. Create a client named `resource-api` with:
   - Standard flow enabled
   - Direct access grants enabled
   - Valid redirect URIs: `http://localhost:5173/callback`
   - Web origins: `http://localhost:5173`
4. Create a demo user with an email address and set a password

### 5. Access the App
- Frontend: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

### 6. Create Your First User
The first user to register or sign in via OIDC becomes admin. Either:
- Register via local auth: `POST /auth/register` with `{ email, password }`
- Or log in via Keycloak on the frontend

---

## ORM Choice: SQLAlchemy (async)

I chose **SQLAlchemy** with the async `asyncpg` driver for the following reasons:

- **Mature and battle-tested**: SQLAlchemy is the de facto ORM in the Python ecosystem with excellent PostgreSQL support
- **Async-native**: `AsyncSession` + `asyncpg` fits naturally with FastAPI's async request handling, avoiding thread pool overhead that sync ORMs require
- **Explicit migrations**: Alembic (SQLAlchemy's migration tool) gives full control over schema changes with proper up/down migrations, not auto-create-on-boot
- **Mapped columns**: SQLAlchemy 2.0's `Mapped` + `mapped_column` API gives type-safe model definitions that integrate cleanly with Python's type system

The tradeoff: SQLAlchemy has more boilerplate than lighter ORMs like Tortoise or Piccolo. For a larger team I'd still choose it for its maturity and ecosystem, but for a pure async greenfield project Tortoise ORM is worth considering.

---

## Auth Design

### Local Auth
- `POST /auth/register`: bcrypt hashes the password and stores the user. The first user to register becomes admin, all subsequent users get the `user` role. Role assignment is intentionally server-side and not derived from the OIDC provider: this keeps user management self-contained.
- `POST /auth/login`: verifies the bcrypt hash and issues an HS256 JWT (`sub`, `email`, `role`, `iat`, `exp`)
- All protected routes validate the JWT via the `get_current_user` FastAPI dependency, which decodes the token and fetches the user from the database on every request

### OpenID Connect (Keycloak)
The frontend implements the **Authorization Code + PKCE** flow:

1. User clicks "Continue with Keycloak"
2. Frontend generates a `code_verifier` (random 32 bytes) and `code_challenge` (SHA-256 of the verifier, base64url encoded), stores the verifier in `sessionStorage`
3. Browser redirects to Keycloak's `/auth` endpoint with `response_type=code`, `code_challenge`, and `code_challenge_method=S256`
4. User authenticates on Keycloak's login page
5. Keycloak redirects to `http://localhost:5173/callback?code=...&state=...`
6. Frontend exchanges the code at Keycloak's token endpoint using the `code_verifier`
7. Frontend sends the returned `id_token` to `POST /auth/oidc`
8. resource-api fetches Keycloak's JWKS via the discovery document, validates the RS256 signature, and extracts the email claim
9. resource-api find-or-creates the user in its own database and issues an app JWT

PKCE is used because this is a browser-based SPA with no client secret: PKCE replaces the secret by binding the authorization request to the token exchange, preventing authorization code interception attacks.

`verify_aud` is set to `False` during ID token validation because Keycloak sets the audience to the client ID. In production this would be tightened to explicitly validate `aud=resource-api`.

### Role Gating
- `GET /providers`, `GET /providers/:id`, `GET /referrals`: any authenticated user
- `POST /providers`, `PATCH /providers/:id`, `DELETE /providers/:id`: admin only
- `POST /referrals`, `PATCH /referrals/:id`: any authenticated user
- `GET /auth/me`: returns the current user's role, used by the frontend to gate admin UI

401 is returned for unauthenticated requests. 403 is returned when a user is authenticated but lacks the required role this distinction is intentional.

---

## Service-to-Service Auth

When `POST /providers` is called, resource-api must verify the NPI with verification-svc before persisting. verification-svc rejects unauthenticated callers.

**Flow:**
1. resource-api calls `create_service_token()` which signs a short-lived RS256 JWT with `iss=resource-api`, `aud=verification-svc`, a 5-minute expiry, and a `kid` header identifying which key signed it
2. resource-api calls `GET /verify/:npi` on verification-svc with `Authorization: Bearer <token>`
3. verification-svc's auth middleware fetches resource-api's JWKS from `GET /.well-known/jwks.json`, matches the key by `kid`, and validates the RS256 signature, issuer, and audience
4. The JWKS response is cached for 10 minutes; on an unknown `kid`, `jwks-rsa` re-fetches automatically
5. If verification-svc is unreachable, resource-api returns 503. If verification fails, it returns 422.

**Key rotation** is supported without sharing any secret. Two keys (`SERVICE_PRIVATE_KEY_1`, `SERVICE_PRIVATE_KEY_2`) can be loaded simultaneously — both are published in the JWKS so tokens signed with either key remain valid. `SERVICE_ACTIVE_KID` controls which key signs new tokens. To rotate: load a new key, switch `SERVICE_ACTIVE_KID`, restart resource-api. After 5 minutes (token expiry), all tokens signed with the old key are expired and it can be removed. In production, keys would be stored in a secrets manager and rotated without restart.

---

## Trade-offs and Intentional Skips

**Kept simple intentionally:**
- **NPI verification is synthetic**: validation checks the 10-digit format only. In production this would call `npiregistry.cms.hhs.gov`. The architecture (service-to-service JWT auth, 503 handling) is production-ready; the verification logic is the placeholder.
- **Patient data is opaque**: `patient_ref` is a synthetic identifier (e.g. `PAT-001`). No real PHI is stored. In production this would reference a patients table with its own access controls.
- **OIDC audience validation**: `verify_aud=False` is a POC shortcut. Production would validate `aud=resource-api`.
- **CORS origins**: pulled from config with a default of `localhost:5173`. Production would have no default and require explicit configuration per environment.
- **No refresh tokens**: access tokens expire after 1 hour. Refresh token rotation is a stretch goal.
- **HS256 for user JWTs**: resource-api is the only service that issues and verifies user tokens, so a symmetric secret is appropriate. RS256 would be necessary if other services needed to independently verify tokens without being trusted to issue them: in that case a JWKS endpoint would replace the shared secret. Keycloak uses RS256 for exactly this reason.
- **Rate limiting**: implemented via `slowapi`. Auth endpoints (`/auth/register`, `/auth/login`, `/auth/oidc`) are limited to 5 requests/minute per IP; all other endpoints are limited to 10 requests/minute. The limiter is defined in its own `limiter.py` module to avoid circular imports. In production this would be backed by Redis so limits are shared across multiple instances, and trusted proxy IPs would be explicitly configured to prevent `X-Forwarded-For` spoofing. Auth endpoints would also be paired with account lockout after N consecutive failures since rate limiting slows brute force but a patient attacker who stays under the threshold can still make thousands of guesses per day.

**Skipped:**
- Automated tests: given the 6-hour target, I prioritized a working end-to-end system over test coverage. I would add pytest + httpx integration tests for the API layer and verify the PKCE flow with Playwright.

---

## What I'd Do With More Time

1. **Refresh tokens with rotation**: short-lived access tokens + longer-lived refresh tokens stored server-side, invalidated on use
2. **Integration tests**: pytest + httpx against a real test database, Playwright for the PKCE flow
3. **Patient resource**: a proper patients table with its own endpoints and access controls, replacing the opaque `patient_ref` string
4. **Deeper RBAC**: currently binary admin/user. A production system would have more granular permissions (e.g. only the referring provider can update a referral's status)
5. **Secrets manager integration**: move `SERVICE_PRIVATE_KEY_1/2` out of `.env` and into AWS Secrets Manager or Vault, with hot reload so key rotation doesn't require a restart
6. **JWKS key rotation for Keycloak tokens**: cache the Keycloak JWKS with a TTL and refresh on unknown `kid` rather than fetching on every OIDC login
