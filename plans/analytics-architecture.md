# Analytics / KPI architecture

> Source of truth for where computed numbers live and how KPI endpoints are
> shaped. Consult before adding any dashboard/summary number.

## 3-tier rule

- **Tier 1 (DEFAULT):** compute KPIs with RUNTIME SQL aggregates on request. Add
  the required composite indexes; fast enough for the vast majority of cases.
- **Tier 2 (Redis cache):** SKIP by default — added complexity/cost rarely pays
  off.
- **Tier 3 (materialized tables):** ONLY when a Tier-1 endpoint's MEASURED
  latency exceeds the threshold; refreshed by a scheduled/queued job. Never
  pre-optimise.

## Placement

- A number that **changes with a user filter** (chip/dropdown/date range) is
  aggregated in the **FRONTEND** from already-loaded rows (see
  `hooks/useProjects.ts` KPIs).
- A number **identical for every user on the same data** (dashboard summary,
  scheduled email) is computed in the **BACKEND** via SQL.

## Endpoint & hook shape

- Backend query params: `date_from`, `date_to`, `as_of`, `granularity`. New
  optional params default to `None` so existing callers keep working.
- Frontend hooks: `useXxxSummary({ dateFrom?, dateTo? })` returning
  `{ data, loading, error }`. Reuse shared currency/number helpers
  (`utils/format.ts`) — never hand-roll conversion or separators.
