"""Neo4j graph layer.

Postgres is the SYSTEM OF RECORD; Neo4j is a SECONDARY, derived store for
relationship-heavy queries. Every node/relationship carries ``tenant_id`` and
every Cypher query is parameterized and tenant-scoped.
"""
