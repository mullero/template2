/** Login page. */
import { useState, type FormEvent } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { authStrings } from '@/constants/uiStrings';
import { config } from '@/config';
import { useAuth } from '@/hooks/useAuth';

interface LocationState {
  from?: { pathname?: string };
}

export function LoginPage(): React.JSX.Element {
  const { firebaseUser, signIn, signInWithGoogle } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const from = (location.state as LocationState | null)?.from?.pathname ?? '/';

  if (config.disableAuth || firebaseUser) {
    return <Navigate to={from} replace />;
  }

  const onSubmit = async (event: FormEvent): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await signIn(email, password);
    } catch {
      setError(authStrings.signInFailed);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="app-main">
      <div className="card stack" style={{ maxWidth: 360, margin: '10vh auto' }}>
        <h1>{authStrings.loginTitle}</h1>
        <form className="stack" onSubmit={(e) => void onSubmit(e)}>
          <label className="stack">
            {authStrings.emailLabel}
            <input
              className="input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label className="stack">
            {authStrings.passwordLabel}
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          {error !== null && <p className="text-danger">{error}</p>}
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {authStrings.signInButton}
          </button>
        </form>
        <button className="btn" type="button" onClick={() => void signInWithGoogle()}>
          {authStrings.signInWithGoogle}
        </button>
      </div>
    </div>
  );
}
