/** Auth context object + value type. Kept separate from the provider so the
 * provider file only exports a component (react-refresh friendly). */
import { createContext } from 'react';
import { type User } from 'firebase/auth';

import { type BackendUser } from '@/api/auth';

export interface AuthContextValue {
  firebaseUser: User | null;
  backendUser: BackendUser | null;
  loading: boolean;
  bootstrapRequired: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshToken: () => Promise<string | null>;
  completeBootstrap: (tenantId: string) => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);
