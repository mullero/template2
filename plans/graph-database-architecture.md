# Graph database architecture (Neo4j projection)

## Purpose

machote uses **Postgres as the system of record** and **Neo4j as a derived
projection** optimized for relationship traversal (e.g. "all tasks reachable
from a project", dependency graphs, impact analysis). The graph exists to answer
questions that are awkward or slow in relational SQL. It holds **no primary
data** — everything in Neo4j can be rebuilt from Postgres.

```
        write (source of truth)              project (derived)
Client ───────────────► Postgres ──────────────► Neo4j
                          │  ▲                      │
                          │  └── re-projection ─────┘
                          │      (rebuild anytime)
                          ▼
                    system of record
```

## Invariants

1. **Postgres first.** A write is committed to Postgres before it is projected.
   If projection fails, the Postgres write still stands; the projection is
   retried/reconciled. The API never blocks on Neo4j for a primary write.
2. **Reconstructable.** Any Neo4j state must be reproducible from Postgres. No
   field lives only in the graph.
3. **Tenant-scoped.** Every node has `tenant_id`; every query filters on it.
   Uniqueness is composite `(tenant_id, id)`.
4. **Idempotent projection.** Projection uses `MERGE`, so replays are safe.

## Data model (vertical slice)

Nodes: `(:Project {tenant_id, id, name, ...})`, `(:Task {tenant_id, id, title, ...})`.
Relationship: `(:Project)-[:HAS_TASK]->(:Task)`.

Constraints (Community-compatible — see below):

```cypher
CREATE CONSTRAINT project_tenant_id_unique IF NOT EXISTS
  FOR (p:Project) REQUIRE (p.tenant_id, p.id) IS UNIQUE;
CREATE CONSTRAINT task_tenant_id_unique IF NOT EXISTS
  FOR (t:Task) REQUIRE (t.tenant_id, t.id) IS UNIQUE;
```

## Community Edition constraint

The local stack and this template target **Neo4j Community**. `IS NODE KEY` is
**Enterprise-only** and fails on the `neo4j:*-community` image. Use composite
`IS UNIQUE` constraints instead — they provide the backing index, so no separate
index is needed for the same key set. This lives in
[`backend/src/graph/constraints.py`](../backend/src/graph/constraints.py).

## Write path

1. Route → service persists to Postgres (repository, tenant-scoped).
2. After commit, the service calls the graph repository under
   `backend/src/graph/repositories/` to `MERGE` the node/relationship.
3. Graph errors are logged and surfaced via `/health` (`checks.neo4j`), never
   raised into the primary request.

## Health & degradation

- `GRAPH_ENABLED=false` disables the projection entirely; the app runs Postgres-only.
- When enabled but Neo4j is down, primary CRUD keeps working; graph-backed
  read endpoints degrade (return empty/last-known) and `/health` reports
  `neo4j: "error"` while `status` stays `healthy` for core.

## Re-projection

Because the graph is derived, a maintenance job can wipe and rebuild it from
Postgres (iterate rows per tenant, `MERGE` nodes/edges). This is the recovery
story for drift or a lost Neo4j volume. Keep projection logic centralized so a
batch rebuild reuses the same `MERGE` code as the live write path.

## Production note

`terraform-mvp/` provisions Cloud Run + Cloud SQL but **not** Neo4j. Use Neo4j
AuraDB (or self-managed) and provide `NEO4J_URI` / `NEO4J_PASSWORD` via Secret
Manager (the secrets are pre-created when `graph_enabled = true`).
