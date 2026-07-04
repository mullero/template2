# kpi-architecture

3-tier KPI rule:
- Tier 1 runtime SQL by DEFAULT (add the composite indexes).
- Tier 2 Redis cache SKIPPED.
- Tier 3 materialized tables ONLY when a Tier-1 endpoint's MEASURED latency
  exceeds the threshold (never pre-optimise).

Standard analytics endpoint params: `date_from` / `date_to` / `as_of` /
`granularity` (new optional params default None so old callers keep working).
Frontend hooks follow `useXxxSummary({ dateFrom?, dateTo? })`.
See `plans/analytics-architecture.md`.
