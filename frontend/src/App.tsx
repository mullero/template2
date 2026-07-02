/** Root app: Suspense + Routes composed from route-group functions. */
import { Suspense } from 'react';
import { Routes } from 'react-router-dom';

import { Spinner } from '@/components/ui/Spinner';
import { ToasterProvider } from '@/components/ui/Toaster';
import { commonStrings } from '@/constants/uiStrings';
import { appRoutes, publicRoutes } from '@/routes';

export function App(): React.JSX.Element {
  return (
    <ToasterProvider>
      <Suspense fallback={<Spinner label={commonStrings.loading} />}>
        <Routes>
          {publicRoutes()}
          {appRoutes()}
        </Routes>
      </Suspense>
    </ToasterProvider>
  );
}
