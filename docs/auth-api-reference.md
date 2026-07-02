# Auth & User API Reference (Frontend Integration Guide)

## Base URL
Dev: `http://localhost:8000` (`uvicorn app.main:app --reload` from `backend/CAREERDNAAI/backend/`). Ask backend for the production URL when deploying.

## Every route except auth itself is private
`/`, `/health`, and the four `/auth/*` endpoints below are the **only** public routes — everything else in the API (sessions, reports, onboarding, `/users/*`) requires a valid access token and returns `401` without one. There's no "browse without logging in" mode anywhere else. Concretely: the frontend must have a valid `access_token` in hand *before* it can call any session/report/user endpoint, which is why the page-load pattern at the bottom of this doc matters — it's not optional polish, it's how the app decides whether to show login or the dashboard at all.

## Auth model, in short
- `signup`, `signin`, and `refresh` all return an **access token** (JWT, ~24h life) and a **refresh token** (opaque string, 30 days).
- Send the access token on every authenticated request: header `Authorization: Bearer <access_token>`.
- Refresh tokens are **single-use** — every call to `/auth/refresh` returns a brand new refresh token and invalidates the old one. Always overwrite your stored refresh_token with the new one.
- If a request comes back `401`, call `/auth/refresh` with the stored refresh_token, then retry. If refresh itself returns `401`, the session is genuinely over — clear stored tokens and show the login screen.
- Where you store these tokens (`localStorage` vs an `httpOnly` cookie) is your call — real security tradeoffs either way (XSS vs CSRF), not something the backend prescribes.

---

## POST /auth/signup
Creates an account and logs the user in immediately — no separate signin call needed afterward.

**Request body:**
```json
{
  "full_name": "Jane Doe",
  "email": "jane@example.com",
  "password": "correct-horse-battery",
  "university": "MIT",
  "degree": "CS",
  "graduation_year": 2026,
  "core_interests": ["backend", "ml"]
}
```
| field | type | required | constraints |
|---|---|---|---|
| full_name | string | yes | 1–200 chars |
| email | string | yes | valid email format; case/whitespace normalized server-side |
| password | string | yes | 8–72 chars |
| university | string | no | default `""` |
| degree | string | no | default `""` |
| graduation_year | int | no | 1950–2050 |
| core_interests | string[] | no | max 10 items, no empty strings |

A `role` field, if sent, is silently ignored — accounts always start as `student`.

**Success `200`:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "wi7p...",
  "token_type": "bearer",
  "user": {
    "id": "c809d15b-...",
    "email": "jane@example.com",
    "full_name": "Jane Doe",
    "role": "student",
    "university": "MIT",
    "degree": "CS",
    "graduation_year": 2026,
    "core_interests": ["backend", "ml"]
  }
}
```

**Errors:**
| status | body | meaning |
|---|---|---|
| 422 | FastAPI validation error shape | bad email / password length / graduation_year range / etc. |
| 409 | `{"detail": "Email already registered"}` | |
| 503 | `{"detail": "Database not configured"}` | backend misconfiguration, not a user error |

---

## POST /auth/signin
**Request:**
```json
{ "email": "jane@example.com", "password": "correct-horse-battery" }
```
**Success `200`:** same shape as signup's response.

**Errors:**
| status | body | meaning |
|---|---|---|
| 401 | `{"detail": "Invalid email or password"}` | wrong password **or** unknown email — deliberately the same message for both, don't use it to distinguish which |
| 423 | `{"detail": "Account temporarily locked. Try again later."}` | 5 failed attempts locks the account for 15 minutes |
| 403 | `{"detail": "Account is disabled"}` | |

---

## POST /auth/refresh
**Request:**
```json
{ "refresh_token": "wi7p..." }
```
**Success `200`:** a fresh token pair — **both** access and refresh tokens are new. Discard the old refresh_token.

**Errors (all `401`):**
| detail | meaning |
|---|---|
| `Invalid refresh token` | garbage/unrecognized token |
| `Refresh token has been revoked` | user already logged out with this token |
| `Refresh token reuse detected — all sessions revoked` | an already-rotated (superseded) token was reused — treated as theft, every session for that user is now dead, they must sign in again |
| `Refresh token expired` | past its 30-day lifetime |

---

## POST /auth/logout
**Request:**
```json
{ "refresh_token": "wi7p..." }
```
**Success `200`:** `{"status": "success"}`. Only revokes the one session this token belongs to — other devices/tabs stay logged in.

---

## GET /users/me
No body. Requires `Authorization: Bearer <access_token>`.

**Success `200`:** the same `user` object shape shown in signup's response (no tokens, just the profile).

**Errors:**
| status | meaning |
|---|---|
| 401 | missing, invalid, or expired access token |

Use this on app load to check whether a stored token is still valid — see the pattern below.

---

## GET /users/{user_id}
Same success shape as `/users/me`, for looking up a specific account.

**Errors:**
| status | meaning |
|---|---|
| 403 | caller is neither `user_id` nor an `admin` — returned both when the id belongs to someone else **and** when the id doesn't exist at all, so a regular user can't probe IDs to discover which accounts exist |
| 404 | only reachable by an `admin` requesting a truly nonexistent id |

---

## Recommended pattern: staying logged in across visits
1. On app start, if a stored `access_token` exists, call `GET /users/me`.
2. `200` → render the dashboard with the returned profile, done.
3. `401` → call `POST /auth/refresh` with the stored `refresh_token`.
   - success → store the new token pair, go back to step 1 (or just proceed, you already have the profile from signup/signin/refresh responses — `/users/me` isn't the only source of it).
   - failure → clear stored tokens, show the login screen.
