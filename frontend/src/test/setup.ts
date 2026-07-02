/** Vitest setup: jest-dom matchers, cleanup, and jsdom polyfills. */
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

afterEach(() => {
  cleanup();
});

// Polyfill localStorage for jsdom if missing.
if (typeof localStorage === 'undefined') {
  const store = new Map<string, string>();
  Object.defineProperty(globalThis, 'localStorage', {
    value: {
      getItem: (k: string): string | null => store.get(k) ?? null,
      setItem: (k: string, v: string): void => void store.set(k, v),
      removeItem: (k: string): void => void store.delete(k),
      clear: (): void => store.clear(),
    },
    writable: true,
  });
}

// Polyfill ResizeObserver for jsdom (charting / layout libs may require it).
if (typeof globalThis.ResizeObserver === 'undefined') {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  };
}

// Mock Firebase so importing firebase.ts never hits the network.
vi.mock('@/firebase', () => ({
  auth: { currentUser: null },
  firebaseApp: {},
}));
