# Auth API — Manual Test Cases (Hoppscotch)

## Setup
- Run the server: `uvicorn app.main:app --reload` from `backend/CAREERDNAAI/backend/`
- Base URL: `http://localhost:8000`
- All requests: `Content-Type: application/json`
- Run these roughly in order — later cases reuse tokens/state from earlier ones (e.g. the duplicate-email test needs case 1's account to already exist).

---

## POST /auth/signup

**1. Happy path**
```json
{
  "full_name": "Jane Doe",
  "email": "jane.doe@example.com",
  "password": "correct-horse-battery",
  "university": "MIT",
  "degree": "CS",
  "graduation_year": 2026,
  "core_interests": ["backend", "ml"]
}
```
Expect: `200`, body has `access_token`, `refresh_token`, `user` (no `password`/`password_hash` anywhere). Save both tokens for later cases.

**2. Duplicate email** — same body as #1, resend as-is.
Expect: `409`, `{"detail": "Email already registered"}`

**3. Invalid email format** — `"email": "not-an-email"`
Expect: `422`

**4. Password too short** — `"password": "abc123"` (6 chars)
Expect: `422`

**5. Password too long** — `"password"` set to 80+ characters
Expect: `422` (bcrypt's 72-byte limit — rejected outright, not silently truncated)

**6. Missing full_name** — omit `full_name` entirely
Expect: `422`

**7. graduation_year out of range** — `"graduation_year": 1800` and separately `2999`
Expect: `422` for both (allowed range is 1950–2050)

**8. core_interests contains an empty string** — `"core_interests": ["backend", ""]`
Expect: `422`

**9. core_interests over the cap** — 11+ items in the array
Expect: `422` (max 10)

**10. role field is ignored (privilege escalation check)** — take body #1 with a new email, add `"role": "admin"`
Expect: `200`, but `user.role` in the response is `"student"` regardless — confirms the client can't self-promote to admin.

---

## POST /auth/signin

**11. Happy path**
```json
{ "email": "jane.doe@example.com", "password": "correct-horse-battery" }
```
Expect: `200`, fresh `access_token` + `refresh_token`.

**12. Wrong password**
```json
{ "email": "jane.doe@example.com", "password": "wrong-password" }
```
Expect: `401`, `{"detail": "Invalid email or password"}`

**13. Nonexistent email**
```json
{ "email": "nobody@example.com", "password": "whatever123" }
```
Expect: `401` with the **same** generic message as #12 (deliberate — don't leak which part was wrong).

**14. Account lockout** — send #12 (wrong password) **5 times in a row**, then a 6th time with the **correct** password.
Expect: attempts 1–5 → `401` each. Attempt 6 (even with correct password) → `423`, `{"detail": "Account temporarily locked. Try again later."}`
(Lockout is 15 minutes — either wait it out or use a fresh signup account to keep testing other cases.)

---

## POST /auth/refresh

Use a fresh signup/signin (not the locked-out account from #14) for this section.

**15. Happy path** — `{ "refresh_token": "<token from signin>" }`
Expect: `200`, new `access_token` **and** new `refresh_token`, both different from the ones you sent in.

**16. Reuse of a rotated (old) refresh token** — immediately after #15, call `/auth/refresh` again with the **original** (pre-#15) refresh token.
Expect: `401`, `{"detail": "Refresh token reuse detected — all sessions revoked"}`. This is the theft-detection path — confirm by then trying the token you got back from #15 too: it should now also be `401` (whole chain revoked).

**17. Garbage token** — `{ "refresh_token": "not-a-real-token" }`
Expect: `401`, `{"detail": "Invalid refresh token"}`

---

## POST /auth/logout

Do a fresh signin to get a clean refresh token before this section.

**18. Happy path** — `{ "refresh_token": "<valid token>" }`
Expect: `200`, `{"status": "success"}`. Then call `/auth/refresh` with that same token — expect `401`, `{"detail": "Refresh token has been revoked"}` (note: different message from #16 — logout isn't treated as theft).

**19. Logout on one session doesn't kill others** — sign in **twice** (two separate `/auth/signin` calls, same account) to get tokens A and B. Logout with A's refresh token. Then call `/auth/refresh` with B's refresh token.
Expect: logout → `200`. Refresh with B → `200` (still works — this was a real bug caught during dev, now fixed and covered by an automated regression test too).

---

## Protected endpoint (get_current_user) sanity check

Use `POST /user/onboarding` (or any endpoint behind `Depends(get_current_user)`) to confirm the access token itself is honored:

**20. Valid access token** — header `Authorization: Bearer <access_token from any signin>`
Expect: `200` (or whatever that endpoint normally returns for a valid call) — not a `401`.

**21. Missing Authorization header** — send the same request with no `Authorization` header.
Expect: `401`, `{"detail": "Missing or invalid Authorization header"}`

**22. Garbage access token** — `Authorization: Bearer garbage.not.a.jwt`
Expect: `401`, `{"detail": "Invalid token"}`

---

## Not practically testable manually
- **Access token expiry** (24h) and **refresh token expiry** (30 days) — too long to wait out by hand. Covered by unit tests (`tests/test_auth.py`) instead, which manipulate expiry directly.
