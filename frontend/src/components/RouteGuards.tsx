/**
 * Route guards. Each renders <Outlet/> or <Navigate/>.
 *
 * - ProtectedRoute  : requires firebaseUser (or dev bypass via VITE_DISABLE_AUTH).
 * - AdminRoute      : role in {admin, superadmin}.
 * - SuperAdminRoute : role == superadmin.
 * - TenantRoute     : requires a tenant assignment before the dashboard.
 */
import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { config } from '@/config';
import { Spinner } from '@/components/ui/Spinner';
import { authStrings } from '@/constants/uiStrings';
import { useAuth } from '@/hooks/useAuth';

export function ProtectedRoute(): React.JSX.Element {
  const { firebaseUser, loading } = useAuth();
  const location = useLocation();

  if (config.disableAuth) {
    return <Outlet />;
  }
  if (loading) {
    return <Spinner label={authStrings.loadingSession} />;
  }
  if (!firebaseUser) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <Outlet />;
}

export function TenantRoute(): React.JSX.Element {
  const { backendUser, bootstrapRequired, loading } = useAuth();

  if (config.disableAuth) {
    return <Outlet />;
  }
  if (loading) {
    return <Spinner label={authStrings.loadingSession} />;
  }
  if (bootstrapRequired || !backendUser?.tenant_id) {
    return <Navigate to="/bootstrap" replace />;
  }
  return <Outlet />;
}

export function AdminRoute(): React.JSX.Element {
  const { backendUser, loading } = useAuth();

  if (config.disableAuth) {
    return <Outlet />;
  }
  if (loading) {
    return <Spinner label={authStrings.loadingSession} />;
  }
  if (backendUser?.role !== 'admin' && backendUser?.role !== 'superadmin') {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}

export function SuperAdminRoute(): React.JSX.Element {
  const { backendUser, loading } = useAuth();

  if (config.disableAuth) {
    return <Outlet />;
  }
  if (loading) {
    return <Spinner label={authStrings.loadingSession} />;
  }
  if (backendUser?.role !== 'superadmin') {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
