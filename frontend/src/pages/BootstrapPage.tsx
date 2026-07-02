/** Bootstrap page: assign a tenant to the first superadmin. */
import { useState, type FormEvent } from 'react';
import { Navigate } from 'react-router-dom';

import { authStrings } from '@/constants/uiStrings';
import { useAuth } from '@/hooks/useAuth';

export function BootstrapPage(): React.JSX.Element {
  const { backendUser, completeBootstrap } = useAuth();
  const [tenantId, setTenantId] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (backendUser?.tenant_id) {
    return <Navigate to="/" replace />;
  }

  const onSubmit = async (event: FormEvent): Promise<void> => {
    event.preventDefault();
    setSubmitting(true);
    try {
      await completeBootstrap(tenantId);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="app-main">
      <div className="card stack" style={{ maxWidth: 360, margin: '10vh auto' }}>
        <h1>{authStrings.bootstrapTitle}</h1>
        <form className="stack" onSubmit={(e) => void onSubmit(e)}>
          <label className="stack">
            {authStrings.bootstrapTenantLabel}
            <input
              className="input"
              value={tenantId}
              onChange={(e) => setTenantId(e.target.value)}
              required
            />
          </label>
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {authStrings.bootstrapButton}
          </button>
        </form>
      </div>
    </div>
  );
}
