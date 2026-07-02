# Auth & User Profile — What We Built and Why

## Starting point
The backend had no real authentication. `get_current_user` called `supabase.auth.get_user(token)`, which assumes Supabase Auth issues sessions — but nothing actually signed users up or logged them in. There was no `password_hash` column, no JWT library, and no signup/signin/refresh/logout endpoints at all.

This was built as production infrastructure, not a semester-project stub — an 8-week internship MVP, with roughly 4 weeks already gone when this work started. That timeline shaped several of the tradeoffs below.

## What was built
- Full custom auth: `POST /auth/signup`, `/signin`, `/refresh`, `/logout`
- Profile lookup: `GET /users/me`, `GET /users/{user_id}`
- Schema changes to support all of the above, including normalizing university/degree into lookup tables

## Key decisions and why

**1. Fully custom auth, not Supabase Auth.** Own bcrypt password hashing, own JWT issuance/verification — chosen over delegating to Supabase Auth for full control over the flow. Cost: we lose Supabase Auth's built-in email verification/password-reset, and the existing RLS policies (keyed on `auth.uid()`, Supabase Auth's session claim) stopped working since our JWTs never create a Supabase Auth session. Those policies were removed from `schema.sql`; the backend now connects with the Supabase **service_role** key (bypasses RLS) and enforces all authorization in application code.

**2. Access + refresh tokens, with rotation and theft detection.** Access token: JWT, 24h expiry (raised from an initial 1h once we realized the refresh token already covers longer sessions — no need to force re-login every hour). Refresh token: opaque random string, 30 days, stored **hashed** (SHA-256) in a `refresh_tokens` table, never raw. Every refresh rotates the token (old one is invalidated, a new one issued); if an already-rotated token is ever replayed, that's treated as a theft signal and **every** session for that user is revoked. Logout revokes only the one token it's given — a real bug where logout was cascading to revoke *every* session (including other devices) was caught during smoke testing and fixed.

**3. Account lockout.** 5 failed signin attempts locks the account for 15 minutes. Signin failures return the same generic `401` regardless of whether the email doesn't exist or the password is wrong, to avoid leaking which accounts exist.

**4. Normalized schema, but with a conscious exception.** `university`/`degree` became proper lookup tables (`universities`, `degrees`) referenced by FK, instead of free text — avoids duplicate/typo'd institution names and enables clean aggregation later. Their IDs are plain integers (not UUID), since these are small, non-sensitive reference tables where a guessable sequential ID doesn't matter — unlike `users.id`, which stays UUID. `core_interests` deliberately stayed a `TEXT[]` array column rather than a fully normalized many-to-many (interests + junction table) — matches existing array-column conventions elsewhere in the schema (`scenes_completed`, `strengths`, `growth_areas`), and was a conscious tradeoff, not an oversight.

**5. Stayed on `supabase-py`/PostgREST — did not switch to an ORM.** A direct-Postgres connection via SQLAlchemy + Alembic migrations would be more standard/production-grade (real cross-table transactions, versioned migrations, no need for the RLS-bypass-via-service_role workaround). Consciously deferred: with 4 of 8 weeks left and the auth repository layer already built against `supabase-py`, the rewrite cost (every repository — auth, sessions, reports, users) outweighed the benefit for this timeline. **Known consequence:** signup performs up to 4 separate writes (university lookup, degree lookup, users insert, refresh_tokens insert) with no transaction wrapping them — a failure partway through can leave inconsistent state (e.g. a user row created but no refresh token issued, requiring the client to fall back to signin).

**6. Privilege escalation prevented at the schema boundary.** The signup request accepts no `role` field — accounts always default to `student` server-side, regardless of what a client sends.

**7. ID enumeration prevented on `GET /users/{user_id}`.** A non-admin gets `403` both when the id belongs to someone else *and* when the id doesn't exist at all — so probing random IDs can't be used to discover which accounts exist. `404` is only reachable by an admin.

## Files touched
- `database/schema.sql` — new `universities`, `degrees`, `refresh_tokens` tables; `users` gained `password_hash`, `university_id`/`degree_id`, `graduation_year`, `core_interests`, lockout fields; `auth.uid()`-based RLS policies removed
- `app/core/security.py` *(new)* — bcrypt hashing, JWT issuance/decoding, refresh token generation/hashing
- `app/core/auth.py` — `get_current_user` rewritten to decode our own JWT; new `verify_self_or_admin()` helper (also now used by `verify_session_ownership`, removing duplicated logic)
- `app/core/config.py` — JWT settings
- `app/schemas/auth.py` *(new)* — request/response models
- `app/repositories/auth.py` *(new)* — all users/refresh_tokens/universities/degrees DB access, including the get-or-create lookup helper
- `app/repositories/users.py` — onboarding now resolves university through the same lookup-table helper
- `app/services/auth_service.py` *(new)* — signup/signin/refresh/logout/get_user_profile orchestration
- `app/api/v1/auth.py` *(new)*, `app/api/v1/users.py` — the actual endpoints
- `app/main.py` — registered the new auth router
- `requirements.txt` — `bcrypt`, `pyjwt`, `email-validator`
- `.env` / `.env.example` — `JWT_SECRET_KEY` added; `SUPABASE_KEY` switched to service_role
- `tests/test_auth.py` *(new)* — 19 tests against an in-memory fake of the repository layer, no live DB required to run them

## Verified
- 19/19 automated tests pass (`pytest tests/`)
- Full manual smoke test against the live Supabase project: signup, signin (incl. wrong password and lockout), refresh (incl. rotation and theft-detection), logout (incl. confirming it doesn't cascade to other sessions), duplicate-email rejection, university/degree lookup dedup, `/users/me` and `/users/{id}` authorization — all correct

## Known gaps (intentionally out of scope for this pass)
- No email verification
- No password-reset / forgot-password flow
- No "logout all devices" endpoint (the underlying `revoke_all_user_tokens` exists and is used internally for theft-detection, but isn't exposed directly)
- No rate limiting beyond the per-account lockout counter
- No cross-table transactions (see decision #5)
