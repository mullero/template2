/** Route-group functions returning <Route> fragments. Pages are lazy-loaded. */
import { lazy } from 'react';
import { Route } from 'react-router-dom';

import { Layout } from '@/components/Layout';
import { ProtectedRoute, TenantRoute } from '@/components/RouteGuards';

const LoginPage = lazy(() =>
  import('@/pages/LoginPage').then((m) => ({ default: m.LoginPage })),
);
const BootstrapPage = lazy(() =>
  import('@/pages/BootstrapPage').then((m) => ({ default: m.BootstrapPage })),
);
const ProjectsPage = lazy(() =>
  import('@/pages/ProjectsPage').then((m) => ({ default: m.ProjectsPage })),
);
const NotFoundPage = lazy(() =>
  import('@/pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage })),
);

export function publicRoutes(): React.JSX.Element {
  return <Route path="/login" element={<LoginPage />} />;
}

export function appRoutes(): React.JSX.Element {
  return (
    <Route element={<ProtectedRoute />}>
      <Route path="/bootstrap" element={<BootstrapPage />} />
      <Route element={<TenantRoute />}>
        <Route
          path="/"
          element={
            <Layout>
              <ProjectsPage />
            </Layout>
          }
        />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Route>
  );
}
