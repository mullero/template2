---
applyTo: "backend/src/**/{internal,task_queue,worker,scheduler,document_extraction,quota_service,email_service}*.py"
---
# Background jobs (Cloud Tasks)

Durable async work runs on **Google Cloud Tasks**, not in-process FastAPI
`BackgroundTasks` (those die on Cloud Run instance recycle / scale-to-zero, have
no retries, and cannot coordinate across instances).

## Enqueue rules
- Persist to Postgres FIRST. Create the `jobs` row, commit, THEN enqueue.
- NEVER enqueue inside the request's transaction — enqueue AFTER the commit
  (`services/task_queue.py::enqueue`).
- Locally (`TASKS_ENABLED=false`) the worker runs INLINE/synchronously — no
  emulator. In cloud it pushes to `POST /api/internal/tasks/{kind}`.

## Worker rules (`api/routes/internal.py`, `services/worker.py`)
- Auth is the Cloud Tasks **OIDC token** (verify audience + the queue SA email),
  NOT the Firebase user flow. These routes are on the auth-coverage allow-list.
- Every handler is **idempotent**: guard on job/document status so a retried task
  never re-runs completed work (skip when already `succeeded`/committed).
- Every job is **tenant-scoped**: the worker loads the row un-scoped (it is a
  machine principal) then acts strictly on that row's own `tenant_id`.
- Let unhandled errors 5xx so Cloud Tasks retries with backoff; record the
  failure on the job row and refund any reserved quota.

## Quota
- Reserve BEFORE you spend (`quota_service.reserve`) so a tenant can't blow the
  paid-API budget; refund on failure. The reservation is a single atomic
  `INSERT ... ON CONFLICT DO UPDATE ... WHERE used < cap`.

## Observability
- Emit structured entry/decision/success/failure logs. NEVER log secrets,
  tokens, tenant_id, or raw payloads.
