"""async subsystems (jobs, documents, quota_usage)

Revision ID: 0002_async_subsystems
Revises: 0001_baseline
Create Date: 2026-01-02 00:00:00.000000+00:00

Idempotent: every statement is guarded with IF [NOT] EXISTS and there is exactly
ONE statement per op.execute (asyncpg requirement). Fix-forward only.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_async_subsystems"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- jobs ---------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id VARCHAR(36) NOT NULL,
            tenant_id VARCHAR(128) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            kind VARCHAR(64) NOT NULL,
            status VARCHAR(32) NOT NULL,
            attempts INTEGER NOT NULL,
            payload JSONB NOT NULL,
            error TEXT,
            created_by VARCHAR(128),
            CONSTRAINT pk_jobs PRIMARY KEY (id)
        )
        """,
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_jobs_id ON jobs (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_jobs_tenant_id ON jobs (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_jobs_kind ON jobs (kind)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_jobs_status ON jobs (status)")

    # --- documents ----------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id VARCHAR(36) NOT NULL,
            tenant_id VARCHAR(128) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            deleted_at TIMESTAMP WITH TIME ZONE,
            filename VARCHAR(512) NOT NULL,
            content_hash VARCHAR(64) NOT NULL,
            storage_uri VARCHAR(1024),
            status VARCHAR(32) NOT NULL,
            extraction JSONB,
            confidence FLOAT,
            created_by VARCHAR(128),
            CONSTRAINT pk_documents PRIMARY KEY (id)
        )
        """,
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_documents_id ON documents (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_documents_tenant_id ON documents (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_documents_content_hash ON documents (content_hash)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_documents_status ON documents (status)")

    # --- quota_usage --------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS quota_usage (
            id VARCHAR(36) NOT NULL,
            tenant_id VARCHAR(128) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            usage_date DATE NOT NULL,
            used INTEGER NOT NULL,
            CONSTRAINT pk_quota_usage PRIMARY KEY (id),
            CONSTRAINT uq_quota_usage_tenant_id_usage_date UNIQUE (tenant_id, usage_date)
        )
        """,
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_quota_usage_id ON quota_usage (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_quota_usage_tenant_id ON quota_usage (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_quota_usage_usage_date ON quota_usage (usage_date)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS quota_usage")
    op.execute("DROP TABLE IF EXISTS documents")
    op.execute("DROP TABLE IF EXISTS jobs")
