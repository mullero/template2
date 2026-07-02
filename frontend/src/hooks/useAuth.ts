/** `useAuth` — thin context accessor that throws outside the provider. */
import { useContext } from 'react';

import { AuthContext, type AuthContextValue } from '@/contexts/auth-context';

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (ctx === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
