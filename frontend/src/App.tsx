/** Root app: Suspense + Routes composed from route-group functions. */
import { Suspense } from 'react';
import { Routes } from 'react-router-dom';

import { JobProgressIndicator } from '@/components/JobProgressIndicator';
import { Spinner } from '@/components/ui/Spinner';
import { ToasterProvider } from '@/components/ui/Toaster';
import { commonStrings } from '@/constants/uiStrings';
import { JobProgressProvider } from '@/contexts/JobProgressContext';
import { appRoutes, publicRoutes } from '@/routes';

export function App(): React.JSX.Element {
  return (
    <ToasterProvider>
      <JobProgressProvider>
        <Suspense fallback={<Spinner label={commonStrings.loading} />}>
          <Routes>
            {publicRoutes()}
            {appRoutes()}
          </Routes>
        </Suspense>
        <JobProgressIndicator />
      </JobProgressProvider>
    </ToasterProvider>
  );
}
