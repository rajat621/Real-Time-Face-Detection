# backend/alembic/versions/0001_create_roi_detections.py

"""create roi detections

Revision ID: 0001_create_roi_detections
Revises:
Create Date: 2026-05-07
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_create_roi_detections"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roi_detections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("frame_index", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("x_min", sa.Integer(), nullable=False),
        sa.Column("y_min", sa.Integer(), nullable=False),
        sa.Column("x_max", sa.Integer(), nullable=False),
        sa.Column("y_max", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), sa.Computed("x_max - x_min", persisted=True)),
        sa.Column("height", sa.Integer(), sa.Computed("y_max - y_min", persisted=True)),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("frame_width", sa.Integer(), nullable=True),
        sa.Column("frame_height", sa.Integer(), nullable=True),
    )
    op.create_index("idx_roi_session", "roi_detections", ["session_id"])
    op.create_index("idx_roi_timestamp", "roi_detections", ["timestamp"])


def downgrade() -> None:
    op.drop_index("idx_roi_timestamp", table_name="roi_detections")
    op.drop_index("idx_roi_session", table_name="roi_detections")
    op.drop_table("roi_detections")
