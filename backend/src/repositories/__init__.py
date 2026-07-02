"""Data-access layer.

Every repository read takes a required ``tenant_id`` and filters by it. A request
scoped to tenant A must never see tenant B's rows.
"""
