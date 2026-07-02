---
applyTo: "backend/src/graph/**/*.py"
---
# Graph projection (Neo4j)

## Cardinal rule
**Postgres is the system of record; Neo4j is a derived, disposable projection.**
Every write path persists to Postgres first, then projects to the graph. The
graph must be fully reconstructable from Postgres at any time (a re-projection
job should be able to rebuild it). Never store data in Neo4j that exists nowhere
else.

## Tenancy
- Every node carries `tenant_id`. Every Cypher `MATCH`/`MERGE` filters on it.
- Uniqueness is **composite** on `(tenant_id, id)` — never global `id`.

## Community Edition constraints
- Use `CREATE CONSTRAINT ... REQUIRE (n.tenant_id, n.id) IS UNIQUE`.
- **Do NOT use `IS NODE KEY`** — it is Neo4j Enterprise-only and will fail on the
  `neo4j:*-community` image used in `docker-compose.yml`. A uniqueness constraint
  already provides the backing index, so don't add a separate index for the same
  keys.

## Driver usage
- Async driver (`neo4j>=5`). Use parameterized Cypher (`$tenant_id`, `$id`) —
  never string-format values into queries.
- Graph failures must not break the primary write. Projection errors are logged;
  the Postgres write is the source of truth. The backend `/health` reports graph
  status separately and the API stays up if Neo4j is down.

## MERGE pattern
```cypher
MERGE (p:Project {tenant_id: $tenant_id, id: $id})
SET p.name = $name, p.updated_at = $updated_at
```
Use `MERGE` (idempotent) for projection, not `CREATE`.
