"""baseline — snapshot of the live schema as it actually is today

This is not a literal copy of database/schema.sql — it reflects true live
state, which had already drifted from that file at the time Alembic was
introduced (self_rated_* columns on user_profiles are still nullable/no
default live; schema.sql already says NOT NULL DEFAULT 3). That pending
change is 0002, a real migration, not folded into this baseline. This
revision is meant to be adopted via `alembic stamp head`, not run — the
live database already has all of this.

Revision ID: 0001
Revises:
Create Date: 2026-07-10

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.execute("""
        CREATE TYPE domain_type AS ENUM (
            'product_manager', 'sqa_engineer', 'data_analyst',
            'frontend_engineer', 'backend_engineer'
        )
    """)
    op.execute("CREATE TYPE difficulty_type AS ENUM ('easy', 'medium', 'hard')")
    op.execute("""
        CREATE TYPE session_status AS ENUM (
            'active', 'paused', 'scene_complete', 'simulation_complete',
            'timer_expired', 'quit', 'network_failure', 'admin_terminated'
        )
    """)
    op.execute("CREATE TYPE user_role AS ENUM ('student', 'admin')")
    op.execute("CREATE TYPE sentiment_type AS ENUM ('positive', 'neutral', 'negative')")
    op.execute("CREATE TYPE simulation_status AS ENUM ('in_progress', 'completed', 'abandoned')")

    op.execute("""
        CREATE TABLE universities (
          id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          name  TEXT UNIQUE NOT NULL
        )
    """)
    op.execute("""
        CREATE TABLE degrees (
          id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          name  TEXT UNIQUE NOT NULL
        )
    """)

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX idx_users_university ON users(university_id)")
    op.execute("CREATE INDEX idx_users_degree ON users(degree_id)")
    op.execute("CREATE INDEX idx_users_role ON users(role)")

    # self_rated_* deliberately nullable/no-default here — matches true live
    # state at the time this baseline was captured. 0002 brings this in line
    # with schema.sql's NOT NULL DEFAULT 3.
    op.execute("""
        CREATE TABLE user_profiles (
          user_id              UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
          personality_results  JSONB,
          interest_results     JSONB,
          self_rated_product_manager   INT CHECK (self_rated_product_manager   BETWEEN 1 AND 5),
          self_rated_sqa_engineer      INT CHECK (self_rated_sqa_engineer      BETWEEN 1 AND 5),
          self_rated_data_analyst      INT CHECK (self_rated_data_analyst      BETWEEN 1 AND 5),
          self_rated_frontend_engineer INT CHECK (self_rated_frontend_engineer BETWEEN 1 AND 5),
          self_rated_backend_engineer  INT CHECK (self_rated_backend_engineer  BETWEEN 1 AND 5),
          created_at           TIMESTAMPTZ DEFAULT NOW(),
          updated_at           TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION touch_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER user_profiles_updated_at
          BEFORE UPDATE ON user_profiles
          FOR EACH ROW EXECUTE FUNCTION touch_updated_at()
    """)

    op.execute("""
        CREATE TABLE refresh_tokens (
          id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          token_hash    TEXT NOT NULL,
          expires_at    TIMESTAMPTZ NOT NULL,
          revoked_at    TIMESTAMPTZ,
          replaced_by   UUID REFERENCES refresh_tokens(id),
          created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id)")
    op.execute("CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash)")

    op.execute("""
        CREATE TABLE career_dna_reports (
          id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          dim_analytical      NUMERIC(5,2),
          dim_ambiguity       NUMERIC(5,2),
          dim_communication   NUMERIC(5,2),
          dim_attention       NUMERIC(5,2),
          dim_decisiveness    NUMERIC(5,2),
          domain_fit_scores   JSONB,
          summary_narrative   TEXT,
          strengths           TEXT[],
          growth_areas        TEXT[],
          top_recommendation  domain_type,
          confidence_level    TEXT CHECK (confidence_level IN ('high', 'moderate', 'directional')),
          evidence_citations  JSONB,
          simulation_session_ids  UUID[],
          pdf_url             TEXT,
          version             INT NOT NULL DEFAULT 1,
          generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_reports_user ON career_dna_reports(user_id)")

    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX idx_sim_sessions_user ON simulation_sessions(user_id)")
    op.execute("CREATE INDEX idx_sim_sessions_status ON simulation_sessions(status)")
    op.execute("CREATE INDEX idx_sim_sessions_domain ON simulation_sessions(domain)")

    op.execute("""
        CREATE TABLE simulation_scenes (
          id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          simulation_session_id  UUID NOT NULL REFERENCES simulation_sessions(id) ON DELETE CASCADE,
          scene_number           INT NOT NULL,
          content                JSONB NOT NULL,
          generated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          UNIQUE(simulation_session_id, scene_number)
        )
    """)
    op.execute("CREATE INDEX idx_sim_scenes_session ON simulation_scenes(simulation_session_id)")

    op.execute("""
        CREATE TABLE scene_evaluations (
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
        )
    """)
    op.execute("CREATE INDEX idx_scene_evals_scene ON scene_evaluations(scene_id)")

    op.execute("""
        CREATE TABLE stakeholder_trust (
          id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          simulation_session_id  UUID NOT NULL REFERENCES simulation_sessions(id) ON DELETE CASCADE,
          npc_id                 TEXT NOT NULL,
          trust_score            INT NOT NULL DEFAULT 50 CHECK (trust_score BETWEEN 0 AND 100),
          sentiment              sentiment_type NOT NULL DEFAULT 'neutral',
          updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          UNIQUE(simulation_session_id, npc_id)
        )
    """)
    op.execute("CREATE INDEX idx_trust_session ON stakeholder_trust(simulation_session_id)")

    op.execute("""
        CREATE TABLE npc_memory (
          id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          simulation_session_id  UUID NOT NULL REFERENCES simulation_sessions(id) ON DELETE CASCADE,
          npc_id                 TEXT NOT NULL,
          memory_summary         TEXT,
          updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          UNIQUE(simulation_session_id, npc_id)
        )
    """)
    op.execute("CREATE INDEX idx_npc_memory_session ON npc_memory(simulation_session_id)")

    op.execute("""
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
        GROUP BY ss.id
    """)

    op.execute("""
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
        ORDER BY ss.last_active_at DESC
    """)

    for table in (
        "users", "universities", "degrees", "user_profiles", "refresh_tokens",
        "stakeholder_trust", "npc_memory", "career_dna_reports",
        "simulation_sessions", "simulation_scenes", "scene_evaluations",
    ):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    # Destructive and rarely appropriate to actually run — kept for
    # completeness, not as a routinely-used path.
    op.execute("DROP SCHEMA public CASCADE")
    op.execute("CREATE SCHEMA public")
