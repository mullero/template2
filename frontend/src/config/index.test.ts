import { describe, expect, it } from 'vitest';

import { getConfig, resetConfig } from '@/config';

describe('config', () => {
  it('exposes the required apiUrl from env', () => {
    resetConfig();
    const cfg = getConfig();
    expect(cfg.apiUrl).toBe('http://localhost:8000/api');
  });

  it('parses boolean feature flags', () => {
    resetConfig();
    const cfg = getConfig();
    expect(cfg.disableAuth).toBe(true);
    expect(cfg.graphEnabled).toBe(true);
  });

  it('caches the config instance', () => {
    resetConfig();
    expect(getConfig()).toBe(getConfig());
  });
});
