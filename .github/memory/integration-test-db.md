# integration-test-db

Integration tests hit ONE real shared Postgres DB. The session fixture does
`Base.metadata.create_all` on setup and `DROP SCHEMA public CASCADE; CREATE
SCHEMA public` on teardown, so:

- NEVER run more than one pytest invocation at a time against it (concurrent runs
  drop each other's schema mid-test → spurious IntegrityError / "type already
  exists" that are NOT code regressions).
- An interrupted run leaves orphaned enum types/tables → reset by
  dropping/recreating the public schema.

Async-session gotchas:
- After `await session.commit()` attributes expire → touching an ORM attr
  triggers a SYNC lazy refresh (`MissingGreenlet`). Capture ids into vars before
  commit OR `session.expunge_all()` after raw SQL/UPDATEs.
- The global soft-delete hook hides `deleted_at` rows from ALL ORM queries incl.
  `session.get` — read them back with
  `.execution_options(include_deleted=True)`.

Local runner: start a throwaway PG and point `TEST_DATABASE_URL` at it, e.g.
`docker run --rm -e POSTGRES_USER=app_skeleton -e POSTGRES_PASSWORD=app_skeleton
-e POSTGRES_DB=app_skeleton_test -p 55432:5432 postgres:15-alpine` then
`TEST_DATABASE_URL=postgresql+asyncpg://app_skeleton:app_skeleton@localhost:55432/app_skeleton_test`.
