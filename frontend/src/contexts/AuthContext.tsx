/**
 * Auth context — the source of truth for authentication state.
 *
 * Subscribes to Firebase `onAuthStateChanged`, exposes the firebaseUser plus a
 * backendUser ({role, tenant_id}) synced via `GET /auth/me`, and the auth
 * actions. On mount it wires the API client (token provider + 401 handler).
 */
import {
  GoogleAuthProvider,
  onAuthStateChanged,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut as firebaseSignOut,
  type User,
} from 'firebase/auth';
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { bootstrapWorkspace, fetchCurrentUser, type BackendUser } from '@/api/auth';
import { setOnUnauthorized, setTokenProvider } from '@/api/client';
import { config } from '@/config';
import { AuthContext, type AuthContextValue } from '@/contexts/auth-context';
import { auth } from '@/firebase';

const DEV_USER: BackendUser = {
  uid: 'dev-superadmin',
  email: 'dev@localhost',
  role: 'superadmin',
  tenant_id: 'dev-tenant',
};

export function AuthProvider({ children }: { children: ReactNode }): React.JSX.Element {
  const [firebaseUser, setFirebaseUser] = useState<User | null>(null);
  const [backendUser, setBackendUser] = useState<BackendUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshToken = useCallback(async (): Promise<string | null> => {
    const current = auth.currentUser;
    if (!current) return null;
    return current.getIdToken(true);
  }, []);

  // Wire the API client once.
  useEffect(() => {
    setTokenProvider(async (forceRefresh?: boolean): Promise<string | null> => {
      const current = auth.currentUser;
      if (!current) return null;
      return current.getIdToken(forceRefresh ?? false);
    });
    setOnUnauthorized((): void => {
      void firebaseSignOut(auth);
    });
    return (): void => {
      setTokenProvider(null);
      setOnUnauthorized(null);
    };
  }, []);

  // Dev bypass: skip Firebase entirely.
  useEffect(() => {
    if (config.disableAuth) {
      setBackendUser(DEV_USER);
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setFirebaseUser(user);
      if (user) {
        fetchCurrentUser()
          .then(setBackendUser)
          .catch(() => setBackendUser(null))
          .finally(() => setLoading(false));
      } else {
        setBackendUser(null);
        setLoading(false);
      }
    });
    return unsubscribe;
  }, []);

  const signIn = useCallback(async (email: string, password: string): Promise<void> => {
    await signInWithEmailAndPassword(auth, email, password);
  }, []);

  const signInWithGoogle = useCallback(async (): Promise<void> => {
    await signInWithPopup(auth, new GoogleAuthProvider());
  }, []);

  const resetPassword = useCallback(async (email: string): Promise<void> => {
    await sendPasswordResetEmail(auth, email);
  }, []);

  const signOut = useCallback(async (): Promise<void> => {
    await firebaseSignOut(auth);
    setBackendUser(null);
  }, []);

  const completeBootstrap = useCallback(async (tenantId: string): Promise<void> => {
    const updated = await bootstrapWorkspace(tenantId);
    await refreshToken();
    setBackendUser(updated);
  }, [refreshToken]);

  const bootstrapRequired = Boolean(
    !config.disableAuth && firebaseUser && backendUser && !backendUser.tenant_id,
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      firebaseUser,
      backendUser,
      loading,
      bootstrapRequired,
      signIn,
      signInWithGoogle,
      resetPassword,
      signOut,
      refreshToken,
      completeBootstrap,
    }),
    [
      firebaseUser,
      backendUser,
      loading,
      bootstrapRequired,
      signIn,
      signInWithGoogle,
      resetPassword,
      signOut,
      refreshToken,
      completeBootstrap,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
