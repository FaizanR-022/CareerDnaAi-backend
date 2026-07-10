-- CareerDNA AI — Database Schema
-- Supabase / PostgreSQL
--
-- This file previously carried two generations of the simulation schema
-- side by side. The legacy generation is now retired: `session_service.py`,
-- `app/api/v1/sessions.py`, and `app/repositories/sessions.py` have all
-- been deleted (frontend is being re-integrated from scratch against the
-- new flow — only login/signup stay as they are), so `sessions` is
-- disabled below rather than left live. `career_dna_reports` stays active
-- — it's the persistence target for the new report-generation flow
-- (task 9), just not yet written to by anything.
--
-- Current tables:
--   ACTIVE: universities, degrees, users, user_profiles, refresh_tokens,
--     career_dna_reports, simulation_sessions, simulation_scenes,
--     scene_evaluations, stakeholder_trust, npc_memory.
--   DISABLED (commented out, kept for reference): sessions, scores,
--     decisions_log — all confirmed to have never been written to before
--     being disabled, so nothing was lost in any case.
--
-- The two legacy dashboard views (student_completed_domains,
-- admin_session_overview) have been removed — superseded by
-- simulation_student_progress / simulation_admin_overview below, and kept
-- alive they would reference a `scores.session_id` column that no longer
-- exists under that name.

-- EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ENUMS 
CREATE TYPE domain_type      AS ENUM ('product_manager', 'sqa_engineer', 'data_analyst', 'frontend_engineer', 'backend_engineer');
CREATE TYPE difficulty_type  AS ENUM ('easy', 'medium', 'hard');
CREATE TYPE session_status AS ENUM ('active', 'paused', 'scene_complete', 'simulation_complete', 'timer_expired', 'quit', 'network_failure', 'admin_terminated');
CREATE TYPE user_role        AS ENUM ('student', 'admin');
CREATE TYPE sentiment_type   AS ENUM ('positive', 'neutral', 'negative');
CREATE TYPE simulation_status AS ENUM ('in_progress', 'completed', 'abandoned');  -- new flow only

-- TABLE: universities
-- Lookup table for institution names — avoids duplicate/typo'd free text
-- ("MIT" vs "M.I.T." would otherwise be two different values) and lets us
-- aggregate/query by institution cleanly.
CREATE TABLE universities (
  id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name  TEXT UNIQUE NOT NULL
);

-- TABLE: degrees
-- Lookup table for degree/program names, same rationale as universities.
CREATE TABLE degrees (
  id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name  TEXT UNIQUE NOT NULL
);

-- TABLE 1: users
-- One row per registered account
-- admin can view all sessions and reports (mentor dashboard)
CREATE TABLE users (
  id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email                   TEXT UNIQUE NOT NULL,
  password_hash           TEXT NOT NULL,
  full_name               TEXT NOT NULL,
  role                    user_role NOT NULL DEFAULT 'student',
  university_id           INT REFERENCES universities(id),
  degree_id               INT REFERENCES degrees(id),
  graduation_year         INT CHECK (graduation_year BETWEEN 1950 AND 2050),
  core_interests          TEXT[] NOT NULL DEFAULT '{}',
  is_active               BOOLEAN NOT NULL DEFAULT TRUE,
  failed_login_attempts   INT NOT NULL DEFAULT 0,
  locked_until            TIMESTAMPTZ,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_login              TIMESTAMPTZ
);

CREATE INDEX idx_users_university ON users(university_id);
CREATE INDEX idx_users_degree     ON users(degree_id);

-- Index: admin needs to list all users quickly 
CREATE INDEX idx_users_role ON users(role);

-- TABLE 2: user_profiles
-- Onboarding assessment data — filled once before first sim
-- Answers: "where is the onboarding data stored?"
CREATE TABLE user_profiles (
  user_id              UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  personality_results  JSONB,
  interest_results     JSONB,
  -- Defaulted to 3 (neutral) rather than required — the onboarding flow no
  -- longer collects per-domain self-ratings (replaced by chosen-field +
  -- dynamic MCQ calibration, done client-side), but scene generation still
  -- reads these via get_self_rating() for any domain, so a safe default
  -- keeps that path working without requiring backfill or code changes.
  self_rated_product_manager   INT NOT NULL DEFAULT 3 CHECK (self_rated_product_manager   BETWEEN 1 AND 5),
  self_rated_sqa_engineer      INT NOT NULL DEFAULT 3 CHECK (self_rated_sqa_engineer      BETWEEN 1 AND 5),
  self_rated_data_analyst      INT NOT NULL DEFAULT 3 CHECK (self_rated_data_analyst      BETWEEN 1 AND 5),
  self_rated_frontend_engineer INT NOT NULL DEFAULT 3 CHECK (self_rated_frontend_engineer BETWEEN 1 AND 5),
  self_rated_backend_engineer  INT NOT NULL DEFAULT 3 CHECK (self_rated_backend_engineer  BETWEEN 1 AND 5),
  created_at           TIMESTAMPTZ DEFAULT NOW(),
  updated_at           TIMESTAMPTZ DEFAULT NOW()
);
 
-- Trigger: auto-update updated_at on any change
CREATE OR REPLACE FUNCTION touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;
 
CREATE TRIGGER user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- TABLE: refresh_tokens
-- One row per issued refresh token (opaque random string, never stored raw)
-- Enables logout/revocation and rotation-reuse theft detection, unlike a bare stateless JWT
CREATE TABLE refresh_tokens (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash    TEXT NOT NULL,                        -- SHA-256 hash of the raw token
  expires_at    TIMESTAMPTZ NOT NULL,
  revoked_at    TIMESTAMPTZ,
  replaced_by   UUID REFERENCES refresh_tokens(id),   -- rotation chain
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);

-- TABLE: sessions — DISABLED, kept for reference only (not created).
-- The legacy director.py-based session flow this powered has been fully
-- retired: session_service.py, app/api/v1/sessions.py, and
-- app/repositories/sessions.py were all deleted (frontend is being
-- re-integrated from scratch next week against `simulation_sessions`
-- instead, per team decision — only login/signup stay as-is). Already
-- fully decoupled from the rest of the schema before this — nothing else
-- references it (stakeholder_trust/npc_memory/scores/decisions_log were
-- all repointed at `simulation_sessions` earlier), so disabling it is
-- a clean cut with zero cascade impact.
--
-- CREATE TABLE sessions (
--   id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--   user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
--   domain              domain_type NOT NULL,
--   difficulty          difficulty_type NOT NULL DEFAULT 'medium',
--   status              session_status NOT NULL DEFAULT 'active',
--   current_scene_id    TEXT NOT NULL DEFAULT 'scene_1',
--   scenes_completed    TEXT[] NOT NULL DEFAULT '{}',
--   scene_state         JSONB NOT NULL DEFAULT '{}',
--   sprint_progress     INT NOT NULL DEFAULT 0 CHECK (sprint_progress BETWEEN 0 AND 100),
--   time_remaining      INT,
--   completion_reason   TEXT,
--   started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
--   completed_at        TIMESTAMPTZ,
--   last_active_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
-- );
--
-- CREATE INDEX idx_sessions_user    ON sessions(user_id);
-- CREATE INDEX idx_sessions_status  ON sessions(status);
-- CREATE INDEX idx_sessions_domain  ON sessions(domain);

-- NOTE: stakeholder_trust used to be defined here (TABLE 4). The live
-- session flow never wrote to it (confirmed empty), so it's been moved
-- down and redefined against the new `simulation_sessions` table instead
-- of being duplicated — see the NEW SIMULATION SCHEMA section below.

-- NOTE: scores (TABLE 5) and decisions_log (TABLE 6) used to be defined
-- here, FK'd to the legacy `sessions` table. Neither was ever written to
-- by the live session flow (confirmed empty), so both have been moved
-- down and repointed at `simulation_sessions` instead of being
-- duplicated — see the NEW SIMULATION SCHEMA section below.

-- NOTE: npc_memory used to be defined here (TABLE 7). Same situation as
-- stakeholder_trust above — moved down and redefined against
-- `simulation_sessions` instead of being duplicated.

-- TABLE 8: career_dna_reports
-- Final output per user
-- One row per completed simulation set
-- Generated by Report Agent
-- Versioned so regeneration doesn't silently overwrite previous reports
CREATE TABLE career_dna_reports (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 
  -- Aggregated dimension scores across all simulation_session_ids
  dim_analytical      NUMERIC(5,2),
  dim_ambiguity       NUMERIC(5,2),
  dim_communication   NUMERIC(5,2),
  dim_attention       NUMERIC(5,2),
  dim_decisiveness    NUMERIC(5,2),
 
  -- Ranked fit scores per domain  e.g. {"product_manager": 82, "sqa_engineer": 74}
  domain_fit_scores   JSONB,
 
  -- Narrative (LLM-generated, grounded in scores)
  summary_narrative   TEXT,
  strengths           TEXT[],
  growth_areas        TEXT[],
  top_recommendation  domain_type,
  confidence_level    TEXT CHECK (confidence_level IN ('high', 'moderate', 'directional')),
 
  -- Evidence: maps dimension → array of scene_evaluations UUIDs (real,
  -- stable ids — unlike the legacy flow's synthetic decision ids that
  -- never pointed at a persisted row)
  -- e.g. {"analytical_reasoning": ["uuid1", "uuid2"]}
  evidence_citations  JSONB,
 
  -- Which simulation_sessions fed into this report
  simulation_session_ids  UUID[],
 
  -- PDF download — NULL until Report Agent generates it
  pdf_url             TEXT,
 
  version             INT NOT NULL DEFAULT 1,
  generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reports_user ON career_dna_reports(user_id);

-- Legacy dashboard views (student_completed_domains, admin_session_overview)
-- removed — superseded by simulation_student_progress /
-- simulation_admin_overview below. No application code queried them (no
-- admin API was ever built against the legacy flow), so removal is safe.

-- ═══════════════════════════════════════════════════════════════════════════
-- NEW SIMULATION SCHEMA — scene-by-scene dynamic generation
-- `sessions` (legacy, above) is now disabled — its code has been deleted.
-- Everything below is either new, or an existing table (`stakeholder_trust`,
-- `npc_memory`) repointed at `simulation_sessions` — safe since the legacy
-- flow never wrote to either. `scores` and `decisions_log` are both
-- disabled too (commented out below) — see their comments for why.
-- ═══════════════════════════════════════════════════════════════════════════

-- TABLE: simulation_sessions
-- One row per simulation attempt under the new scene-by-scene flow.
CREATE TABLE simulation_sessions (
  id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  domain                domain_type NOT NULL,
  difficulty            difficulty_type NOT NULL DEFAULT 'medium',
  status                simulation_status NOT NULL DEFAULT 'in_progress',
  current_scene_number  INT NOT NULL DEFAULT 1,
  started_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at          TIMESTAMPTZ,
  last_active_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sim_sessions_user   ON simulation_sessions(user_id);
CREATE INDEX idx_sim_sessions_status ON simulation_sessions(status);
CREATE INDEX idx_sim_sessions_domain ON simulation_sessions(domain);

-- TABLE: simulation_scenes
-- One row per agent-generated scene. Full agent output kept as JSONB so
-- the contract can evolve without a migration; scene_number is the only
-- structural field backend relies on for ordering/lookup.
CREATE TABLE simulation_scenes (
  id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  simulation_session_id  UUID NOT NULL REFERENCES simulation_sessions(id) ON DELETE CASCADE,
  scene_number           INT NOT NULL,
  content                JSONB NOT NULL,   -- full SceneContent from the agent layer
  generated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(simulation_session_id, scene_number)
);

CREATE INDEX idx_sim_scenes_session ON simulation_scenes(simulation_session_id);

-- TABLE: scene_evaluations
-- One row per scene, 1:1. Inserted at response-submission time with
-- evaluation fields NULL; updated once the agent layer's evaluation
-- completes.
CREATE TABLE scene_evaluations (
  id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  scene_id               UUID NOT NULL UNIQUE REFERENCES simulation_scenes(id) ON DELETE CASCADE,
  user_response          JSONB NOT NULL,   -- raw_text / structured / response_time_seconds / revision_count
  evaluation             JSONB,            -- full EvaluationResult once evaluated, NULL until then
  overall_score          NUMERIC(5,2),     -- pulled out of `evaluation` for admin sort/filter
  -- Per-dimension scores, also pulled out of `evaluation.dimension_scores`
  -- for the same reason — lets progression across scenes be queried/
  -- charted directly instead of unpacking JSONB per row.
  analytical_reasoning   NUMERIC(5,2),
  ambiguity_tolerance    NUMERIC(5,2),
  communication_clarity  NUMERIC(5,2),
  attention_to_detail    NUMERIC(5,2),
  decisiveness           NUMERIC(5,2),
  -- Pulled out of `evaluation` the same way — the two fields decisions_log
  -- used to carry that don't already exist as their own column here.
  behavioral_flags       TEXT[],           -- e.g. ARRAY['clarification_sought', 'escalated']
  justification          TEXT,             -- one-line explanation of the score
  response_submitted_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  evaluated_at           TIMESTAMPTZ
);

CREATE INDEX idx_scene_evals_scene ON scene_evaluations(scene_id);

-- TABLE: stakeholder_trust (redefined — see note above)
-- One row per NPC per session, trust over time. Upserted from
-- EvaluationResult.npc_state_updates after each evaluation.
CREATE TABLE stakeholder_trust (
  id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  simulation_session_id  UUID NOT NULL REFERENCES simulation_sessions(id) ON DELETE CASCADE,
  npc_id                 TEXT NOT NULL,
  trust_score            INT NOT NULL DEFAULT 50 CHECK (trust_score BETWEEN 0 AND 100),
  sentiment              sentiment_type NOT NULL DEFAULT 'neutral',
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(simulation_session_id, npc_id)
);

CREATE INDEX idx_trust_session ON stakeholder_trust(simulation_session_id);

-- TABLE: npc_memory (redefined — see note above)
-- One row per NPC per session — compressed memory the agent layer carries
-- forward, not raw chat history. Same source as stakeholder_trust.
CREATE TABLE npc_memory (
  id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  simulation_session_id  UUID NOT NULL REFERENCES simulation_sessions(id) ON DELETE CASCADE,
  npc_id                 TEXT NOT NULL,
  memory_summary         TEXT,
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(simulation_session_id, npc_id)
);

CREATE INDEX idx_npc_memory_session ON npc_memory(simulation_session_id);

-- TABLE: scores — DISABLED, kept for reference only (not created).
-- Superseded by the five dimension columns added to `scene_evaluations`
-- below: this table only ever held one aggregate row per session, which
-- can't show progression across scenes. `scene_evaluations` already had
-- the per-scene dimension breakdown sitting in its `evaluation` JSONB
-- (EvaluationResult.dimension_scores) — pulling those into typed columns
-- there (same pattern as `overall_score`) gives per-scene granularity for
-- free instead of duplicating a less detailed copy here. Nothing ever
-- wrote to this table, so nothing is lost by disabling it.
--
-- CREATE TABLE scores (
--   id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--   simulation_session_id   UUID UNIQUE NOT NULL REFERENCES simulation_sessions(id) ON DELETE CASCADE,
--   analytical_reasoning    NUMERIC(5,2) NOT NULL DEFAULT 0,
--   ambiguity_tolerance     NUMERIC(5,2) NOT NULL DEFAULT 0,
--   communication_clarity   NUMERIC(5,2) NOT NULL DEFAULT 0,
--   attention_to_detail     NUMERIC(5,2) NOT NULL DEFAULT 0,
--   decisiveness            NUMERIC(5,2) NOT NULL DEFAULT 0,
--   updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
-- );

-- TABLE: decisions_log — DISABLED, kept for reference only (not created).
-- Was the old model's audit trail of branch-point decisions within a
-- scene. That concept doesn't exist in the new flow — one scene now has
-- exactly one response and one evaluation, which `scene_evaluations`
-- already records in full. `branch_point_id`/`action_type` below have no
-- new-flow equivalent at all (they came from director.py's classify_node,
-- which no longer exists); everything else here (score, dimensions,
-- behavioral_flags, justification, timing, revision count) either already
-- is or has just been added as a column on `scene_evaluations`. Nothing
-- ever wrote to this table, so nothing is lost by disabling it.
--
-- CREATE TABLE decisions_log (
--   id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--   simulation_session_id  UUID NOT NULL REFERENCES simulation_sessions(id) ON DELETE CASCADE,
--   scene_id               TEXT NOT NULL,
--   branch_point_id        TEXT NOT NULL,
--   user_action            TEXT NOT NULL,
--   action_type            TEXT NOT NULL,    -- 'branch_decision_defer', 'npc_message_clarification', etc.
--   overall_score          INT CHECK (overall_score BETWEEN 0 AND 100),
--   dim_analytical         NUMERIC(5,2),
--   dim_ambiguity          NUMERIC(5,2),
--   dim_communication      NUMERIC(5,2),
--   dim_attention          NUMERIC(5,2),
--   dim_decisiveness       NUMERIC(5,2),
--   behavioural_flags      TEXT[],
--   justification          TEXT,
--   time_to_decide_secs    INT,
--   revision_count         INT DEFAULT 0,
--   created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
-- );
--
-- CREATE INDEX idx_decisions_session ON decisions_log(simulation_session_id);
-- CREATE INDEX idx_decisions_scene   ON decisions_log(scene_id);

-- VIEW: simulation_student_progress
-- Per-session progress snapshot under the new flow.
CREATE VIEW simulation_student_progress AS
SELECT
  ss.id            AS simulation_session_id,
  ss.user_id,
  ss.domain,
  ss.difficulty,
  ss.status,
  ss.current_scene_number,
  COUNT(sc.id)                       AS scenes_generated,
  COUNT(se.evaluated_at)             AS scenes_evaluated,
  AVG(se.overall_score)              AS avg_score,
  AVG(se.analytical_reasoning)       AS avg_analytical_reasoning,
  AVG(se.ambiguity_tolerance)        AS avg_ambiguity_tolerance,
  AVG(se.communication_clarity)      AS avg_communication_clarity,
  AVG(se.attention_to_detail)        AS avg_attention_to_detail,
  AVG(se.decisiveness)               AS avg_decisiveness,
  ss.started_at,
  ss.completed_at,
  ss.last_active_at
FROM simulation_sessions ss
LEFT JOIN simulation_scenes sc ON sc.simulation_session_id = ss.id
LEFT JOIN scene_evaluations se ON se.scene_id = sc.id
GROUP BY ss.id;

-- VIEW: simulation_admin_overview
-- Dashboard — one query, full picture of all students under the new flow.
CREATE VIEW simulation_admin_overview AS
SELECT
  u.full_name,
  u.email,
  un.name  AS university,
  ss.id    AS simulation_session_id,
  ss.domain,
  ss.difficulty,
  ss.status,
  ss.current_scene_number,
  sp.scenes_generated,
  sp.scenes_evaluated,
  sp.avg_score,
  sp.avg_analytical_reasoning,
  sp.avg_ambiguity_tolerance,
  sp.avg_communication_clarity,
  sp.avg_attention_to_detail,
  sp.avg_decisiveness,
  ss.started_at,
  ss.completed_at,
  ss.last_active_at
FROM simulation_sessions ss
JOIN users u                             ON u.id = ss.user_id
LEFT JOIN universities un                ON un.id = u.university_id
LEFT JOIN simulation_student_progress sp ON sp.simulation_session_id = ss.id
ORDER BY ss.last_active_at DESC;

-- ROW-LEVEL SECURITY (RLS)
-- NOTE: Auth is fully custom (own JWTs, not Supabase Auth), so Supabase's
-- auth.uid() session claim is never populated for this backend. The backend
-- connects with the service_role key (bypasses RLS) and enforces ownership
-- checks in application code instead (see app/core/auth.py verify_session_ownership).
-- RLS stays enabled as inert defense-in-depth against an anon-key leak, but
-- carries no auth.uid()-based policies since those could never match.
ALTER TABLE users                ENABLE ROW LEVEL SECURITY;
ALTER TABLE universities         ENABLE ROW LEVEL SECURITY;
ALTER TABLE degrees              ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles      ENABLE ROW LEVEL SECURITY;
ALTER TABLE refresh_tokens       ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE sessions           ENABLE ROW LEVEL SECURITY;  -- table disabled, see above
ALTER TABLE stakeholder_trust    ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE scores             ENABLE ROW LEVEL SECURITY;  -- table disabled, see above
-- ALTER TABLE decisions_log      ENABLE ROW LEVEL SECURITY;  -- table disabled, see above
ALTER TABLE npc_memory           ENABLE ROW LEVEL SECURITY;
ALTER TABLE career_dna_reports   ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulation_sessions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulation_scenes    ENABLE ROW LEVEL SECURITY;
ALTER TABLE scene_evaluations    ENABLE ROW LEVEL SECURITY;

-- SEED: create one admin account (uncomment, set a real bcrypt hash, before running)
-- INSERT INTO users (email, password_hash, full_name, role)
-- VALUES ('mentor@folio3.com', '<bcrypt-hash>', 'Mentor Name', 'admin');
