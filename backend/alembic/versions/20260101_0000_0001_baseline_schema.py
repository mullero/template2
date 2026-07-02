"""baseline schema (projects, tasks)

Revision ID: 0001_baseline
Revises:
Create Date: 2026-01-01 00:00:00.000000+00:00

Idempotent baseline: every statement is guarded with IF [NOT] EXISTS and there
is exactly ONE statement per op.execute (asyncpg requirement). Fix-forward only.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- projects -----------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id VARCHAR(36) NOT NULL,
            tenant_id VARCHAR(128) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            deleted_at TIMESTAMP WITH TIME ZONE,
            name VARCHAR(255) NOT NULL,
            normalized_name VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(32) NOT NULL,
            CONSTRAINT pk_projects PRIMARY KEY (id),
            CONSTRAINT uq_projects_tenant_id_normalized_name UNIQUE (tenant_id, normalized_name)
        )
        """,
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_projects_id ON projects (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_projects_tenant_id ON projects (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_projects_normalized_name ON projects (normalized_name)")

    # --- tasks --------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id VARCHAR(36) NOT NULL,
            tenant_id VARCHAR(128) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            deleted_at TIMESTAMP WITH TIME ZONE,
            project_id VARCHAR(36) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(32) NOT NULL,
            CONSTRAINT pk_tasks PRIMARY KEY (id),
            CONSTRAINT fk_tasks_project_id_projects FOREIGN KEY (project_id)
                REFERENCES projects (id) ON DELETE CASCADE
        )
        """,
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_id ON tasks (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_tenant_id ON tasks (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_project_id ON tasks (project_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tasks")
    op.execute("DROP TABLE IF EXISTS projects")
