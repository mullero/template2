"""Global soft-delete filter.

Rows carrying a non-null ``deleted_at`` are hidden from ALL ORM SELECTs by
default. Pass ``.execution_options(include_deleted=True)`` on a statement to read
soft-deleted rows back (e.g. audit/restore flows).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import ORMExecuteState, Session, with_loader_criteria

from src.models.mixins import SoftDeleteMixin

_installed = False


def _add_soft_delete_criteria(state: ORMExecuteState) -> None:
    """Append ``deleted_at IS NULL`` to every SELECT unless opted out."""
    if not state.is_select:
        return
    if state.execution_options.get("include_deleted", False):
        return
    state.statement = state.statement.options(
        with_loader_criteria(
            SoftDeleteMixin,
            lambda cls: cls.deleted_at.is_(None),
            include_aliases=True,
        ),
    )


def install_soft_delete_filter(_session_class: Any = None) -> None:
    """Register the soft-delete listener on the sync ORM ``Session`` class.

    Idempotent: registers at most once per process. The optional argument is
    accepted for call-site symmetry (async sessions delegate to the sync
    ``Session`` class, which is where the event must live).
    """
    global _installed
    if _installed:
        return
    event.listen(Session, "do_orm_execute", _add_soft_delete_criteria)
    _installed = True
