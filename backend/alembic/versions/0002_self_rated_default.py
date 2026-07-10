"""user_profiles.self_rated_* -> NOT NULL DEFAULT 3

Brings the live DB in line with what database/schema.sql has said since the
onboarding rework (self-ratings are no longer collected during onboarding —
replaced by chosen-field + MCQ calibration — but simulation_service still
reads these via get_self_rating() for any domain, so a safe default keeps
that path working without a backfill). Backfills existing NULLs to 3 before
adding the NOT NULL constraint, since ALTER COLUMN ... SET NOT NULL fails
outright if any row doesn't already satisfy it.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-10

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUMNS = [
    "self_rated_product_manager",
    "self_rated_sqa_engineer",
    "self_rated_data_analyst",
    "self_rated_frontend_engineer",
    "self_rated_backend_engineer",
]


def upgrade() -> None:
    for column in COLUMNS:
        op.execute(f"UPDATE user_profiles SET {column} = 3 WHERE {column} IS NULL")
    for column in COLUMNS:
        op.execute(f"ALTER TABLE user_profiles ALTER COLUMN {column} SET DEFAULT 3")
        op.execute(f"ALTER TABLE user_profiles ALTER COLUMN {column} SET NOT NULL")


def downgrade() -> None:
    for column in COLUMNS:
        op.execute(f"ALTER TABLE user_profiles ALTER COLUMN {column} DROP NOT NULL")
        op.execute(f"ALTER TABLE user_profiles ALTER COLUMN {column} DROP DEFAULT")
