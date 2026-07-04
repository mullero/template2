# Document processing flow (async AI extraction) — architecture

> Source of truth for the "AI turns an uploaded file into reviewed structured
> data" pipeline. Update this doc in the same PR that changes the upload route,
> the extraction worker, or the confidence gate.

## Flow

```
POST /api/documents/upload
  1. validate type/size  (streamed with a HARD cap — reject before buffering)
  2. Layer-1 dedup       (content sha256 — surface duplicate, don't silently drop)
  3. reserve quota       (quota_service.reserve — refund on failure)
  4. store original      (GCS when configured) + write documents row (processing)
  5. enqueue extraction  (Cloud Tasks / inline) — returns 201 immediately
        │
        ▼
worker: run_extraction
  6. run LLM extraction (structured JSON) + compute confidence
  7. CONFIDENCE GATE:
        confidence >= EXTRACTION_AUTOCOMMIT_THRESHOLD and not force_review
              ─► auto-commit  (status=committed)
        else  ─► human-review queue (status=needs_review)   [force_review always here]
  8. on failure: mark failed + refund quota + re-raise (Cloud Tasks retries)
```

## Statuses (`models/document.py`)

`processing → {committed | needs_review | duplicate | failed}`.

## Resumability & review

- `GET /api/documents?pending_review=true` lists unreviewed items so a human can
  resume across sessions (the frontend surfaces a "pending review" banner).
- `POST /api/documents/{id}/review?accept=` resolves a review item
  (accept → committed, reject → failed).

## Dedup

- **Layer 1 (upload):** content hash. A repeat upload returns the existing row
  with `duplicate=true` instead of creating work.
- **Layer 2 (post-extraction):** normalized extracted fields → route likely
  duplicates to a decision step (extend `run_extraction`), never a silent drop.

## Quota & key-pool

- Reserve-before-spend per `(tenant_id, day)` caps paid-API cost; refund on
  failure. For a single-key rate ceiling, route calls across a POOL of provider
  keys with per-key health + cooldown (future extension).

## Frontend

- The global `JobProgressProvider` (mounted above the router) owns the polling
  loop so progress SURVIVES navigation. Pages start uploads and read status;
  they do not own the loop.
