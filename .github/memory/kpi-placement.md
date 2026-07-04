# kpi-placement

Where a computed number lives:
- A KPI that CHANGES with a user filter (chip, dropdown, date range) is
  aggregated in the FRONTEND from already-loaded rows.
- A number IDENTICAL for every user on the same data (dashboard summary,
  scheduled email) is computed in the BACKEND via SQL.

Reuse the shared currency/number helpers (`frontend/src/utils/format.ts`) — never
hand-roll conversion or separators.
