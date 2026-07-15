# Manual Test Cases — Scene Generation Variability Across Users

**Goal:** confirm whether the AI-generated simulation content (scenes,
evaluations) is actually personalized/varied across different users and
attempts, or suspiciously identical — which would indicate a caching bug,
a prompt that ignores user context, or the LLM being called with settings
that make it deterministic when it shouldn't be.

**Important — run this against the real agent, not the mock.**
`mock_agent.py` is intentionally deterministic (same input → same output,
always) — testing "is output varied" against it will always say "identical,"
which tells you nothing about the actual LLM. Set in `.env`:
```
AGENT_LAYER_IMPL=real
```
Test Group D below deliberately runs against `mock` first as a control —
if that *doesn't* come back identical, something is wrong with the test
setup itself, not the AI layer.

---

## Setup — three test accounts

```bash
BASE=http://localhost:8000/api/v1

for n in a b c; do
  curl -s -X POST $BASE/auth/signup -H "Content-Type: application/json" \
    -d "{\"full_name\":\"Variability Test $n\",\"email\":\"variability-test-$n@example.com\",\"password\":\"test-password-123\"}" \
    | tee "user_$n.json"
done
```
Copy each response's `data.access_token` → `TOKEN_A`, `TOKEN_B`, `TOKEN_C`.

---

## Test Group A — Cross-user scene generation, identical inputs

Same `domain`+`difficulty`, three different accounts, compare scene 1.

```bash
curl -s -X POST $BASE/simulations -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" -d '{"domain":"product_manager","difficulty":"medium"}' \
  | python -m json.tool > scene_A.json

curl -s -X POST $BASE/simulations -H "Authorization: Bearer $TOKEN_B" \
  -H "Content-Type: application/json" -d '{"domain":"product_manager","difficulty":"medium"}' \
  | python -m json.tool > scene_B.json

curl -s -X POST $BASE/simulations -H "Authorization: Bearer $TOKEN_C" \
  -H "Content-Type: application/json" -d '{"domain":"product_manager","difficulty":"medium"}' \
  | python -m json.tool > scene_C.json

diff scene_A.json scene_B.json
diff scene_A.json scene_C.json
```

**TC-A1 — Record:** is `data.scene.title`/`narrative`/`context_data`
identical or different across A, B, C?
**Expected (real agent):** different — same domain/difficulty shouldn't
produce byte-identical scenes across unrelated users.
**Red flag:** `diff` shows zero differences in the narrative content across
all three — suggests caching or a prompt that ignores per-call variation.

Keep each account's `session_id` (`SESSION_A`, `SESSION_B`, `SESSION_C`) for
the next groups.

---

## Test Group B — Same user, repeated generation

Does the *same* account get varied content across separate attempts, or
does it always get the same scene 1 for a given domain/difficulty?

```bash
for i in 1 2 3; do
  curl -s -X POST $BASE/simulations -H "Authorization: Bearer $TOKEN_A" \
    -H "Content-Type: application/json" -d '{"domain":"product_manager","difficulty":"medium"}' \
    | python -m json.tool > "scene_A_attempt_$i.json"
done

diff scene_A_attempt_1.json scene_A_attempt_2.json
diff scene_A_attempt_2.json scene_A_attempt_3.json
```

**TC-B1 — Record:** does the same account get different scene content on
each fresh attempt?
**Expected:** different each time (the LLM shouldn't be pinned to one fixed
output per user+domain+difficulty combination either).

---

## Test Group C — Cross-user evaluation, identical response text

Submit the **exact same** response text to scene 1 under two different
accounts — does the evaluation (score, feedback, dimension scores) vary?

```bash
curl -s -X POST $BASE/simulations/$SESSION_A/scenes/1/responses \
  -H "Authorization: Bearer $TOKEN_A" -H "Content-Type: application/json" \
  -d '{"response":{"raw_text":"I would clarify the success metric with the stakeholder before committing to scope."}}' \
  | python -m json.tool > eval_A.json

curl -s -X POST $BASE/simulations/$SESSION_B/scenes/1/responses \
  -H "Authorization: Bearer $TOKEN_B" -H "Content-Type: application/json" \
  -d '{"response":{"raw_text":"I would clarify the success metric with the stakeholder before committing to scope."}}' \
  | python -m json.tool > eval_B.json

diff eval_A.json eval_B.json
```

**TC-C1 — Record:** are `overall_score`/`dimension_scores`/`feedback_summary`
the same or different between A and B?
**Expected:** could reasonably go either way — if scene 1's content differed
between A and B (per Test Group A), the evaluation is scored against a
*different scene*, so different scores are expected and not a bug. This
test is more about sanity-checking that evaluation isn't hardcoded/cached
than proving strict randomness — note the scene content each was evaluated
against alongside the scores, so you're comparing like-for-like context.

---

## Test Group D — Control: confirm the mock *is* deterministic

Flip `.env` to `AGENT_LAYER_IMPL=mock`, restart the server, repeat Test
Group A's steps once.

**TC-D1 — Expected:** `diff` between all three mock runs shows **zero
differences** in generated content (mock is intentionally deterministic).
If the mock run shows differences, the test methodology itself is broken
(e.g. comparing the wrong fields, or a non-deterministic field like a
timestamp/UUID is polluting the diff — see note below) — fix that before
trusting the real-agent results above.

> **Note:** every response includes non-deterministic fields regardless of
> agent implementation — `session_id`, scene `id`/timestamps, etc. Diff
> only the meaningful content fields (`title`, `narrative`, `context_data`,
> `prompt_for_response`, `evaluation.dimension_scores`, etc.), or strip the
> IDs/timestamps before diffing, so those don't create false "differences."

---

## Summary table to fill in

| Test | A vs B | A vs C | Same-user repeat | Notes |
|---|---|---|---|---|
| Scene 1 content (real) | | | | |
| Evaluation, same input text (real) | | | | |
| Scene 1 content (mock, control) | identical (expected) | identical (expected) | identical (expected) | confirms test setup is valid |
