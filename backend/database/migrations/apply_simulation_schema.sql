-- ============================================================
-- Migration: Create new simulation schema tables
-- Apply this in: Supabase Dashboard → SQL Editor → Run
--
-- Safe to re-run — all statements use IF NOT EXISTS guards.
-- ============================================================

-- 1. New enum for simulation status (new flow only)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'simulation_status') THEN
    CREATE TYPE simulation_status AS ENUM ('in_progress', 'completed', 'abandoned');
  END IF;
END$$;

-- 2. simulation_sessions — one row per simulation attempt
CREATE TABLE IF NOT EXISTS simulation_sessions (
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

CREATE INDEX IF NOT EXISTS idx_sim_sessions_user   ON simulation_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sim_sessions_status ON simulation_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sim_sessions_domain ON simulation_sessions(domain);

-- 3. simulation_scenes — one row per agent-generated scene
CREATE TABLE IF NOT EXISTS simulation_scenes (
  id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  simulation_session_id  UUID NOT NULL REFERENCES simulation_sessions(id) ON DELETE CASCADE,
  scene_number           INT NOT NULL,
  content                JSONB NOT NULL,
  generated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(simulation_session_id, scene_number)
);

CREATE INDEX IF NOT EXISTS idx_sim_scenes_session ON simulation_scenes(simulation_session_id);

-- 4. scene_evaluations — one row per scene, inserted at response-submission time
CREATE TABLE IF NOT EXISTS scene_evaluations (
  id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  scene_id               UUID NOT NULL UNIQUE REFERENCES simulation_scenes(id) ON DELETE CASCADE,
  user_response          JSONB NOT NULL,
  evaluation             JSONB,
  overall_score          NUMERIC(5,2),
  analytical_reasoning   NUMERIC(5,2),
  ambiguity_tolerance    NUMERIC(5,2),
  communication_clarity  NUMERIC(5,2),
  attention_to_detail    NUMERIC(5,2),
  decisiveness           NUMERIC(5,2),
  behavioral_flags       TEXT[],
  justification          TEXT,
  response_submitted_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  evaluated_at           TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_scene_evals_scene ON scene_evaluations(scene_id);

-- 5. stakeholder_trust — one row per NPC per session
CREATE TABLE IF NOT EXISTS stakeholder_trust (
  id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  simulation_session_id  UUID NOT NULL REFERENCES simulation_sessions(id) ON DELETE CASCADE,
  npc_id                 TEXT NOT NULL,
  trust_score            INT NOT NULL DEFAULT 50 CHECK (trust_score BETWEEN 0 AND 100),
  sentiment              sentiment_type NOT NULL DEFAULT 'neutral',
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(simulation_session_id, npc_id)
);

CREATE INDEX IF NOT EXISTS idx_trust_session ON stakeholder_trust(simulation_session_id);

-- 6. npc_memory — one row per NPC per session
CREATE TABLE IF NOT EXISTS npc_memory (
  id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  simulation_session_id  UUID NOT NULL REFERENCES simulation_sessions(id) ON DELETE CASCADE,
  npc_id                 TEXT NOT NULL,
  memory_summary         TEXT,
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(simulation_session_id, npc_id)
);

CREATE INDEX IF NOT EXISTS idx_npc_memory_session ON npc_memory(simulation_session_id);

-- 7. Enable RLS on new tables (service_role key bypasses it — safe)
ALTER TABLE simulation_sessions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulation_scenes    ENABLE ROW LEVEL SECURITY;
ALTER TABLE scene_evaluations    ENABLE ROW LEVEL SECURITY;
ALTER TABLE stakeholder_trust    ENABLE ROW LEVEL SECURITY;
ALTER TABLE npc_memory           ENABLE ROW LEVEL SECURITY;

-- 8. Views
CREATE OR REPLACE VIEW simulation_student_progress AS
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

CREATE OR REPLACE VIEW simulation_admin_overview AS
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
