# background-jobs

Durable async work runs on Cloud Tasks (see `plans/background-jobs.md`).
Operational facts:

- Locally `TASKS_ENABLED=false` → the worker runs INLINE in a fresh session
  right after the enqueue commit. No emulator, no queue. Tests exercise
  `services/worker.py::run_job` directly.
- Enqueue AFTER the Postgres commit — never inside the request transaction, or a
  rollback leaves an orphaned Cloud Task pointing at a non-existent row.
- Worker idempotency is guarded on `jobs.status` (skip `succeeded`) AND on the
  domain row status (skip already committed/needs_review). Retried deliveries are
  safe.
- Internal worker routes (`/api/internal/tasks/*`) authenticate with the Cloud
  Tasks OIDC token (audience + queue SA email), NOT Firebase. They are on the
  auth-coverage allow-list — do not add `require_tenant` to them.
- Quota reserve is a single atomic `INSERT ... ON CONFLICT DO UPDATE ...
  WHERE used < cap RETURNING used`; a NULL return means the cap is hit. Refund on
  extraction failure.
