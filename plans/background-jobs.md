# Background jobs & durable async work — architecture

> Source of truth for how app-skeleton runs durable background work. Update this
> doc in the same PR that changes the job model, worker, or queue wiring.

## Decision: Cloud Tasks (push) over in-process background tasks

Cloud Run scales to zero and recycles instances. In-process
`BackgroundTasks`/threads die with the instance, have no retries, and can't
coordinate across instances. **Google Cloud Tasks** durably stores each task and
PUSHes it to an internal HTTPS endpoint, cold-starting an instance from zero,
with built-in retries/backoff, a dead-letter path, and per-queue concurrency +
dispatch-rate limits (which also cap paid-API burst cost). It stays ~free at low
volume and preserves scale-to-zero (no Redis, no always-on worker).

## Flow

```
request ──► create jobs row ──► COMMIT (Postgres = system of record)
                                   │ (after commit)
                                   ▼
        TASKS_ENABLED=false ─► run worker INLINE (local dev, no emulator)
        TASKS_ENABLED=true  ─► Cloud Tasks ─► POST /api/internal/tasks/{kind}
                                                  (OIDC token, queue SA)
                                                  │
                                                  ▼
                                       worker.run_job (idempotent)
```

## Tables (`models/job.py`)

`jobs`: `id, tenant_id (NOT NULL), kind, status(queued|running|succeeded|failed),
attempts, payload(JSONB), error, created_by, created_at, updated_at`.

## Contracts

- **Enqueue after commit.** `services/task_queue.py::create_job` writes the row;
  the route commits; `enqueue()` then dispatches. Never enqueue in-transaction.
- **Idempotent worker.** `services/worker.py::run_job` skips jobs already
  `succeeded`; handlers skip already-processed domain rows. Retried deliveries
  are safe.
- **Machine auth.** `dependencies/internal_auth.py` verifies the Cloud Tasks
  OIDC token (audience + queue SA email). The internal routes are on the
  auth-coverage allow-list.
- **Status API.** `GET /api/jobs/{id}` is tenant-scoped for frontend polling.

## Scheduled work

`services/scheduler.py` (APScheduler) runs periodic in-process jobs, each wrapped
so a failure can't crash the worker. NOTE: scale-to-zero means it only ticks
while an instance is warm — for guaranteed cadence use **Cloud Scheduler → an
internal endpoint** instead.

## Fallback (zero new managed services)

A DB-backed `jobs` table drained by a Cloud Scheduler cron hitting
`/api/internal/tasks/drain` gives near-zero cost and ~1-min latency with
hand-rolled retries — for teams that want to avoid Cloud Tasks entirely.
