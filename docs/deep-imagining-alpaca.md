# Custom Auth (Signup + Signin) — CareerDNA AI Backend

## Context

The backend currently has no real authentication: `app/core/auth.py:get_current_user` validates tokens by calling `supabase.auth.get_user(token)`, which assumes Supabase Auth issues sessions — but nothing actually signs users up or logs them in yet. There's also no `password_hash` column, no JWT library, and no `bcrypt`/`passlib` in `requirements.txt`.

We're building this as production-grade infrastructure, not a semester-project stub, so the user chose **fully custom auth** (own bcrypt password hashing, own JWT issuance) over delegating to Supabase Auth. That decision has a direct consequence: `database/schema.sql`'s RLS policies are all keyed on `auth.uid()` (Supabase Auth's session claim), which will never populate once we stop using Supabase Auth sessions. So the backend must move to the Supabase **service_role** key (bypasses RLS, standard pattern for a trusted backend) and enforce all authorization in application code — the existing `verify_session_ownership()` helper already does this for sessions, we're extending the same pattern to auth.

Signup fields: full name, email, university, degree, graduation year, core interests (array), password.

**Confirmed decisions (from discussion with user):**
1. Fully custom auth — own `password_hash`, own JWT, no Supabase Auth dependency.
2. `core_interests` — denormalized `TEXT[]` column (not a normalized lookup/junction table), consistent with existing array columns in the schema (`scenes_completed`, `strengths`, `growth_areas`).
3. `university` / `degree` / `graduation_year` — added directly to the `users` table (not a separate academic-info table).
4. No email verification for this pass.
5. Switch `SUPABASE_KEY` to the service_role key; drop the now-dead `auth.uid()`-based RLS policies from `schema.sql` since the backend will bypass RLS entirely and authorization moves to app code.
6. Edit `schema.sql` in place (no live data to preserve, no migrations folder exists yet).
7. Build refresh tokens now: `refresh_tokens` table with rotation + revocation, plus a logout endpoint — not just a bare access token.

## Database changes (`backend/CAREERDNAAI/backend/database/schema.sql`)

**`users` table — add columns:**
```sql
password_hash          TEXT NOT NULL,
degree                 TEXT,
graduation_year         INT CHECK (graduation_year BETWEEN 1950 AND 2100),
core_interests          TEXT[] NOT NULL DEFAULT '{}',
is_active               BOOLEAN NOT NULL DEFAULT TRUE,
failed_login_attempts   INT NOT NULL DEFAULT 0,
locked_until            TIMESTAMPTZ,
```
(`university` already exists as `TEXT`; `full_name`, `email`, `role`, `created_at`, `last_login` already exist and are reused as-is.)

**New `refresh_tokens` table** (opaque random tokens, not JWTs — they need server-side revocability, so there's no benefit to encoding them; only the access token is a JWT):
```sql
CREATE TABLE refresh_tokens (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash    TEXT NOT NULL,              -- SHA-256 hash of the raw token; raw value never stored
  expires_at    TIMESTAMPTZ NOT NULL,
  revoked_at    TIMESTAMPTZ,
  replaced_by   UUID REFERENCES refresh_tokens(id),  -- rotation chain, for reuse-detection
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_refresh_tokens_user  ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash  ON refresh_tokens(token_hash);
```

**RLS cleanup:** remove `CREATE POLICY "users_own" ...` and the `is_admin()` function's dependency on `auth.uid()`, since the backend will always connect with the service_role key (bypasses RLS) and authorization is enforced in Python. Leave `ENABLE ROW LEVEL SECURITY` statements in place as inert defense-in-depth (harmless, costs nothing), but drop the policies that reference `auth.uid()` since they can never match and are misleading dead code. Add `ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;` with no policy, for consistency.

## New/changed application files

Following the existing `Router → Service → Repository` layering (`app/api/v1` → `app/services` → `app/repositories`):

- **`app/schemas/auth.py`** (new) — `SignupRequest`, `SigninRequest`, `TokenResponse`, `RefreshRequest`. Validation: email format + lowercased/stripped; password min 8 / max 72 chars (bcrypt silently truncates beyond 72 bytes — reject longer instead of silently truncating); `full_name` required non-empty; `core_interests` list of non-empty strings, capped (e.g. max 10); `graduation_year` bounded; **no `role` field accepted from the client** (always defaults to `student` server-side — prevents privilege escalation via signup payload).
- **`app/core/security.py`** (new) — password hashing (`bcrypt` package directly, not `passlib`, since passlib's bcrypt backend has known compatibility breaks with `bcrypt>=4.1`), JWT encode/decode helpers (`pyjwt`), and opaque refresh-token generation (`secrets.token_urlsafe`) + SHA-256 hashing for storage.
- **`app/core/auth.py`** (rewrite `get_current_user`) — decode our own JWT (signature + expiry check via `pyjwt`) instead of calling `supabase.auth.get_user()`; extract `user_id`/`role` from claims. Keep the existing dev-mode fallback behavior when unconfigured, and keep `verify_session_ownership()` unchanged.
- **`app/repositories/auth.py`** (new) — `create_user`, `get_user_by_email`, `update_last_login`, `record_failed_login` / `reset_failed_login`, `save_refresh_token`, `get_refresh_token_by_hash`, `revoke_refresh_token`, `revoke_all_user_tokens`. All Supabase access stays isolated here per existing convention.
- **`app/services/auth_service.py`** (new) — orchestrates signup/signin/refresh/logout: hashing, uniqueness checks, lockout logic, token issuance/rotation. Keeps `api/v1/auth.py` thin, matching `session_service.py`'s existing role.
- **`app/api/v1/auth.py`** (new) — endpoints:
  - `POST /auth/signup` — creates user (role forced to `student`), auto-issues access + refresh token pair (auto-login after signup).
  - `POST /auth/signin` — verifies credentials, enforces lockout (5 failed attempts → 15 min lock, matching common production defaults), issues token pair.
  - `POST /auth/refresh` — validates + rotates refresh token, issues new pair; reuse of an already-rotated/revoked token revokes the whole chain for that user (theft signal).
  - `POST /auth/logout` — revokes the presented refresh token.
- **`app/main.py`** — register the new `auth` router.
- **`app/core/config.py`** — add `jwt_secret_key`, `jwt_algorithm` (default `HS256`), `access_token_expire_minutes` (default 60), `refresh_token_expire_days` (default 30).
- **`requirements.txt`** — add `bcrypt` and `pyjwt`.
- **`.env.example` / `.env`** — add `JWT_SECRET_KEY` (placeholder in `.env.example`, real random secret in `.env`); update `SUPABASE_KEY` comment to clarify it must now be the **service_role** key (user needs to swap the actual key value from the Supabase dashboard — that's a manual/secret step, not something to script).

## Security details worth flagging explicitly

- Generic `401 Invalid credentials` on signin failure regardless of whether the email doesn't exist or the password is wrong — avoids user enumeration.
- Email uniqueness enforced by the existing `UNIQUE` constraint on `users.email`; a 409 is returned on conflict.
- Refresh tokens are stored **hashed** (SHA-256), never raw, mirroring how passwords are never stored raw.
- `password_hash` is never included in any response model.

## Explicitly out of scope for this pass (documented, not built)

- Email verification (per decision #4).
- Password reset / forgot-password flow.
- "Logout all devices" endpoint (the repository method `revoke_all_user_tokens` will exist since it's needed for reuse-detection, but no dedicated endpoint yet).
- Rate limiting beyond the per-account lockout counter.

## Verification

- `pytest tests/` from `backend/CAREERDNAAI/backend` — add `tests/test_auth.py` covering: signup happy path, duplicate email rejection, signin with wrong password, signin lockout after repeated failures, refresh rotation, reuse-of-revoked-token detection, logout — following the existing mocked-dependency style used in `test_director.py`.
- Manual smoke test via the already-running `uvicorn app.main:app --reload` + `/health` endpoint, then `curl`/HTTP client through signup → signin → refresh → logout.
