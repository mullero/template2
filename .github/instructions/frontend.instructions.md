---
applyTo: "frontend/**/*.{ts,tsx}"
---
# Frontend (React 19 + Vite + TypeScript strict)

## Structure
- `src/api/` axios modules (one per resource) → `src/hooks/` data hooks →
  `src/pages/` screens. `src/components/ui/` for shared primitives.
- Path alias `@/*` → `./src/*`. Use it instead of long relative paths.

## TypeScript
- `strict` is on. No `any`, no non-null `!` unless truly unavoidable.
- **Every function/callback needs an explicit return type** (ESLint enforces
  `explicit-function-return-type`), including `useEffect` cleanups (`: void`) and
  async callbacks (`: Promise<T>`).

## React / Fast Refresh
- **A module that exports a component must export ONLY components.** Context
  objects, hooks, and types belong in a separate non-JSX `.ts` module (e.g.
  `contexts/auth-context.ts` exports `AuthContext` + types; `AuthContext.tsx`
  exports only `AuthProvider`). Violating this triggers
  `react-refresh/only-export-components`.
- Hooks live in `src/hooks/` and consume context via their own `useX` file.

## Config
- Read runtime config through `src/config/` (which reads `import.meta.env`),
  not `import.meta.env.*` scattered across components.
- Firebase web config is **public**, not secret. Auth can be disabled locally
  via `VITE_DISABLE_AUTH=true` — never ship that to prod.

## Zero-warning bar
```bash
cd frontend && npm run type-check && npm run lint && npm run build && npx vitest run
```
`eslint` runs with `--max-warnings 0`. Fix causes, don't disable rules.

## Don't
- Don't add dependencies that aren't used (dead `manualChunks` entries break the
  build). Don't fetch in components — use a hook.
