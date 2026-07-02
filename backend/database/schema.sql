-- CareerDNA AI — Database Schema
-- Supabase / PostgreSQL
-- Missing: a table for actual simulation content when we have dynamic scenarios

-- EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ENUMS 
CREATE TYPE domain_type      AS ENUM ('pm', 'sqa', 'data_analyst', 'frontend', 'backend');
CREATE TYPE difficulty_type  AS ENUM ('easy', 'medium', 'hard');
CREATE TYPE session_status AS ENUM ('active', 'paused', 'scene_complete', 'simulation_complete', 'timer_expired', 'quit', 'network_failure', 'admin_terminated');
CREATE TYPE user_role        AS ENUM ('student', 'admin');
CREATE TYPE sentiment_type   AS ENUM ('positive', 'neutral', 'negative');

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
  self_rated_pm        INT CHECK (self_rated_pm        BETWEEN 1 AND 5),
  self_rated_sqa       INT CHECK (self_rated_sqa       BETWEEN 1 AND 5),
  self_rated_data      INT CHECK (self_rated_data      BETWEEN 1 AND 5),
  self_rated_frontend  INT CHECK (self_rated_frontend  BETWEEN 1 AND 5),
  self_rated_backend   INT CHECK (self_rated_backend   BETWEEN 1 AND 5),
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

-- TABLE 3: sessions
-- One row per simulation attempt (one student, one domain)
-- A student can have multiple sessions for the same domain
CREATE TABLE sessions (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  domain              domain_type NOT NULL,
  difficulty          difficulty_type NOT NULL DEFAULT 'medium',
  status              session_status NOT NULL DEFAULT 'active',
  current_scene_id    TEXT NOT NULL DEFAULT 'scene_1',
  scenes_completed    TEXT[] NOT NULL DEFAULT '{}',   -- array of scene_id strings
  scene_state       JSONB NOT NULL DEFAULT '{}',
  sprint_progress     INT NOT NULL DEFAULT 0 CHECK (sprint_progress BETWEEN 0 AND 100),
  time_remaining      INT,   
  completion_reason TEXT,          -- human-readable, e.g. "timer_expired on scene_2"
  started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at        TIMESTAMPTZ,
  last_active_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sessions_user    ON sessions(user_id);
CREATE INDEX idx_sessions_status  ON sessions(status);
CREATE INDEX idx_sessions_domain  ON sessions(domain);

-- TABLE 4: stakeholder_trust
-- One row per NPC per session and tracks trust level over time
CREATE TABLE stakeholder_trust (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id  UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  npc_id      TEXT NOT NULL,        -- e.g. 'sara_khan', 'eng_lead', 'vp_chen'
  trust_score INT NOT NULL DEFAULT 50 CHECK (trust_score BETWEEN 0 AND 100),
  sentiment   sentiment_type NOT NULL DEFAULT 'neutral',
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(session_id, npc_id)        -- one row per NPC per session
);

CREATE INDEX idx_trust_session ON stakeholder_trust(session_id);

-- TABLE 5: scores
-- Running dimension scores for a session
-- Five shared dimensions across ALL domains
-- One row per session (upserted after each decision)
CREATE TABLE scores (
  id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id              UUID UNIQUE NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  analytical_reasoning    NUMERIC(5,2) NOT NULL DEFAULT 0,
  ambiguity_tolerance     NUMERIC(5,2) NOT NULL DEFAULT 0,
  communication_clarity   NUMERIC(5,2) NOT NULL DEFAULT 0,
  attention_to_detail     NUMERIC(5,2) NOT NULL DEFAULT 0,
  decisiveness            NUMERIC(5,2) NOT NULL DEFAULT 0,
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 6: decisions_log
-- One row per branch point hit
-- Full audit trail
-- Powers the Career DNA Report evidence-citation feature
CREATE TABLE decisions_log (
  id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id            UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  scene_id              TEXT NOT NULL,
  branch_point_id       TEXT NOT NULL,
  user_action           TEXT NOT NULL,
  action_type           TEXT NOT NULL,    -- 'branch_decision_defer', 'npc_message_clarification', etc.
  overall_score         INT CHECK (overall_score BETWEEN 0 AND 100),
  -- Per-dimension scores for this single decision
  dim_analytical        NUMERIC(5,2),
  dim_ambiguity         NUMERIC(5,2),
  dim_communication     NUMERIC(5,2),
  dim_attention         NUMERIC(5,2),
  dim_decisiveness      NUMERIC(5,2),
  behavioural_flags     TEXT[],           -- e.g. ARRAY['clarification_sought', 'escalated']
  justification         TEXT,             -- one-line LLM-generated explanation
  time_to_decide_secs   INT,              -- how long student took before acting
  revision_count        INT DEFAULT 0,    -- how many times they edited before sending
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_decisions_session   ON decisions_log(session_id);
CREATE INDEX idx_decisions_scene     ON decisions_log(scene_id);

-- TABLE 7: npc_memory
-- Compressed memory per NPC per session
-- NOT raw chat history — just the summary the NPC carries forward
CREATE TABLE npc_memory (
  id                        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id                UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  npc_id                    TEXT NOT NULL,
  last_interaction_summary  TEXT,
  relationship_score        INT DEFAULT 50 CHECK (relationship_score BETWEEN 0 AND 100),
  current_sentiment         sentiment_type DEFAULT 'neutral',
  key_events                JSONB DEFAULT '[]',   -- max 5 compressed events
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(session_id, npc_id)
);

CREATE INDEX idx_npc_memory_session ON npc_memory(session_id);

-- TABLE 8: career_dna_reports
-- Final output per user
-- One row per completed simulation set
-- Generated by Report Agent
-- Versioned so regeneration doesn't silently overwrite previous reports
CREATE TABLE career_dna_reports (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 
  -- Aggregated dimension scores across all sessions_included
  dim_analytical      NUMERIC(5,2),
  dim_ambiguity       NUMERIC(5,2),
  dim_communication   NUMERIC(5,2),
  dim_attention       NUMERIC(5,2),
  dim_decisiveness    NUMERIC(5,2),
 
  -- Ranked fit scores per domain  e.g. {"pm": 82, "sqa": 74}
  domain_fit_scores   JSONB,
 
  -- Narrative (LLM-generated, grounded in scores)
  summary_narrative   TEXT,
  strengths           TEXT[],
  growth_areas        TEXT[],
  top_recommendation  domain_type,
  confidence_level    TEXT CHECK (confidence_level IN ('high', 'moderate', 'directional')),
 
  -- Evidence: maps dimension → array of decisions_log UUIDs
  -- e.g. {"analytical_reasoning": ["uuid1", "uuid2"]}
  evidence_citations  JSONB,
 
  -- Which sessions fed into this report
  -- Use this to compute domains_completed dynamically (see view below)
  sessions_included   UUID[],
 
  -- PDF download — NULL until Report Agent generates it
  pdf_url             TEXT,
 
  version             INT NOT NULL DEFAULT 1,
  generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reports_user ON career_dna_reports(user_id);

-- VIEW: student_completed_domains
-- Answers "which domains has this student completed?"
-- Computed fresh every time
-- Usage: SELECT * FROM student_completed_domains WHERE user_id = '...';
CREATE VIEW student_completed_domains AS
SELECT
  s.user_id,
  s.domain,
  COUNT(*) AS attempts,
  BOOL_OR(s.status = 'simulation_complete') AS completed,
  MIN(s.started_at)   AS first_attempt,
  MAX(s.completed_at) AS last_completed
FROM sessions s
GROUP BY s.user_id, s.domain;
 
-- VIEW: admin_session_overview
-- Dashboard — one query, full picture of all students
CREATE VIEW admin_session_overview AS
SELECT
  u.full_name,
  u.email,
  un.name         AS university,
  s.id            AS session_id,
  s.domain,
  s.difficulty,
  s.status,
  s.completion_reason,
  s.current_scene_id,
  array_length(s.scenes_completed, 1) AS scenes_done,
  sc.analytical_reasoning,
  sc.ambiguity_tolerance,
  sc.communication_clarity,
  sc.attention_to_detail,
  sc.decisiveness,
  -- Self-rated vs actual gap (useful for mentor insight)
  CASE s.domain
    WHEN 'pm'           THEN up.self_rated_pm
    WHEN 'sqa'          THEN up.self_rated_sqa
    WHEN 'data_analyst' THEN up.self_rated_data
    WHEN 'frontend'     THEN up.self_rated_frontend
    WHEN 'backend'      THEN up.self_rated_backend
  END AS self_rating_for_domain,
  s.started_at,
  s.completed_at,
  s.last_active_at
FROM sessions s
JOIN users u             ON u.id = s.user_id
LEFT JOIN universities un ON un.id = u.university_id
LEFT JOIN scores sc      ON sc.session_id = s.id
LEFT JOIN user_profiles up ON up.user_id = s.user_id
ORDER BY s.last_active_at DESC;

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
ALTER TABLE sessions             ENABLE ROW LEVEL SECURITY;
ALTER TABLE stakeholder_trust    ENABLE ROW LEVEL SECURITY;
ALTER TABLE scores               ENABLE ROW LEVEL SECURITY;
ALTER TABLE decisions_log        ENABLE ROW LEVEL SECURITY;
ALTER TABLE npc_memory           ENABLE ROW LEVEL SECURITY;
ALTER TABLE career_dna_reports   ENABLE ROW LEVEL SECURITY;

-- SEED: create one admin account (uncomment, set a real bcrypt hash, before running)
-- INSERT INTO users (email, password_hash, full_name, role)
-- VALUES ('mentor@folio3.com', '<bcrypt-hash>', 'Mentor Name', 'admin');
