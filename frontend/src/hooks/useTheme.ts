/** `useTheme` — thin context accessor that throws outside the provider. */
import { useContext } from 'react';

import { ThemeContext } from '@/contexts/theme-context';

export interface UseThemeResult {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

export function useTheme(): UseThemeResult {
  const ctx = useContext(ThemeContext);
  if (ctx === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return ctx;
}
