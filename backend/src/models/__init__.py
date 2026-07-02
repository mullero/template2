"""ORM model registry.

Alembic's ``env.py`` and the app both call :func:`import_all_models` so that
every table is registered on ``Base.metadata`` before autogenerate/create_all.
When you add a model:

  1. import it here (TYPE_CHECKING block below),
  2. import it inside :func:`import_all_models`,
  3. add it to ``__all__`` (or ruff F401 fires).

See ``.github/memory/new-model-checklist.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.project import Project
    from src.models.task import Task


def import_all_models() -> None:
    """Import every model module so it registers on ``Base.metadata``."""
    from src.models.project import Project  # noqa: F401
    from src.models.task import Task  # noqa: F401


__all__ = ["Project", "Task", "import_all_models"]
