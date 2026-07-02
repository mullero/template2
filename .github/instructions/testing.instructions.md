---
applyTo: "**/*.{test,spec}.{ts,tsx,py}"
---
# Testing

## Backend (pytest)
- Tests live in `backend/tests/`. Unit tests must run without external services.
- Integration tests that need Postgres/Neo4j **skip cleanly** when the service is
  absent (guard on env / connection), so `pytest -q` is green on a bare checkout.
- Use `pytest.mark.asyncio` for async paths. Assert tenant isolation explicitly
  in repository tests (one tenant cannot see another's rows).

## Frontend (Vitest + Testing Library)
- Setup in `src/test/setup.ts` (jest-dom, cleanup, localStorage/ResizeObserver
  polyfills, `vi.mock('@/firebase')`). Render via `renderWithProviders` from
  `src/test/utils.tsx`.
- Test behavior through the DOM (roles/text), not implementation details. Mock
  the `@/api/*` module, not axios internals.
- Env is stubbed in `vite.config.ts` test block (`VITE_DISABLE_AUTH=true`, etc.).

## Bar
- Don't lower coverage or delete assertions to make a test pass — fix the code.
- New vertical-slice features get tests on both sides mirroring the existing
  `Project`/`Task` tests.
