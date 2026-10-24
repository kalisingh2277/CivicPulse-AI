"""remove notifications, reports, SLA and CV columns

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-24

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # notifications (index first, then the table, then its now-unused enum)
    op.drop_index("notifications_inbox_idx", table_name="notifications")
    op.drop_table("notifications")
    postgresql.ENUM(name="notification_channel").drop(op.get_bind(), checkfirst=True)

    # reports
    op.drop_index("reports_created_idx", table_name="reports")
    op.drop_table("reports")

    # SLA columns
    op.drop_column("issues", "sla_due_at")
    op.drop_column("issues", "sla_breached")
    op.drop_column("categories", "sla_hours")
    op.drop_column("daily_stats", "sla_breaches")

    # CV columns, then the enum they used
    op.drop_column("complaint_media", "cv_status")
    op.drop_column("complaint_media", "cv_result")
    postgresql.ENUM(name="cv_status").drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    cv_status = postgresql.ENUM(
        "pending", "done", "failed", "skipped", name="cv_status", create_type=False
    )
    cv_status.create(op.get_bind(), checkfirst=True)
    notification_channel = postgresql.ENUM(
        "inapp", "email", name="notification_channel", create_type=False
    )
    notification_channel.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "complaint_media",
        sa.Column("cv_status", cv_status, server_default="pending", nullable=False),
    )
    op.add_column("complaint_media", sa.Column("cv_result", postgresql.JSONB))

    op.add_column(
        "daily_stats",
        sa.Column("sla_breaches", sa.Integer, server_default="0", nullable=False),
    )
    op.add_column(
        "categories",
        sa.Column("sla_hours", sa.Integer, server_default="168", nullable=False),
    )
    # sla_due_at was NOT NULL: add nullable, backfill with the default 168h SLA, then enforce.
    op.add_column("issues", sa.Column("sla_due_at", sa.DateTime(timezone=True)))
    op.execute("UPDATE issues SET sla_due_at = first_reported_at + interval '168 hours'")
    op.alter_column("issues", "sla_due_at", nullable=False)
    op.add_column(
        "issues",
        sa.Column("sla_breached", sa.Boolean, server_default=sa.text("false"), nullable=False),
    )

    op.create_table(
        "reports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("scope", sa.String, server_default="city", nullable=False),
        sa.Column("stats", postgresql.JSONB, nullable=False),
        sa.Column("content_md", sa.Text),
        sa.Column("pdf_key", sa.String),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("reports_created_idx", "reports", [sa.text("created_at DESC")])

    op.create_table(
        "notifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_notifications_user_id_users"),
            nullable=False,
        ),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("body", sa.Text),
        sa.Column(
            "issue_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("issues.id", name="fk_notifications_issue_id_issues"),
        ),
        sa.Column("channel", notification_channel, server_default="inapp", nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("emailed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "notifications_inbox_idx",
        "notifications",
        ["user_id", sa.text("created_at DESC")],
        postgresql_where=sa.text("read_at IS NULL"),
    )
