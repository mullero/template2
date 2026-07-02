---
applyTo: "**"
---
# Security guardrails

These apply to every file. Fail closed.

## Secrets
- Never commit secrets. Use `CHANGE_ME` placeholders, `.env` (gitignored), and
  Secret Manager. If you find a real secret in a diff, stop and flag it.
- Firebase **web** config is public and may live in frontend env; API keys,
  DB passwords, `SECRET_KEY`, and Neo4j credentials are secret.

## Auth
- `AUTH_ENABLED` defaults to **true**; `VITE_DISABLE_AUTH` is a local-only
  convenience. Never default either to the insecure value or ship it disabled.
- Verify tenant scoping on every data path. A missing `tenant_id` filter is a
  security bug, not a style nit.

## Input & queries
- Parameterize all SQL (SQLAlchemy) and Cypher. Never string-concatenate user
  input into a query.
- Validate at boundaries with Pydantic / zod-style checks; trust nothing from the
  client (including `tenant_id` — derive it from the authenticated principal, not
  the request body).

## Web
- Keep the nginx security headers and CSP intact. Don't loosen CORS to `*` in
  production; `CORS_ORIGINS` is explicit.
- Rate limiting is on by default (`SlowAPIMiddleware`); don't remove it.

## OWASP Top 10
- Watch for injection, broken access control (tenant leaks), SSRF (validate
  outbound URLs), and sensitive-data exposure in logs/errors. Detailed errors are
  gated behind `ENABLE_DETAILED_ERRORS` (off in prod).
