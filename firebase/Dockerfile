# syntax=docker/dockerfile:1
# Firebase Auth emulator for local development only. NOT for production.
FROM node:20-alpine

# The emulators run on the JVM; install a headless JRE plus small utilities used
# by the healthcheck.
RUN apk add --no-cache openjdk17-jre-headless bash curl \
    && npm install -g firebase-tools@13

WORKDIR /firebase
COPY firebase.json .firebaserc ./

# 9099 = Auth emulator, 4000 = Emulator UI.
EXPOSE 9099 4000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=12 \
  CMD wget -qO- http://127.0.0.1:9099/ >/dev/null 2>&1 || exit 1

CMD ["firebase", "emulators:start", "--only", "auth", "--project", "app-skeleton-local"]
