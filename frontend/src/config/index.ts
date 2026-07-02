/**
 * Typed environment configuration singleton.
 *
 * `VITE_API_URL` is REQUIRED and throws on load if missing. Feature flags are
 * parsed from strings. Firebase reads its own VITE_FIREBASE_* vars in
 * `firebase.ts`.
 */

export interface Config {
  apiUrl: string;
  disableAuth: boolean;
  enableAnalytics: boolean;
  graphEnabled: boolean;
}

function parseBool(value: string | undefined, fallback = false): boolean {
  if (value === undefined) return fallback;
  return value.toLowerCase() === 'true';
}

function loadConfig(): Config {
  const apiUrl = import.meta.env.VITE_API_URL;
  if (!apiUrl) {
    throw new Error('VITE_API_URL is required but was not provided at build time.');
  }
  return {
    apiUrl,
    disableAuth: parseBool(import.meta.env.VITE_DISABLE_AUTH),
    enableAnalytics: parseBool(import.meta.env.VITE_ENABLE_ANALYTICS),
    graphEnabled: parseBool(import.meta.env.VITE_GRAPH_ENABLED),
  };
}

let cached: Config | null = null;

export function getConfig(): Config {
  if (cached === null) {
    cached = loadConfig();
  }
  return cached;
}

/** Reset the cached config (tests only). */
export function resetConfig(): void {
  cached = null;
}

export const config: Config = getConfig();
