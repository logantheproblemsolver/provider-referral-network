# Backend Take-Home — Provider Referral Network

Welcome, and thanks for taking the time. This is a backend exercise for a **senior**
engineering role. We care about how you design systems, not how much boilerplate you can
produce. Aim for roughly **6 focused hours**; ship something coherent and well-reasoned
rather than feature-complete.

---

## 1. Scenario

You're building the backend for a small **Provider Referral Network** — a platform that
tracks healthcare providers and the referrals they send to one another. The system is
split into **two services**:

- **`resource-api`** — the main API. It owns the domain resources (providers, referrals),
  authentication, and the database. When a new provider is added, it must confirm the
  provider's NPI with the verification service before persisting it.

- **`verification-svc`** — a downstream microservice. Given an NPI, it returns a
  verification result (e.g. active/inactive, taxonomy). It only serves **authenticated**
  callers — `resource-api` must present a token that this service validates.

> **Data is fully synthetic.** NPIs and ICD-10 codes are public reference data, not PHI.
> **Do not use, generate, or commit any real patient data (PHI).** Member references must
> be opaque, fictional identifiers.

---

## 2. What we're evaluating

Four pillars. Touch all of them:

1. **API design** — resource modeling, validation, status codes, pagination, error shape.
2. **ORM usage** — schema, **migrations**, and a working seed step. You pick the ORM.
3. **Auth fundamentals** — JWT issuance/validation, protected routes, roles, and
   **OpenID Connect**.
4. **Microservice comfort** — two services and how they authenticate to each other.

We're hiring for backend judgment. **Data modeling is yours to own** — we deliberately do
not hand you a schema.

---

## 3. Core requirements (must-have)

**`resource-api`**
- User **registration** and **login**.
- **JWT**-protected routes; reject missing/invalid/expired tokens correctly.
- At least one **role-gated** action (e.g. only an `admin` may delete a provider).
- **Provider** resource: create, read, list (with **filtering** and **pagination**), update, delete.
- **Referral** resource: create a referral between two providers, list referrals, update status.
- On **provider create**, call `verification-svc` and only persist if verification passes.
  Handle the case where that service is unavailable.

**Persistence**
- Use an **ORM of your choice** (justify the choice in your write-up).
- Provide **migrations** (not auto-create-tables-on-boot) and a **seed** step that loads
  `data/providers.seed.json`. Map that raw data onto whatever schema you design.

**`verification-svc`**
- Expose `GET /verify/{npi}` returning a synthetic verification result.
- **Reject unauthenticated requests.** Validate the token `resource-api` sends.

**OpenID Connect**
- Demonstrate OIDC understanding: either accept and validate an **OIDC ID token** from an
  external identity provider for login, or stand up the **optional Keycloak** service
  (commented in `docker-compose.yml`) and integrate it. A local password + self-signed JWT
  flow alone does **not** satisfy this pillar.

**Frontend (intentionally minimal)**
- **React + Vite + TypeScript.** A single page that **logs in** and **lists providers**.
  Styling does not matter. This is not a frontend role — keep it small.

---

## 4. Stretch goals (optional, only if time allows)

Refresh tokens with rotation · deeper RBAC · rate limiting · automated tests ·
OpenAPI/Swagger docs · both services containerized · async endpoints · caching verification
results · JWKS-based key rotation between the two services.

---

## 5. Constraints

- The core backend must be `FastAPI` using **python**
- The microservice for verifiction must be built with `TypeScript/JavaScript` on Node.js using your preference of node library or framework - `express.js` is perfectly fine here.
- **Synthetic data only — no PHI, ever.** No real names, addresses, dates of birth, or
  record numbers.
- Target **~6 hours**. If you cut something, say so and explain the trade-off.

---

## 6. What we provide vs. what you build

**Provided (scaffolding):**
- `docker-compose.yml` — Postgres out of the box (plus a commented Keycloak block for OIDC).
- `.env.example` — copy to `.env` and adjust.
- `data/providers.seed.json` — raw synthetic provider records to seed from.
- Empty `services/` and `frontend/` directories with brief notes.

**You build:** everything inside `services/resource-api`, `services/verification-svc`, and
`frontend`. Choose your own project structure, dependencies, and tooling.

---

## 7. Setup

```bash
cp .env.example .env
docker compose up -d        # starts Postgres (and Keycloak if you enable it)
```

Then build each service under `services/` and document how to run it in your own README(s).

---

## 8. Submission

Provide a git repository (or a zip) including a root **`SOLUTION.md`** that covers:

- How to run everything end-to-end.
- Which ORM you chose and **why**.
- Your auth design, and **how the two services authenticate to each other**.
- Trade-offs you made and anything you intentionally skipped.
- What you'd do with more time.

We read the write-up closely — it's where senior judgment shows.
