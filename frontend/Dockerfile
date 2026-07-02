# syntax=docker/dockerfile:1

# --- Build stage ---------------------------------------------------------
FROM node:24-alpine AS builder

WORKDIR /app

# Install dependencies with a clean, reproducible install.
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

# Build. Vite auto-loads `.env.production` (public VITE_* config only — API URL
# and Firebase web config, which are NOT secrets). Generate it beforehand with
# `scripts/sync-config.sh`. We keep VITE_* out of ARG/ENV on purpose so no build
# arg is mistaken for a secret and so config stays single-sourced from root .env.
COPY . .
RUN test -f .env.production || { \
      echo "ERROR: frontend/.env.production is missing."; \
      echo "Run scripts/sync-config.sh from the repo root first."; \
      exit 1; \
    }
RUN npm run build

# --- Runtime stage -------------------------------------------------------
# Unprivileged nginx image: runs as non-root (uid 101) on port 8080 by default.
FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime

# Cloud Run sends traffic to $PORT (default 8080). nginx-unprivileged already
# listens on 8080, matching Cloud Run's default.
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 8080

# Basic container healthcheck against the SPA entrypoint.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/healthz >/dev/null 2>&1 || exit 1

# nginx-unprivileged sets a non-root USER and a sane default CMD already.
