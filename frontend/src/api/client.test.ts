import { describe, expect, it, vi } from 'vitest';

import { setOnUnauthorized, setTokenProvider } from '@/api/client';

describe('api client token wiring', () => {
  it('accepts and clears the token provider without throwing', () => {
    const provider = vi.fn().mockResolvedValue('token-123');
    expect(() => setTokenProvider(provider)).not.toThrow();
    expect(() => setTokenProvider(null)).not.toThrow();
  });

  it('accepts and clears the unauthorized handler', () => {
    const handler = vi.fn();
    expect(() => setOnUnauthorized(handler)).not.toThrow();
    expect(() => setOnUnauthorized(null)).not.toThrow();
  });
});
